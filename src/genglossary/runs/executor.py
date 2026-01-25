"""Pipeline executor for running glossary generation steps."""

import hashlib
import sqlite3
from queue import Queue
from threading import Event

from genglossary.db.document_repository import (
    create_document,
    delete_all_documents,
    list_all_documents,
)
from genglossary.db.issue_repository import create_issue, delete_all_issues
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
from genglossary.models.term import Term
from genglossary.term_extractor import TermExtractor


class PipelineExecutor:
    """Executes glossary generation pipeline steps.

    This class handles the execution of the pipeline steps in a background thread,
    with support for cancellation and progress reporting.
    """

    def __init__(self, provider: str = "ollama", model: str = ""):
        """Initialize the PipelineExecutor.

        Args:
            provider: LLM provider name (default: 'ollama').
            model: LLM model name (default: '').
        """
        self._llm_client = create_llm_client(provider=provider, model=model)
        self._run_id: int | None = None
        self._log_queue: Queue | None = None
        self._cancel_event: Event | None = None

    def _log(self, level: str, message: str) -> None:
        """Log a message to the queue.

        Args:
            level: Log level ('info', 'warning', 'error').
            message: Log message.
        """
        if self._log_queue is not None:
            self._log_queue.put({"run_id": self._run_id, "level": level, "message": message})

    def _check_cancellation(self) -> bool:
        """Check if execution is cancelled.

        Returns:
            bool: True if cancelled, False otherwise.
        """
        if self._cancel_event is not None and self._cancel_event.is_set():
            self._log("info", "Execution cancelled")
            return True
        return False

    def execute(
        self,
        conn: sqlite3.Connection,
        scope: str,
        cancel_event: Event,
        log_queue: Queue,
        doc_root: str = ".",
        run_id: int | None = None,
    ) -> None:
        """Execute the pipeline for the given scope.

        Args:
            conn: Project database connection.
            scope: Execution scope ('full', 'from_terms', 'provisional_to_refined').
            cancel_event: Event to signal cancellation.
            log_queue: Queue for log messages.
            doc_root: Root directory for documents (default: ".").
            run_id: Run ID for log filtering (default: None).
        """
        # Set execution context
        self._run_id = run_id
        self._log_queue = log_queue
        self._cancel_event = cancel_event

        self._log("info", f"Starting pipeline execution: {scope}")

        if self._check_cancellation():
            return

        # Clear tables before execution
        self._clear_tables_for_scope(conn, scope)

        # Execute based on scope
        if scope == "full":
            self._execute_full(conn, doc_root)
        elif scope == "from_terms":
            self._execute_from_terms(conn)
        elif scope == "provisional_to_refined":
            self._execute_provisional_to_refined(conn)
        else:
            self._log("error", f"Unknown scope: {scope}")
            return

        self._log("info", "Pipeline execution completed")

    def _load_documents_from_db(self, conn: sqlite3.Connection) -> list[Document]:
        """Load documents from database.

        Args:
            conn: Project database connection.

        Returns:
            list[Document]: Loaded documents.

        Raises:
            RuntimeError: If no documents found or loading fails.
        """
        self._log("info", "Loading documents from database...")
        doc_rows = list_all_documents(conn)
        if not doc_rows:
            self._log("error", "No documents found in database")
            raise RuntimeError("Cannot execute pipeline without documents")

        # Reconstruct Document objects by re-reading files
        loader = DocumentLoader()
        documents = []
        for row in doc_rows:
            try:
                doc = loader.load_file(row["file_path"])
                documents.append(doc)
            except Exception as e:
                self._log("warning", f"Failed to load document {row['file_path']}: {str(e)}")

        if not documents:
            self._log("error", "No documents could be loaded from file system")
            raise RuntimeError("Cannot execute pipeline without documents")

        return documents

    def _execute_full(
        self,
        conn: sqlite3.Connection,
        doc_root: str = ".",
    ) -> None:
        """Execute full pipeline (steps 1-5).

        Args:
            conn: Project database connection.
            doc_root: Root directory for documents (default: ".").
        """
        # Step 1: Load documents
        if self._check_cancellation():
            return

        self._log("info", "Loading documents...")
        loader = DocumentLoader()
        documents = loader.load_directory(doc_root)

        if not documents:
            self._log("error", "No documents found")
            raise RuntimeError("No documents found in doc_root")

        # Save documents to database
        for document in documents:
            content_hash = hashlib.sha256(document.content.encode("utf-8")).hexdigest()
            create_document(conn, document.file_path, content_hash)

        self._log("info", f"Loaded {len(documents)} documents")

        # Step 2: Extract terms
        if self._check_cancellation():
            return

        self._log("info", "Extracting terms...")
        extractor = TermExtractor(llm_client=self._llm_client)
        extracted_terms = extractor.extract_terms(documents, return_categories=True)

        # Save extracted terms
        for classified_term in extracted_terms:  # type: ignore[union-attr]
            create_term(
                conn,
                classified_term.term,  # type: ignore[union-attr]
                category=classified_term.category.value,  # type: ignore[union-attr]
            )

        self._log("info", f"Extracted {len(extracted_terms)} terms")

        # Continue with steps 3-5
        self._execute_from_terms(conn, documents, extracted_terms)

    def _execute_from_terms(
        self,
        conn: sqlite3.Connection,
        documents: list[Document] | None = None,
        extracted_terms: list | None = None,
    ) -> None:
        """Execute from terms (steps 3-5).

        Args:
            conn: Project database connection.
            documents: Pre-loaded documents (None to load from DB).
            extracted_terms: Pre-extracted terms (None to load from DB).
        """
        # Load documents from DB if not provided
        if documents is None:
            if self._check_cancellation():
                return
            documents = self._load_documents_from_db(conn)

        # Load terms from DB if not provided
        if extracted_terms is None:
            if self._check_cancellation():
                return

            self._log("info", "Loading terms from database...")
            term_rows = list_all_terms(conn)
            extracted_terms = [row["term_text"] for row in term_rows]

        # Step 3: Generate glossary
        if self._check_cancellation():
            return

        self._log("info", "Generating glossary...")
        generator = GlossaryGenerator(llm_client=self._llm_client)
        glossary = generator.generate(extracted_terms, documents)

        # Save provisional glossary
        for term in glossary.terms.values():
            create_provisional_term(
                conn,
                term.name,
                term.definition,
                term.confidence,
                term.occurrences,
            )

        self._log("info", f"Generated {len(glossary.terms)} terms")

        # Continue with steps 4-5
        self._execute_provisional_to_refined(conn, glossary, documents)

    def _execute_provisional_to_refined(
        self,
        conn: sqlite3.Connection,
        glossary: Glossary | None = None,
        documents: list[Document] | None = None,
    ) -> None:
        """Execute from provisional to refined (steps 4-5).

        Args:
            conn: Project database connection.
            glossary: Pre-generated provisional glossary (None to load from DB).
            documents: Pre-loaded documents (None to load from DB).
        """
        # Load glossary from DB if not provided
        if glossary is None:
            if self._check_cancellation():
                return

            self._log("info", "Loading provisional glossary from database...")
            provisional_rows = list_all_provisional(conn)
            if not provisional_rows:
                self._log("error", "No provisional terms found in database")
                raise RuntimeError("Cannot execute provisional_to_refined without provisional glossary")

            # Reconstruct Glossary from DB rows
            glossary = Glossary()
            for row in provisional_rows:
                term = Term(
                    name=row["term_name"],
                    definition=row["definition"],
                    confidence=row["confidence"],
                    occurrences=row["occurrences"],
                )
                glossary.add_term(term)

            self._log("info", f"Loaded {len(provisional_rows)} provisional terms")

        # Load documents from DB if not provided
        if documents is None:
            if self._check_cancellation():
                return
            documents = self._load_documents_from_db(conn)

        # Step 4: Review glossary
        if self._check_cancellation():
            return

        self._log("info", "Reviewing glossary...")
        reviewer = GlossaryReviewer(llm_client=self._llm_client)
        issues = reviewer.review(glossary)

        # Save issues
        for issue in issues:
            create_issue(
                conn,
                issue.term_name,
                issue.issue_type,
                issue.description,
            )

        self._log("info", f"Found {len(issues)} issues")

        # Step 5: Refine glossary (only if issues exist)
        if not issues:
            return

        if self._check_cancellation():
            return

        self._log("info", "Refining glossary...")
        refiner = GlossaryRefiner(llm_client=self._llm_client)
        glossary = refiner.refine(glossary, issues, documents)

        # Save refined glossary
        for term in glossary.terms.values():
            create_refined_term(
                conn,
                term.name,
                term.definition,
                term.confidence,
                term.occurrences,
            )

        self._log("info", f"Refined {len(glossary.terms)} terms")

    def _clear_tables_for_scope(self, conn: sqlite3.Connection, scope: str) -> None:
        """Clear relevant tables before execution.

        Args:
            conn: Project database connection.
            scope: Execution scope.
        """
        if scope == "full":
            # Clear all tables for full execution
            delete_all_documents(conn)
            delete_all_terms(conn)
            delete_all_provisional(conn)
            delete_all_issues(conn)
            delete_all_refined(conn)
        elif scope == "from_terms":
            # Clear only glossary-related tables
            delete_all_provisional(conn)
            delete_all_issues(conn)
            delete_all_refined(conn)
        elif scope == "provisional_to_refined":
            # Clear only review and refinement tables
            delete_all_issues(conn)
            delete_all_refined(conn)
