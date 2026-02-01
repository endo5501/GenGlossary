"""Pipeline executor for running glossary generation steps."""

import sqlite3
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from pathlib import Path
from threading import Event
from typing import Callable

from genglossary.db.connection import transaction
from genglossary.db.document_repository import (
    create_documents_batch,
    delete_all_documents,
    list_all_documents,
)
from genglossary.db.issue_repository import create_issues_batch, delete_all_issues
from genglossary.db.models import GlossaryTermRow
from genglossary.db.provisional_repository import (
    create_provisional_terms_batch,
    delete_all_provisional,
    list_all_provisional,
)
from genglossary.db.refined_repository import create_refined_terms_batch, delete_all_refined
from genglossary.db.term_repository import create_terms_batch, delete_all_terms, list_all_terms
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


def _safe_relative_path(file_path: Path, doc_root: Path) -> str:
    """Convert file path to safe relative path in POSIX format.

    Args:
        file_path: Target file path.
        doc_root: Document root directory.

    Returns:
        Relative path in POSIX format (using /).

    Raises:
        ValueError: If file is outside doc_root.
    """
    resolved_file = file_path.resolve()
    resolved_root = doc_root.resolve()

    if not resolved_file.is_relative_to(resolved_root):
        raise ValueError(f"File is outside doc_root: {file_path}")

    return resolved_file.relative_to(resolved_root).as_posix()


class PipelineScope(Enum):
    """Enumeration of pipeline execution scopes."""

    FULL = "full"
    FROM_TERMS = "from_terms"
    PROVISIONAL_TO_REFINED = "provisional_to_refined"

# Map of scope to clear functions for table cleanup
_SCOPE_CLEAR_FUNCTIONS: dict[PipelineScope, list[Callable[[sqlite3.Connection], None]]] = {
    PipelineScope.FULL: [delete_all_terms, delete_all_provisional, delete_all_issues, delete_all_refined],
    PipelineScope.FROM_TERMS: [delete_all_provisional, delete_all_issues, delete_all_refined],
    PipelineScope.PROVISIONAL_TO_REFINED: [delete_all_issues, delete_all_refined],
}



