"""Pipeline executor for running glossary generation steps."""

import hashlib
import sqlite3
from queue import Queue
from threading import Event

from genglossary.db.document_repository import create_document, list_all_documents
from genglossary.db.issue_repository import create_issue
from genglossary.db.provisional_repository import (
    create_provisional_term,
    list_all_provisional,
)
from genglossary.db.refined_repository import create_refined_term
from genglossary.db.term_repository import create_term, list_all_terms
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.factory import create_llm_client
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.term_extractor import TermExtractor


class PipelineExecutor:
    """Executes glossary generation pipeline steps.

    This class handles the execution of the pipeline steps in a background thread,
    with support for cancellation and progress reporting.
    """

    def execute(
        self,
        conn: sqlite3.Connection,
        scope: str,
        cancel_event: Event,
        log_queue: Queue,
    ) -> None:
        """Execute the pipeline for the given scope.

        Args:
            conn: Project database connection.
            scope: Execution scope ('full', 'from_terms', 'provisional_to_refined').
            cancel_event: Event to signal cancellation.
            log_queue: Queue for log messages.
        """
        # Log execution start
        log_queue.put({"level": "info", "message": f"Starting pipeline execution: {scope}"})

        # Check cancellation before starting
        if cancel_event.is_set():
            log_queue.put({"level": "info", "message": "Execution cancelled"})
            return

        # Execute based on scope
        if scope == "full":
            self._execute_full(conn, cancel_event, log_queue)
        elif scope == "from_terms":
            self._execute_from_terms(conn, cancel_event, log_queue)
        elif scope == "provisional_to_refined":
            self._execute_provisional_to_refined(conn, cancel_event, log_queue)
        else:
            log_queue.put({"level": "error", "message": f"Unknown scope: {scope}"})
            return

        log_queue.put({"level": "info", "message": "Pipeline execution completed"})

    def _execute_full(
        self, conn: sqlite3.Connection, cancel_event: Event, log_queue: Queue
    ) -> None:
        """Execute full pipeline (steps 1-5).

        Args:
            conn: Project database connection.
            cancel_event: Event to signal cancellation.
            log_queue: Queue for log messages.
        """
        # Step 1: Load documents
        if cancel_event.is_set():
            return

        log_queue.put({"level": "info", "message": "Loading documents..."})
        loader = DocumentLoader()
        documents = loader.load_directory(".")  # TODO: Get actual input dir

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
        llm_client = create_llm_client(provider="ollama")
        extractor = TermExtractor(llm_client=llm_client)
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
            # TODO: Reconstruct Document objects from DB
            # For now, skip
            documents = []

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
        llm_client = create_llm_client(provider="ollama")
        generator = GlossaryGenerator(llm_client=llm_client)
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
            # TODO: Reconstruct Glossary from DB
            # For now, create empty glossary
            glossary = Glossary()

        # Load documents from DB if not provided
        if documents is None:
            if cancel_event.is_set():
                return

            log_queue.put({"level": "info", "message": "Loading documents from database..."})
            # TODO: Reconstruct Document objects from DB
            # For now, skip
            documents = []

        # Step 4: Review glossary
        if cancel_event.is_set():
            return

        log_queue.put({"level": "info", "message": "Reviewing glossary..."})
        llm_client = create_llm_client(provider="ollama")
        reviewer = GlossaryReviewer(llm_client=llm_client)
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
            llm_client = create_llm_client(provider="ollama")
            refiner = GlossaryRefiner(llm_client=llm_client)
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
