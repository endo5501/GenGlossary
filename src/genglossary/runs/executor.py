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
from genglossary.db.issue_repository import create_issues_batch, delete_all_issues, list_all_issues
from genglossary.db.models import GlossaryTermRow
from genglossary.db.provisional_repository import (
    create_provisional_terms_batch,
    delete_all_provisional,
    list_all_provisional,
)
from genglossary.db.refined_repository import create_refined_terms_batch, delete_all_refined
from genglossary.db.runs_repository import update_run_progress
from genglossary.db.term_repository import create_terms_batch, delete_all_terms, list_all_terms
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.factory import create_llm_client
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import ClassifiedTerm, Term, TermOccurrence
from genglossary.term_extractor import TermExtractor
from genglossary.utils.hash import compute_content_hash
from genglossary.utils.path_utils import to_safe_relative_path


class PipelineCancelledException(Exception):
    """Raised when pipeline execution is cancelled by user request."""


class PipelineScope(Enum):
    """Enumeration of pipeline execution scopes."""

    FULL = "full"
    EXTRACT = "extract"
    GENERATE = "generate"
    REVIEW = "review"
    REFINE = "refine"

# Map of scope to clear functions for table cleanup
_SCOPE_CLEAR_FUNCTIONS: dict[PipelineScope, list[Callable[[sqlite3.Connection], None]]] = {
    PipelineScope.FULL: [delete_all_provisional, delete_all_issues, delete_all_refined],
    PipelineScope.EXTRACT: [delete_all_terms],
    PipelineScope.GENERATE: [delete_all_provisional],
    PipelineScope.REVIEW: [delete_all_issues],
    PipelineScope.REFINE: [delete_all_refined],
}



