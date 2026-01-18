"""Tests for document_repository module."""

import sqlite3

import pytest

from genglossary.db.document_repository import (
    create_document,
    get_document,
    get_document_by_path,
    list_documents_by_run,
)
from genglossary.db.run_repository import create_run
from genglossary.db.schema import initialize_db


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized.

    Args:
        in_memory_db: Base in-memory database fixture.

    Returns:
        sqlite3.Connection: Database with schema initialized.
    """
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateDocument:
    """Test create_document function."""

    def test_create_document_returns_document_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_document returns a document ID."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        doc_id = create_document(
            db_with_schema,
            run_id=run_id,
            file_path="/path/to/doc.txt",
            content_hash="abc123",
        )

        assert isinstance(doc_id, int)
        assert doc_id > 0

    def test_create_document_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_document stores data correctly."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        doc_id = create_document(
            db_with_schema,
            run_id=run_id,
            file_path="/path/to/doc.txt",
            content_hash="abc123",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["run_id"] == run_id
        assert row["file_path"] == "/path/to/doc.txt"
        assert row["content_hash"] == "abc123"

    def test_create_document_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that (run_id, file_path) must be unique."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        # Create first document
        create_document(
            db_with_schema,
            run_id=run_id,
            file_path="/path/to/doc.txt",
            content_hash="abc123",
        )

        # Try to create duplicate
        with pytest.raises(sqlite3.IntegrityError):
            create_document(
                db_with_schema,
                run_id=run_id,
                file_path="/path/to/doc.txt",
                content_hash="def456",
            )


class TestGetDocument:
    """Test get_document function."""

    def test_get_document_returns_document_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document returns document data."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")
        doc_id = create_document(
            db_with_schema,
            run_id=run_id,
            file_path="/path/to/doc.txt",
            content_hash="abc123",
        )

        doc = get_document(db_with_schema, doc_id)

        assert doc is not None
        assert doc["id"] == doc_id
        assert doc["run_id"] == run_id
        assert doc["file_path"] == "/path/to/doc.txt"
        assert doc["content_hash"] == "abc123"

    def test_get_document_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document returns None for non-existent ID."""
        doc = get_document(db_with_schema, 999)

        assert doc is None


class TestListDocumentsByRun:
    """Test list_documents_by_run function."""

    def test_list_documents_by_run_returns_empty_for_no_documents(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_documents_by_run returns empty list when no documents."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        docs = list_documents_by_run(db_with_schema, run_id)

        assert docs == []

    def test_list_documents_by_run_returns_all_documents(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_documents_by_run returns all documents for a run."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        doc_id1 = create_document(
            db_with_schema,
            run_id=run_id,
            file_path="/path/to/doc1.txt",
            content_hash="abc123",
        )
        doc_id2 = create_document(
            db_with_schema,
            run_id=run_id,
            file_path="/path/to/doc2.txt",
            content_hash="def456",
        )

        docs = list_documents_by_run(db_with_schema, run_id)

        assert len(docs) == 2
        assert docs[0]["id"] == doc_id1
        assert docs[1]["id"] == doc_id2

    def test_list_documents_by_run_filters_by_run_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_documents_by_run filters by run_id."""
        run_id1 = create_run(db_with_schema, "/path/to/doc1.txt", "ollama", "llama3.2")
        run_id2 = create_run(db_with_schema, "/path/to/doc2.txt", "openai", "gpt-4")

        create_document(
            db_with_schema,
            run_id=run_id1,
            file_path="/path/to/doc1.txt",
            content_hash="abc123",
        )
        create_document(
            db_with_schema,
            run_id=run_id2,
            file_path="/path/to/doc2.txt",
            content_hash="def456",
        )

        docs = list_documents_by_run(db_with_schema, run_id1)

        assert len(docs) == 1
        assert docs[0]["run_id"] == run_id1


class TestGetDocumentByPath:
    """Test get_document_by_path function."""

    def test_get_document_by_path_returns_document(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document_by_path returns the correct document."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")
        doc_id = create_document(
            db_with_schema,
            run_id=run_id,
            file_path="/path/to/doc.txt",
            content_hash="abc123",
        )

        doc = get_document_by_path(db_with_schema, run_id, "/path/to/doc.txt")

        assert doc is not None
        assert doc["id"] == doc_id
        assert doc["file_path"] == "/path/to/doc.txt"

    def test_get_document_by_path_returns_none_for_nonexistent(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document_by_path returns None for non-existent path."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        doc = get_document_by_path(db_with_schema, run_id, "/nonexistent.txt")

        assert doc is None

    def test_get_document_by_path_filters_by_run_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document_by_path filters by run_id."""
        run_id1 = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")
        run_id2 = create_run(db_with_schema, "/path/to/doc.txt", "openai", "gpt-4")

        create_document(
            db_with_schema,
            run_id=run_id1,
            file_path="/path/to/doc.txt",
            content_hash="abc123",
        )
        create_document(
            db_with_schema,
            run_id=run_id2,
            file_path="/path/to/doc.txt",
            content_hash="def456",
        )

        doc = get_document_by_path(db_with_schema, run_id1, "/path/to/doc.txt")

        assert doc is not None
        assert doc["run_id"] == run_id1
        assert doc["content_hash"] == "abc123"
