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

    def execute(
        self,
        conn: sqlite3.Connection,
        scope: str,
        cancel_event: Event,
        log_queue: Queue,
        doc_root: str = ".",
    ) -> None:
        """Execute the pipeline for the given scope.

        Args:
            conn: Project database connection.
            scope: Execution scope ('full', 'from_terms', 'provisional_to_refined').
            cancel_event: Event to signal cancellation.
            log_queue: Queue for log messages.
            doc_root: Root directory for documents (default: ".").
        """
        # Log execution start
        log_queue.put({"level": "info", "message": f"Starting pipeline execution: {scope}"})

        # Check cancellation before starting
        if cancel_event.is_set():
            log_queue.put({"level": "info", "message": "Execution cancelled"})
            return

        # Clear tables before execution
        self._clear_tables_for_scope(conn, scope)

        # Execute based on scope
        if scope == "full":
            self._execute_full(conn, cancel_event, log_queue, doc_root)
        elif scope == "from_terms":
            self._execute_from_terms(conn, cancel_event, log_queue, documents=None, extracted_terms=None)
        elif scope == "provisional_to_refined":
            self._execute_provisional_to_refined(conn, cancel_event, log_queue, glossary=None, documents=None)
        else:
            log_queue.put({"level": "error", "message": f"Unknown scope: {scope}"})
            return

        log_queue.put({"level": "info", "message": "Pipeline execution completed"})

    def _execute_full(
        self,
        conn: sqlite3.Connection,
        cancel_event: Event,
        log_queue: Queue,
        doc_root: str = ".",
    ) -> None:
        """Execute full pipeline (steps 1-5).

        Args:
            conn: Project database connection.
            cancel_event: Event to signal cancellation.
            log_queue: Queue for log messages.
            doc_root: Root directory for documents (default: ".").
        """
        # Step 1: Load documents
        if cancel_event.is_set():
            return

        log_queue.put({"level": "info", "message": "Loading documents..."})
        loader = DocumentLoader()
        documents = loader.load_directory(doc_root)

        if not documents:
            log_queue.put({"level": "error", "message": "No documents found"})
            return

        # Save documents to database
        for document in documents:
            content_hash = hashlib.sha256(document.content.encode("utf-8")).hexdigest()
            create_document(conn, document.file_path, content_hash)

        log_queue.put({"level": "info", "message": f"Loaded {len(documents)} documents"})

        # Step 2: Extract terms
        if cancel_event.is_set():
            return

        log_queue.put({"level": "info", "message": "Extracting terms..."})
        extractor = TermExtractor(llm_client=self._llm_client)
        extracted_terms = extractor.extract_terms(documents, return_categories=True)

        # Save extracted terms
        for classified_term in extracted_terms:  # type: ignore[union-attr]
            create_term(
                conn,
                classified_term.term,  # type: ignore[union-attr]
                category=classified_term.category.value,  # type: ignore[union-attr]
            )

        log_queue.put({"level": "info", "message": f"Extracted {len(extracted_terms)} terms"})

        # Continue with steps 3-5
        self._execute_from_terms(conn, cancel_event, log_queue, documents, extracted_terms)

    def _execute_from_terms(
        self,
        conn: sqlite3.Connection,
        cancel_event: Event,
        log_queue: Queue,
        documents: list[Document] | None = None,
        extracted_terms: list | None = None,
    ) -> None:
        """Execute from terms (steps 3-5).

        Args:
            conn: Project database connection.
            cancel_event: Event to signal cancellation.
            log_queue: Queue for log messages.
            documents: Pre-loaded documents (None to load from DB).
            extracted_terms: Pre-extracted terms (None to load from DB).
        """
        # Load documents from DB if not provided
        if documents is None:
            if cancel_event.is_set():
                return

            log_queue.put({"level": "info", "message": "Loading documents from database..."})
            doc_rows = list_all_documents(conn)
            if not doc_rows:
                log_queue.put({"level": "error", "message": "No documents found in database"})
                raise RuntimeError("Cannot execute pipeline without documents")

            # Reconstruct Document objects by re-reading files
            loader = DocumentLoader()
            documents = []
            for row in doc_rows:
                try:
                    # Re-read document from file system
                    doc = loader.load_file(row["file_path"])
                    documents.append(doc)
                except Exception as e:
                    log_queue.put({
                        "level": "warning",
                        "message": f"Failed to load document {row['file_path']}: {str(e)}"
                    })

            if not documents:
                log_queue.put({"level": "error", "message": "No documents could be loaded from file system"})
                raise RuntimeError("Cannot execute pipeline without documents")

        # Load terms from DB if not provided
        if extracted_terms is None:
            if cancel_event.is_set():
                return

            log_queue.put({"level": "info", "message": "Loading terms from database..."})
            term_rows = list_all_terms(conn)
            extracted_terms = [row["term_text"] for row in term_rows]

        # Step 3: Generate glossary
        if cancel_event.is_set():
            return

        log_queue.put({"level": "info", "message": "Generating glossary..."})
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

        log_queue.put({"level": "info", "message": f"Generated {len(glossary.terms)} terms"})

        # Continue with steps 4-5
        self._execute_provisional_to_refined(conn, cancel_event, log_queue, glossary, documents)

    def _execute_provisional_to_refined(
        self,
        conn: sqlite3.Connection,
        cancel_event: Event,
        log_queue: Queue,
        glossary: Glossary | None = None,
        documents: list[Document] | None = None,
    ) -> None:
        """Execute from provisional to refined (steps 4-5).

        Args:
            conn: Project database connection.
            cancel_event: Event to signal cancellation.
            log_queue: Queue for log messages.
            glossary: Pre-generated provisional glossary (None to load from DB).
            documents: Pre-loaded documents (None to load from DB).
        """
        # Load glossary from DB if not provided
        if glossary is None:
            if cancel_event.is_set():
                return

            log_queue.put({"level": "info", "message": "Loading provisional glossary from database..."})
            provisional_rows = list_all_provisional(conn)
            if not provisional_rows:
                log_queue.put({"level": "error", "message": "No provisional terms found in database"})
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

            log_queue.put({"level": "info", "message": f"Loaded {len(provisional_rows)} provisional terms"})

        # Load documents from DB if not provided
        if documents is None:
            if cancel_event.is_set():
                return

            log_queue.put({"level": "info", "message": "Loading documents from database..."})
            doc_rows = list_all_documents(conn)
            if not doc_rows:
                log_queue.put({"level": "error", "message": "No documents found in database"})
                raise RuntimeError("Cannot execute pipeline without documents")

            # Reconstruct Document objects by re-reading files
            loader = DocumentLoader()
            documents = []
            for row in doc_rows:
                try:
                    # Re-read document from file system
                    doc = loader.load_file(row["file_path"])
                    documents.append(doc)
                except Exception as e:
                    log_queue.put({
                        "level": "warning",
                        "message": f"Failed to load document {row['file_path']}: {str(e)}"
                    })

            if not documents:
                log_queue.put({"level": "error", "message": "No documents could be loaded from file system"})
                raise RuntimeError("Cannot execute pipeline without documents")

        # Step 4: Review glossary
        if cancel_event.is_set():
            return

        log_queue.put({"level": "info", "message": "Reviewing glossary..."})
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

        log_queue.put({"level": "info", "message": f"Found {len(issues)} issues"})

        # Step 5: Refine glossary (only if issues exist)
        if issues:
            if cancel_event.is_set():
                return

            log_queue.put({"level": "info", "message": "Refining glossary..."})
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

            log_queue.put({"level": "info", "message": f"Refined {len(glossary.terms)} terms"})

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
