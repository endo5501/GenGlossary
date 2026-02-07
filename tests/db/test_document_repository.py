"""Tests for document_repository module."""

import sqlite3

import pytest

from genglossary.db.document_repository import (
    create_document,
    create_documents_batch,
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

    def test_create_document_returns_row(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_document returns a sqlite3.Row with all fields."""
        row = create_document(
            db_with_schema,
            file_name="doc.txt",
            content="Hello World",
            content_hash="abc123",
        )

        assert isinstance(row, sqlite3.Row)
        assert row["id"] > 0
        assert row["file_name"] == "doc.txt"
        assert row["content"] == "Hello World"
        assert row["content_hash"] == "abc123"

    def test_create_document_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_document stores data correctly."""
        test_content = "# Test Document\n\nThis is content."
        row = create_document(
            db_with_schema,
            file_name="doc.txt",
            content=test_content,
            content_hash="abc123",
        )

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
        created = create_document(
            db_with_schema,
            file_name="doc.txt",
            content=test_content,
            content_hash="abc123",
        )

        doc = get_document(db_with_schema, created["id"])

        assert doc is not None
        assert doc["id"] == created["id"]
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
        created1 = create_document(
            db_with_schema,
            file_name="doc1.txt",
            content="Content 1",
            content_hash="abc123",
        )
        created2 = create_document(
            db_with_schema,
            file_name="doc2.txt",
            content="Content 2",
            content_hash="def456",
        )

        docs = list_all_documents(db_with_schema)

        assert len(docs) == 2
        assert docs[0]["id"] == created1["id"]
        assert docs[1]["id"] == created2["id"]

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
        created = create_document(
            db_with_schema,
            file_name="doc.txt",
            content=test_content,
            content_hash="abc123",
        )

        doc = get_document_by_name(db_with_schema, "doc.txt")

        assert doc is not None
        assert doc["id"] == created["id"]
        assert doc["file_name"] == "doc.txt"
        assert doc["content"] == test_content

    def test_get_document_by_name_returns_none_for_nonexistent(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_document_by_name returns None for non-existent name."""
        doc = get_document_by_name(db_with_schema, "nonexistent.txt")

        assert doc is None


class TestCreateDocumentsBatch:
    """Test create_documents_batch function."""

    def test_create_documents_batch_inserts_all_documents(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_documents_batch inserts all documents."""
        documents = [
            ("doc1.txt", "Content 1", "hash1"),
            ("doc2.txt", "Content 2", "hash2"),
            ("doc3.txt", "Content 3", "hash3"),
        ]

        create_documents_batch(db_with_schema, documents)

        all_docs = list_all_documents(db_with_schema)
        assert len(all_docs) == 3
        file_names = [d["file_name"] for d in all_docs]
        assert "doc1.txt" in file_names
        assert "doc2.txt" in file_names
        assert "doc3.txt" in file_names

    def test_create_documents_batch_stores_content_and_hash(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_documents_batch stores content and hash correctly."""
        documents = [
            ("doc1.txt", "Content 1", "hash1"),
        ]

        create_documents_batch(db_with_schema, documents)

        doc = get_document_by_name(db_with_schema, "doc1.txt")
        assert doc is not None
        assert doc["content"] == "Content 1"
        assert doc["content_hash"] == "hash1"

    def test_create_documents_batch_with_empty_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_documents_batch handles empty list."""
        create_documents_batch(db_with_schema, [])

        all_docs = list_all_documents(db_with_schema)
        assert len(all_docs) == 0

    def test_create_documents_batch_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_documents_batch raises error on duplicate file_name."""
        import sqlite3 as sql

        documents = [
            ("doc1.txt", "Content 1", "hash1"),
            ("doc1.txt", "Content 2", "hash2"),  # Duplicate
        ]

        with pytest.raises(sql.IntegrityError):
            create_documents_batch(db_with_schema, documents)
