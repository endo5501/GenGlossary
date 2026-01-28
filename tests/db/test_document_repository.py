"""Tests for document_repository module."""

import sqlite3

import pytest

from genglossary.db.document_repository import (
    create_document,
    get_document,
    get_document_by_name,
    list_all_documents,
)
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
        doc_id = create_document(
            db_with_schema,
            file_name="doc.txt",
            content="Hello World",
            content_hash="abc123",
        )

        assert isinstance(doc_id, int)
        assert doc_id > 0

    def test_create_document_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_document stores data correctly."""
        test_content = "# Test Document\n\nThis is content."
        doc_id = create_document(
            db_with_schema,
            file_name="doc.txt",
            content=test_content,
            content_hash="abc123",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["file_name"] == "doc.txt"
        assert row["content"] == test_content
        assert row["content_hash"] == "abc123"

    def test_create_document_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that file_name must be unique."""
        # Create first document
        create_document(
            db_with_schema,
            file_name="doc.txt",
            content="Content 1",
            content_hash="abc123",
        )

        # Try to create duplicate
        with pytest.raises(sqlite3.IntegrityError):
            create_document(
                db_with_schema,
                file_name="doc.txt",
                content="Content 2",
                content_hash="def456",
            )


class TestGetDocument:
    """Test get_document function."""

    def test_get_document_returns_document_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document returns document data."""
        test_content = "Test content"
        doc_id = create_document(
            db_with_schema,
            file_name="doc.txt",
            content=test_content,
            content_hash="abc123",
        )

        doc = get_document(db_with_schema, doc_id)

        assert doc is not None
        assert doc["id"] == doc_id
        assert doc["file_name"] == "doc.txt"
        assert doc["content"] == test_content
        assert doc["content_hash"] == "abc123"

    def test_get_document_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document returns None for non-existent ID."""
        doc = get_document(db_with_schema, 999)

        assert doc is None


class TestListAllDocuments:
    """Test list_all_documents function."""

    def test_list_all_documents_returns_empty_for_no_documents(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_documents returns empty list when no documents."""
        docs = list_all_documents(db_with_schema)

        assert docs == []

    def test_list_all_documents_returns_all_documents(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_documents returns all documents."""
        doc_id1 = create_document(
            db_with_schema,
            file_name="doc1.txt",
            content="Content 1",
            content_hash="abc123",
        )
        doc_id2 = create_document(
            db_with_schema,
            file_name="doc2.txt",
            content="Content 2",
            content_hash="def456",
        )

        docs = list_all_documents(db_with_schema)

        assert len(docs) == 2
        assert docs[0]["id"] == doc_id1
        assert docs[1]["id"] == doc_id2

    def test_list_all_documents_ordered_by_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_documents returns documents ordered by id."""
        create_document(
            db_with_schema,
            file_name="doc1.txt",
            content="Content 1",
            content_hash="abc123",
        )
        create_document(
            db_with_schema,
            file_name="doc2.txt",
            content="Content 2",
            content_hash="def456",
        )

        docs = list_all_documents(db_with_schema)

        assert docs[0]["id"] < docs[1]["id"]


class TestGetDocumentByName:
    """Test get_document_by_name function."""

    def test_get_document_by_name_returns_document(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document_by_name returns the correct document."""
        test_content = "Test content"
        doc_id = create_document(
            db_with_schema,
            file_name="doc.txt",
            content=test_content,
            content_hash="abc123",
        )

        doc = get_document_by_name(db_with_schema, "doc.txt")

        assert doc is not None
        assert doc["id"] == doc_id
        assert doc["file_name"] == "doc.txt"
        assert doc["content"] == test_content

    def test_get_document_by_name_returns_none_for_nonexistent(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document_by_name returns None for non-existent name."""
        doc = get_document_by_name(db_with_schema, "nonexistent.txt")

        assert doc is None