def _cancellable(func: Callable) -> Callable:
    """Decorator that checks for cancellation before executing a method.

    The decorated method must receive an ExecutionContext instance as one of its
    positional or keyword arguments. If cancellation is detected, the method
    returns None without executing.

    This decorator helps reduce duplication of the common pattern:
        if self._check_cancellation(context):
            return

    Args:
        func: The method to decorate.

    Returns:
        Wrapped method that checks cancellation at entry.
    """
    @wraps(func)
    def wrapper(self: "PipelineExecutor", *args, **kwargs):  # type: ignore[no-untyped-def]
        # Find context in kwargs first
        context = kwargs.get("context")
        if context is None:
            # Search in positional args
            for arg in args:
                if isinstance(arg, ExecutionContext):
                    context = arg
                    break

        if context is not None and self._check_cancellation(context):
            return None
        return func(self, *args, **kwargs)
    return wrapper


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
        optional_fields = {
            "step": step,
            "progress_current": current,
            "progress_total": total,
            "current_term": current_term,
        }
        log_entry: dict = {
            "run_id": context.run_id,
            "level": level,
            "message": message,
            **{k: v for k, v in optional_fields.items() if v is not None},
        }
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
    def _save_glossary_terms_batch(
        conn: sqlite3.Connection,
        glossary: Glossary,
        batch_func: Callable[
            [sqlite3.Connection, list[tuple[str, str, float, list[TermOccurrence]]]], None
        ],
    ) -> None:
        """Save glossary terms to database using batch insert.

        Args:
            conn: Project database connection.
            glossary: Glossary to save.
            batch_func: Batch function (e.g., create_provisional_terms_batch).
        """
        terms_data = [
            (term.name, term.definition, term.confidence, term.occurrences)
            for term in glossary.terms.values()
        ]
        batch_func(conn, terms_data)

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
            # Normalize term_name: treat whitespace-only as empty
            term_name = term_name.strip() if term_name else ""
            # Format message: include term_name only if not empty
            message = f"{term_name}: {percent}%" if term_name else f"{percent}%"
            self._log(
                context,
                "info",
                message,
                step=step_name,
                current=current,
                total=total,
                # Only include current_term if not empty
                current_term=term_name or None,
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
        # Normalize to PipelineScope enum
        scope_enum = scope if isinstance(scope, PipelineScope) else PipelineScope(scope)

        self._log(context, "info", f"Starting pipeline execution: {scope_enum.value}")

        if self._check_cancellation(context):
            return

        # Clear tables before execution
        self._clear_tables_for_scope(conn, scope_enum)

        # Execute based on scope using dispatch table with direct method references
        scope_handlers = {
            PipelineScope.FULL: self._execute_full,
            PipelineScope.FROM_TERMS: self._execute_from_terms,
            PipelineScope.PROVISIONAL_TO_REFINED: self._execute_provisional_to_refined,
        }

        handler = scope_handlers.get(scope_enum)
        if handler is None:
            self._log(context, "error", f"Unknown scope: {scope_enum}")
            raise ValueError(f"Unknown scope: {scope_enum}")

        handler(conn, context, doc_root)

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
                # Save loaded documents to DB using batch insert
                # Use relative path from doc_root as file_name to:
                # - Avoid same basename collisions (e.g., docs/README.md vs examples/README.md)
                # - Prevent server path leakage via API/logs (security)
                # - Improve portability when moving DB between environments
                # - Reject files outside doc_root for security (path traversal prevention)
                doc_root_path = Path(doc_root)
                with transaction(conn):
                    delete_all_documents(conn)
                    docs_data = [
                        (
                            _safe_relative_path(Path(document.file_path), doc_root_path),
                            document.content,
                            compute_content_hash(document.content),
                        )
                        for document in documents
                    ]
                    create_documents_batch(conn, docs_data)
                return documents

        # No documents found
        self._log(context, "error", "No documents found")
        raise RuntimeError("Cannot execute pipeline without documents")

    @_cancellable
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
        for classified_term in extracted_terms:
            if classified_term.term in seen_terms:
                continue
            seen_terms.add(classified_term.term)
            unique_terms.append(classified_term)

        # Save all unique terms in a single transaction using batch insert
        with transaction(conn):
            terms_data = [
                (classified_term.term, classified_term.category.value)
                for classified_term in unique_terms
            ]
            create_terms_batch(conn, terms_data)

        self._log(context, "info", f"Extracted {len(unique_terms)} unique terms (from {len(extracted_terms)} total)")

        # Continue with steps 3-5 (pass unique terms to avoid duplicate LLM calls)
        self._execute_from_terms(conn, context, documents=documents, extracted_terms=unique_terms)

    @_cancellable
    def _execute_from_terms(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        _doc_root: str = ".",
        documents: list[Document] | None = None,
        extracted_terms: list[str] | list[ClassifiedTerm] | None = None,
    ) -> None:
        """Execute from terms (steps 3-5).

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            _doc_root: Root directory for documents (unused, for unified signature).
            documents: Pre-loaded documents (None to load from DB).
            extracted_terms: Pre-extracted terms as strings or ClassifiedTerms (None to load from DB).
        """
        # Load documents from DB if not provided
        if documents is None:
            documents = self._load_documents(conn, context)

        # Load terms from DB if not provided
        if extracted_terms is None:
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
            extracted_terms, documents,
            term_progress_callback=progress_cb,
            cancel_event=context.cancel_event,
        )

        # Check cancellation before saving provisional glossary
        if self._check_cancellation(context):
            return

        # Save provisional glossary using batch insert
        with transaction(conn):
            self._save_glossary_terms_batch(conn, glossary, create_provisional_terms_batch)

        self._log(context, "info", f"Generated {len(glossary.terms)} terms")

        # Continue with steps 4-5
        self._execute_provisional_to_refined(conn, context, glossary=glossary, documents=documents)

    @_cancellable
    def _execute_provisional_to_refined(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        _doc_root: str = ".",
        glossary: Glossary | None = None,
        documents: list[Document] | None = None,
    ) -> None:
        """Execute from provisional to refined (steps 4-5).

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            _doc_root: Root directory for documents (unused, for unified signature).
            glossary: Pre-generated provisional glossary (None to load from DB).
            documents: Pre-loaded documents (None to load from DB).
        """
        # Load glossary from DB if not provided
        if glossary is None:
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
            documents = self._load_documents(conn, context)

        # Step 4: Review glossary
        if self._check_cancellation(context):
            return

        self._log(context, "info", "Reviewing glossary...")
        reviewer = GlossaryReviewer(llm_client=self._llm_client)
        issues = reviewer.review(glossary, cancel_event=context.cancel_event)

        # If review was cancelled, return early without saving
        if issues is None:
            self._log(context, "info", "Review cancelled")
            return

        # Save issues using batch insert
        with transaction(conn):
            issues_data = [
                (issue.term_name, issue.issue_type, issue.description)
                for issue in issues
            ]
            create_issues_batch(conn, issues_data)

        self._log(context, "info", f"Found {len(issues)} issues")

        # Step 5: Refine glossary
        if issues:
            if self._check_cancellation(context):
                return

            self._log(context, "info", "Refining glossary...")
            refiner = GlossaryRefiner(llm_client=self._llm_client)
            progress_cb = self._create_progress_callback(context, "refined")
            glossary = refiner.refine(
                glossary, issues, documents,
                term_progress_callback=progress_cb,
                cancel_event=context.cancel_event,
            )
            self._log(context, "info", f"Refined {len(glossary.terms)} terms")
        else:
            self._log(context, "info", "No issues found, copying provisional to refined")

        # Check cancellation before saving refined glossary
        if self._check_cancellation(context):
            return

        # Save refined glossary (either refined or copied from provisional) using batch insert
        with transaction(conn):
            self._save_glossary_terms_batch(conn, glossary, create_refined_terms_batch)

    def _clear_tables_for_scope(self, conn: sqlite3.Connection, scope: PipelineScope) -> None:
        """Clear relevant tables before execution.

        Args:
            conn: Project database connection.
            scope: Execution scope (PipelineScope enum).
        """
        clear_funcs = _SCOPE_CLEAR_FUNCTIONS.get(scope, [])
        with transaction(conn):
            for clear_func in clear_funcs:
                clear_func(conn)