def _cancellable(func: Callable) -> Callable:
    """Decorator that checks for cancellation before executing a method.

    The decorated method must receive an ExecutionContext instance as one of its
    positional or keyword arguments. If cancellation is detected, raises
    PipelineCancelledException without executing.

    Args:
        func: The method to decorate.

    Returns:
        Wrapped method that checks cancellation at entry.

    Raises:
        PipelineCancelledException: If cancellation was requested.
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

        if context is not None:
            self._check_cancellation(context)  # Raises if cancelled
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

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "",
        base_url: str | None = None,
        review_batch_size: int = GlossaryReviewer.DEFAULT_BATCH_SIZE,
    ):
        """Initialize the PipelineExecutor.

        Args:
            provider: LLM provider name (default: 'ollama').
            model: LLM model name (default: '').
            base_url: Base URL for the LLM API (optional).
            review_batch_size: Number of terms per batch for review step.
                Defaults to GlossaryReviewer.DEFAULT_BATCH_SIZE (20).
        """
        self._llm_client = create_llm_client(provider=provider, model=model, base_url=base_url)
        self._review_batch_size = review_batch_size

    def close(self) -> None:
        """Close the LLM client to cancel any ongoing requests.

        This method can be called from another thread to force-cancel
        ongoing LLM API calls by closing the underlying HTTP connection.
        """
        if hasattr(self._llm_client, 'close'):
            self._llm_client.close()

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

    def _check_cancellation(self, context: ExecutionContext) -> None:
        """Check if execution is cancelled and raise if so.

        Args:
            context: Execution context containing cancel_event.

        Raises:
            PipelineCancelledException: If cancellation was requested.
        """
        if context.cancel_event.is_set():
            self._log(context, "info", "Execution cancelled")
            raise PipelineCancelledException()

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
        conn: sqlite3.Connection,
        context: ExecutionContext,
        step_name: str,
    ) -> Callable[[int, int, str], None]:
        """Create a progress callback for LLM processing steps.

        The callback logs progress with extended fields (step, current, total, term name)
        and updates the database with the current step and progress.

        Args:
            conn: Project database connection.
            context: Execution context for logging.
            step_name: Name of the current step (e.g., 'extract', 'provisional', 'issues', 'refined').

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
            # Update database with current step and progress
            update_run_progress(conn, context.run_id, current, total, step_name)
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

        Raises:
            PipelineCancelledException: If execution is cancelled.
            ValueError: If scope is unknown.
        """
        # Normalize to PipelineScope enum
        scope_enum = scope if isinstance(scope, PipelineScope) else PipelineScope(scope)

        self._log(context, "info", f"Starting pipeline execution: {scope_enum.value}")

        self._check_cancellation(context)  # Raises if cancelled

        # Clear tables before execution
        self._clear_tables_for_scope(conn, scope_enum)

        # Execute based on scope using dispatch table with direct method references
        scope_handlers = {
            PipelineScope.FULL: self._execute_full,
            PipelineScope.EXTRACT: self._execute_extract,
            PipelineScope.GENERATE: self._execute_generate,
            PipelineScope.REVIEW: self._execute_review,
            PipelineScope.REFINE: self._execute_refine,
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
                with transaction(conn):
                    delete_all_documents(conn)
                    docs_data = [
                        (
                            to_safe_relative_path(document.file_path, doc_root),
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

    def _load_provisional_glossary(
        self, conn: sqlite3.Connection, context: ExecutionContext, step_name: str
    ) -> Glossary:
        """Load provisional glossary from database.

        Args:
            conn: Project database connection.
            context: Execution context for logging.
            step_name: Name of the step requesting the glossary (for error messages).

        Returns:
            Glossary: Loaded provisional glossary.

        Raises:
            RuntimeError: If no provisional glossary found.
        """
        self._log(context, "info", "Loading provisional glossary from database...")
        provisional_rows = list_all_provisional(conn)
        if not provisional_rows:
            self._log(context, "error", "No provisional terms found in database")
            raise RuntimeError(f"Cannot execute {step_name} without provisional glossary")
        glossary = self._glossary_from_db_rows(provisional_rows)
        self._log(context, "info", f"Loaded {len(provisional_rows)} provisional terms")
        return glossary

    @_cancellable
    def _execute_full(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        doc_root: str = ".",
    ) -> None:
        """Execute full pipeline (generate → review → refine).

        Extract is excluded from the full pipeline. Terms must already exist
        in the database (via prior extract run or auto-extract on file add).

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            doc_root: Root directory for documents (default: ".").

        Raises:
            PipelineCancelledException: If execution is cancelled.
            RuntimeError: If no terms found in database.
        """
        # Step 1: Load documents
        documents = self._load_documents(conn, context, doc_root)
        self._log(context, "info", f"Loaded {len(documents)} documents")

        # Step 2: Load existing terms from DB (extract is skipped)
        self._log(context, "info", "Loading terms from database...")
        term_rows = list_all_terms(conn)
        if not term_rows:
            self._log(context, "error", "No terms found in database")
            raise RuntimeError("Cannot execute full pipeline without extracted terms")
        extracted_terms = [row["term_text"] for row in term_rows]

        # Step 3: Generate glossary
        glossary = self._do_generate(conn, context, documents, extracted_terms)

        # Step 4: Review glossary
        issues = self._do_review(conn, context, glossary)

        # Step 5: Refine glossary
        self._do_refine(conn, context, glossary, issues, documents)

    @_cancellable
    def _execute_extract(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        doc_root: str = ".",
    ) -> None:
        """Execute extract step only.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            doc_root: Root directory for documents (default: ".").

        Raises:
            PipelineCancelledException: If execution is cancelled.
        """
        documents = self._load_documents(conn, context, doc_root)
        self._log(context, "info", f"Loaded {len(documents)} documents")
        self._do_extract(conn, context, documents)

    @_cancellable
    def _execute_generate(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        _doc_root: str = ".",
    ) -> None:
        """Execute generate step only.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            _doc_root: Root directory for documents (unused).

        Raises:
            PipelineCancelledException: If execution is cancelled.
            RuntimeError: If no terms found in database.
        """
        documents = self._load_documents(conn, context)

        # Load terms from DB
        self._log(context, "info", "Loading terms from database...")
        term_rows = list_all_terms(conn)
        if not term_rows:
            self._log(context, "error", "No terms found in database")
            raise RuntimeError("Cannot execute generate without extracted terms")
        extracted_terms = [row["term_text"] for row in term_rows]

        self._do_generate(conn, context, documents, extracted_terms)

    @_cancellable
    def _execute_review(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        _doc_root: str = ".",
    ) -> None:
        """Execute review step only.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            _doc_root: Root directory for documents (unused).

        Raises:
            PipelineCancelledException: If execution is cancelled.
            RuntimeError: If no provisional glossary found in database.
        """
        glossary = self._load_provisional_glossary(conn, context, "review")
        self._do_review(conn, context, glossary)

    @_cancellable
    def _execute_refine(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        _doc_root: str = ".",
    ) -> None:
        """Execute refine step only.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            _doc_root: Root directory for documents (unused).

        Raises:
            PipelineCancelledException: If execution is cancelled.
            RuntimeError: If no provisional glossary found in database.
        """
        documents = self._load_documents(conn, context)
        glossary = self._load_provisional_glossary(conn, context, "refine")

        # Load issues from DB
        self._log(context, "info", "Loading issues from database...")
        issue_rows = list_all_issues(conn)
        issues = [
            GlossaryIssue(
                term_name=row["term_name"],
                issue_type=row["issue_type"],
                description=row["description"],
            )
            for row in issue_rows
        ]
        self._log(context, "info", f"Loaded {len(issues)} issues")

        self._do_refine(conn, context, glossary, issues, documents)

    def _do_extract(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        documents: list[Document],
    ) -> list[ClassifiedTerm]:
        """Execute term extraction and save to DB.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            documents: Documents to extract terms from.

        Returns:
            list[ClassifiedTerm]: Unique extracted terms.

        Raises:
            PipelineCancelledException: If execution is cancelled.
        """
        self._check_cancellation(context)

        self._log(context, "info", "用語抽出を開始しました...")
        extractor = TermExtractor(
            llm_client=self._llm_client,
            excluded_term_repo=conn,
            required_term_repo=conn,
        )

        # Create progress callback for batch progress
        progress_cb = self._create_progress_callback(conn, context, "extract")

        extracted_terms = extractor.extract_terms(
            documents,
            progress_callback=lambda current, total: progress_cb(current, total, ""),
            return_categories=True,
        )

        # Build unique list (skip duplicates)
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
        return unique_terms

    def _do_generate(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        documents: list[Document],
        extracted_terms: list[str] | list[ClassifiedTerm],
    ) -> Glossary:
        """Execute glossary generation and save to DB.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            documents: Source documents.
            extracted_terms: Terms to generate definitions for.

        Returns:
            Glossary: Generated provisional glossary.

        Raises:
            PipelineCancelledException: If execution is cancelled.
        """
        self._check_cancellation(context)

        self._log(context, "info", "Generating glossary...")
        generator = GlossaryGenerator(llm_client=self._llm_client)
        progress_cb = self._create_progress_callback(conn, context, "provisional")
        try:
            glossary = generator.generate(
                extracted_terms, documents,
                term_progress_callback=progress_cb,
                cancel_event=context.cancel_event,
            )
        except Exception as e:
            self._log(context, "error", f"Generation failed: {e}")
            raise

        # Save provisional glossary using batch insert
        with transaction(conn):
            self._save_glossary_terms_batch(conn, glossary, create_provisional_terms_batch)

        self._log(context, "info", f"Generated {len(glossary.terms)} terms")
        return glossary

    def _do_review(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        glossary: Glossary,
    ) -> list:
        """Execute glossary review and save issues to DB.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            glossary: Provisional glossary to review.

        Returns:
            list[GlossaryIssue]: Found issues.

        Raises:
            PipelineCancelledException: If execution is cancelled.
        """
        self._check_cancellation(context)

        self._log(context, "info", "Reviewing glossary...")
        reviewer = GlossaryReviewer(
            llm_client=self._llm_client, batch_size=self._review_batch_size
        )

        progress_cb = self._create_progress_callback(conn, context, "issues")

        # Send initial step update before processing
        # This ensures UI shows "Issues" step immediately, even if glossary is empty
        # Use batch count (same as GlossaryReviewer) for consistent progress semantics
        term_count = len(glossary.terms)
        total_batches = (
            (term_count + self._review_batch_size - 1) // self._review_batch_size
            if term_count > 0
            else 0
        )
        progress_cb(0, total_batches, "")

        def on_batch_progress(current: int, total: int) -> None:
            progress_cb(current, total, "")

        try:
            issues = reviewer.review(
                glossary,
                cancel_event=context.cancel_event,
                batch_progress_callback=on_batch_progress,
            )
        except Exception as e:
            self._log(context, "error", f"Review failed: {e}")
            raise

        # If review was cancelled, raise exception
        if issues is None:
            self._log(context, "info", "Review cancelled")
            raise PipelineCancelledException()

        # Save issues using batch insert
        with transaction(conn):
            issues_data = [
                (issue.term_name, issue.issue_type, issue.description)
                for issue in issues
            ]
            create_issues_batch(conn, issues_data)

        self._log(context, "info", f"Found {len(issues)} issues")
        return issues

    def _do_refine(
        self,
        conn: sqlite3.Connection,
        context: ExecutionContext,
        glossary: Glossary,
        issues: list,
        documents: list[Document],
    ) -> Glossary:
        """Execute glossary refinement and save to DB.

        Args:
            conn: Project database connection.
            context: Execution context for logging and cancellation.
            glossary: Provisional glossary to refine.
            issues: Issues to address.
            documents: Source documents.

        Returns:
            Glossary: Refined glossary.

        Raises:
            PipelineCancelledException: If execution is cancelled.
        """
        if issues:
            self._check_cancellation(context)

            self._log(context, "info", "Refining glossary...")
            refiner = GlossaryRefiner(llm_client=self._llm_client)
            progress_cb = self._create_progress_callback(conn, context, "refined")
            try:
                glossary = refiner.refine(
                    glossary, issues, documents,
                    term_progress_callback=progress_cb,
                    cancel_event=context.cancel_event,
                )
            except Exception as e:
                self._log(context, "error", f"Refinement failed: {e}")
                raise
            self._log(context, "info", f"Refined {len(glossary.terms)} terms")
        else:
            self._log(context, "info", "No issues found, copying provisional to refined")

        # Save refined glossary using batch insert
        with transaction(conn):
            self._save_glossary_terms_batch(conn, glossary, create_refined_terms_batch)

        return glossary

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
