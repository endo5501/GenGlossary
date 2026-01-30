"""Pipeline executor for running glossary generation steps."""

import sqlite3
from dataclasses import dataclass
from enum import Enum
from threading import Event
from typing import Any, Callable

from genglossary.db.connection import transaction
from genglossary.db.document_repository import (
    create_document,
    delete_all_documents,
    list_all_documents,
)
from genglossary.db.issue_repository import create_issue, delete_all_issues
from genglossary.db.models import GlossaryTermRow
from genglossary.db.provisional_repository import (
    create_provisional_term,
    delete_all_provisional,
    list_all_provisional,
)
from genglossary.db.refined_repository import create_refined_term, delete_all_refined
from genglossary.db.term_repository import create_term, delete_all_terms, list_all_terms
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.factory import create_llm_client
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.models.term import ClassifiedTerm, Term, TermOccurrence
from genglossary.term_extractor import TermExtractor
from genglossary.utils.hash import compute_content_hash


class PipelineScope(Enum):
    """Enumeration of pipeline execution scopes."""

    FULL = "full"
    FROM_TERMS = "from_terms"
    PROVISIONAL_TO_REFINED = "provisional_to_refined"

# Map of scope to clear functions for table cleanup
_SCOPE_CLEAR_FUNCTIONS: dict[str, list[Callable[[sqlite3.Connection], None]]] = {
    "full": [delete_all_terms, delete_all_provisional, delete_all_issues, delete_all_refined],
    "from_terms": [delete_all_provisional, delete_all_issues, delete_all_refined],
    "provisional_to_refined": [delete_all_issues, delete_all_refined],
}


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context for thread-safe pipeline execution.

    This dataclass holds all execution-specific state that was previously
    stored as instance variables. Using a frozen dataclass ensures:
    1. Thread safety - each execution gets its own context
    2. Immutability - context cannot be accidentally modified
    3. Clear API - execution state is explicitly passed, not hidden in instance
    """

    run_id: int
    log_callback: Callable[[dict], None]
    cancel_event: Event


class PipelineExecutor:
    """Executes glossary generation pipeline steps.

    This class handles the execution of the pipeline steps in a background thread,
    with support for cancellation and progress reporting.

    Thread Safety:
        This class is designed to be thread-safe through the use of ExecutionContext.
        The LLM client is shared across executions (for efficiency), but all
        execution-specific state is contained in the ExecutionContext passed to
        each execute() call.
    """

    def __init__(self, provider: str = "ollama", model: str = ""):
        """Initialize the PipelineExecutor.

        Args:
            provider: LLM provider name (default: 'ollama').
            model: LLM model name (default: '').
        """
        self._llm_client = create_llm_client(provider=provider, model=model)

    def _log(
        self,
        context: ExecutionContext,
        level: str,
        message: str,
        *,
        step: str | None = None,
        current: int | None = None,
        total: int | None = None,
        current_term: str | None = None,
    ) -> None:
        """Log a message using the callback.

        Args:
            context: Execution context containing run_id and log_callback.
            level: Log level ('info', 'warning', 'error').
            message: Log message.
            step: Optional current step name (e.g., 'provisional', 'refined').
            current: Optional current progress count.
            total: Optional total count.
            current_term: Optional current term being processed.
        """
        log_entry: dict = {"run_id": context.run_id, "level": level, "message": message}
        if step is not None:
            log_entry["step"] = step
        if current is not None:
            log_entry["progress_current"] = current
        if total is not None:
            log_entry["progress_total"] = total
        if current_term is not None:
            log_entry["current_term"] = current_term
        try:
            context.log_callback(log_entry)
        except Exception:
            pass  # Ignore callback errors to prevent pipeline interruption

    def _check_cancellation(self, context: ExecutionContext) -> bool:
        """Check if execution is cancelled.

        Args:
            context: Execution context containing cancel_event.

        Returns:
            bool: True if cancelled, False otherwise.
        """
        if context.cancel_event.is_set():
            self._log(context, "info", "Execution cancelled")
            return True
        return False

    @staticmethod
    def _documents_from_db_rows(rows: list[sqlite3.Row]) -> list[Document]:
        """Convert DB rows to Document objects.

        Args:
            rows: List of sqlite3.Row with 'file_name' and 'content' keys.

        Returns:
            list[Document]: List of Document objects.
        """
        return [
            Document(file_path=row["file_name"], content=row["content"])
            for row in rows
        ]

    @staticmethod
    def _glossary_from_db_rows(rows: list[GlossaryTermRow]) -> Glossary:
        """Convert provisional DB rows to Glossary object.

        Args:
            rows: List of GlossaryTermRow with term data.

        Returns:
            Glossary: Reconstructed Glossary object.
        """
        glossary = Glossary()
        for row in rows:
            term = Term(
                name=row["term_name"],
                definition=row["definition"],
                confidence=row["confidence"],
                occurrences=row["occurrences"],
            )
            glossary.add_term(term)
        return glossary

    @staticmethod
    def _save_glossary_terms(
        conn: sqlite3.Connection,
        glossary: Glossary,
        save_func: Callable[
            [sqlite3.Connection, str, str, float, list[TermOccurrence]], Any
        ],
    ) -> None:
        """Save glossary terms to database using the provided save function.

        Args:
            conn: Project database connection.
            glossary: Glossary to save.
            save_func: Function to save individual terms (e.g., create_provisional_term).
        """
        for term in glossary.terms.values():
            save_func(conn, term.name, term.definition, term.confidence, term.occurrences)

    def _create_progress_callback(
        self,
        context: ExecutionContext,
        step_name: str,
    ) -> Callable[[int, int, str], None]:
        """Create a progress callback for LLM processing steps.

        The callback logs progress with extended fields (step, current, total, term name).

        Args:
            context: Execution context for logging.
            step_name: Name of the current step (e.g., 'provisional', 'refined').

        Returns:
            A callback function that takes (current, total, term_name) arguments.
        """
        def callback(current: int, total: int, term_name: str = "") -> None:
            percent = int((current / total) * 100) if total > 0 else 0
            self._log(
                context,
                "info",
                f"{term_name}: {percent}%",
                step=step_name,
                current=current,
                total=total,
                current_term=term_name,
            )
        return callback

    def execute(
        self,
        conn: sqlite3.Connection,
        scope: str | PipelineScope,
        context: ExecutionContext,
        doc_root: str = ".",
    ) -> None:
        """Execute the pipeline for the given scope.

        Args:
            conn: Project database connection.
            scope: Execution scope (PipelineScope enum or string).
            context: Execution context containing run_id, log_callback, and cancel_event.
            doc_root: Root directory for documents (default: ".").
        """
        # Convert PipelineScope enum to string value
        scope_value = scope.value if isinstance(scope, PipelineScope) else scope

        self._log(context, "info", f"Starting pipeline execution: {scope_value}")

        if self._check_cancellation(context):
            return

        # Clear tables before execution
        self._clear_tables_for_scope(conn, scope_value)

        # Execute based on scope
        if scope_value == PipelineScope.FULL.value:
            self._execute_full(conn, context, doc_root)
        elif scope_value == PipelineScope.FROM_TERMS.value:
            self._execute_from_terms(conn, context)
        elif scope_value == PipelineScope.PROVISIONAL_TO_REFINED.value:
            self._execute_provisional_to_refined(conn, context)
        else:
            self._log(context, "error", f"Unknown scope: {scope_value}")
            raise ValueError(f"Unknown scope: {scope_value}")

        self._log(context, "info", "Pipeline execution completed")

    def _load_documents(
        self, conn: sqlite3.Connection, context: ExecutionContext, doc_root: str = "."
    ) -> list[Document]:
        """Load documents from database or filesystem.

        DB-first approach: Try to load from DB first (GUI mode), fall back to
        filesystem if needed (CLI mode).

        Args:
            conn: Project database connection.
            context: Execution context for logging.
            doc_root: Root directory for documents (default: ".").

        Returns:
            list[Document]: Loaded documents.

        Raises:
            RuntimeError: If no documents found.
        """
        # Try loading from database first (GUI mode)
        doc_rows = list_all_documents(conn)
        if doc_rows:
            self._log(context, "info", "Loading documents from database...")
            return self._documents_from_db_rows(doc_rows)

        # Fall back to filesystem if DB is empty (CLI mode)
        if doc_root and doc_root != ".":
            self._log(context, "info", f"Loading documents from filesystem: {doc_root}")
            loader = DocumentLoader()
            documents = loader.load_directory(doc_root)

            if documents:
                # Save loaded documents to DB
                # Use file_path as file_name to avoid collisions with same basename
                with transaction(conn):
                    delete_all_documents(conn)
                    for document in documents:
                        content_hash = compute_content_hash(document.content)
                        create_document(conn, document.file_path, document.content, content_hash)
                return documents

        # No documents found
        self._log(context, "error", "No documents found")
        raise RuntimeError("Cannot execute pipeline without documents")

    def _execute_full(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        doc_root: str = ".",
    ) -> None:
        """Execute full pipeline (steps 1-5).

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            doc_root: Root directory for documents (default: ".").
        """
        # Step 1: Load documents
        if self._check_cancellation(context):
            return

        documents = self._load_documents(conn, context, doc_root)
        self._log(context, "info", f"Loaded {len(documents)} documents")

        # Step 2: Extract terms
        if self._check_cancellation(context):
            return

        self._log(context, "info", "Extracting terms...")
        extractor = TermExtractor(llm_client=self._llm_client)
        extracted_terms = extractor.extract_terms(documents, return_categories=True)

        # Save extracted terms and build unique list (skip duplicates)
        # Note: extracted_terms is list[ClassifiedTerm] here (return_categories=True)
        seen_terms: set[str] = set()
        unique_terms: list[ClassifiedTerm] = []
        for classified_term in extracted_terms:  # type: ignore[union-attr]
            classified_term: ClassifiedTerm  # type: ignore[no-redef]
            term_text = classified_term.term  # type: ignore[union-attr]
            if term_text in seen_terms:
                continue
            seen_terms.add(term_text)
            unique_terms.append(classified_term)

        # Save all unique terms in a single transaction
        with transaction(conn):
            for classified_term in unique_terms:
                create_term(
                    conn,
                    classified_term.term,
                    category=classified_term.category.value,
                )

        self._log(context, "info", f"Extracted {len(unique_terms)} unique terms (from {len(extracted_terms)} total)")

        # Continue with steps 3-5 (pass unique terms to avoid duplicate LLM calls)
        self._execute_from_terms(conn, context, documents, unique_terms)

    def _execute_from_terms(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        documents: list[Document] | None = None,
        extracted_terms: list[str] | list[ClassifiedTerm] | None = None,
    ) -> None:
        """Execute from terms (steps 3-5).

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            documents: Pre-loaded documents (None to load from DB).
            extracted_terms: Pre-extracted terms as strings or ClassifiedTerms (None to load from DB).
        """
        # Load documents from DB if not provided
        if documents is None:
            if self._check_cancellation(context):
                return
            documents = self._load_documents(conn, context)

        # Load terms from DB if not provided
        if extracted_terms is None:
            if self._check_cancellation(context):
                return

            self._log(context, "info", "Loading terms from database...")
            term_rows = list_all_terms(conn)
            extracted_terms = [row["term_text"] for row in term_rows]

        # Step 3: Generate glossary
        if self._check_cancellation(context):
            return

        self._log(context, "info", "Generating glossary...")
        generator = GlossaryGenerator(llm_client=self._llm_client)
        progress_cb = self._create_progress_callback(context, "provisional")
        glossary = generator.generate(
            extracted_terms, documents, term_progress_callback=progress_cb
        )

        # Save provisional glossary
        with transaction(conn):
            self._save_glossary_terms(conn, glossary, create_provisional_term)

        self._log(context, "info", f"Generated {len(glossary.terms)} terms")

        # Continue with steps 4-5
        self._execute_provisional_to_refined(conn, context, glossary, documents)

    def _execute_provisional_to_refined(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        glossary: Glossary | None = None,
        documents: list[Document] | None = None,
    ) -> None:
        """Execute from provisional to refined (steps 4-5).

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            glossary: Pre-generated provisional glossary (None to load from DB).
            documents: Pre-loaded documents (None to load from DB).
        """
        # Load glossary from DB if not provided
        if glossary is None:
            if self._check_cancellation(context):
                return

            self._log(context, "info", "Loading provisional glossary from database...")
            provisional_rows = list_all_provisional(conn)
            if not provisional_rows:
                self._log(context, "error", "No provisional terms found in database")
                raise RuntimeError("Cannot execute provisional_to_refined without provisional glossary")

            # Reconstruct Glossary from DB rows
            glossary = self._glossary_from_db_rows(provisional_rows)

            self._log(context, "info", f"Loaded {len(provisional_rows)} provisional terms")

        # Load documents from DB if not provided
        if documents is None:
            if self._check_cancellation(context):
                return
            documents = self._load_documents(conn, context)

        # Step 4: Review glossary
        if self._check_cancellation(context):
            return

        self._log(context, "info", "Reviewing glossary...")
        reviewer = GlossaryReviewer(llm_client=self._llm_client)
        issues = reviewer.review(glossary)

        # Save issues
        with transaction(conn):
            for issue in issues:
                create_issue(
                    conn,
                    issue.term_name,
                    issue.issue_type,
                    issue.description,
                )

        self._log(context, "info", f"Found {len(issues)} issues")

        # Step 5: Refine glossary
        if issues:
            if self._check_cancellation(context):
                return

            self._log(context, "info", "Refining glossary...")
            refiner = GlossaryRefiner(llm_client=self._llm_client)
            progress_cb = self._create_progress_callback(context, "refined")
            glossary = refiner.refine(
                glossary, issues, documents, term_progress_callback=progress_cb
            )
            self._log(context, "info", f"Refined {len(glossary.terms)} terms")
        else:
            self._log(context, "info", "No issues found, copying provisional to refined")

        # Check cancellation before saving refined glossary
        if self._check_cancellation(context):
            return

        # Save refined glossary (either refined or copied from provisional)
        with transaction(conn):
            self._save_glossary_terms(conn, glossary, create_refined_term)

    def _clear_tables_for_scope(self, conn: sqlite3.Connection, scope: str) -> None:
        """Clear relevant tables before execution.

        Args:
            conn: Project database connection.
            scope: Execution scope.
        """
        clear_funcs = _SCOPE_CLEAR_FUNCTIONS.get(scope, [])
        with transaction(conn):
            for clear_func in clear_funcs:
                clear_func(conn)
