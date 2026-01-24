"""Tests for metadata_repository module."""

import sqlite3

import pytest

from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.db.metadata_repository import (
    get_metadata,
    upsert_metadata,
    clear_metadata,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    """Create an in-memory database connection for testing."""
    connection = get_connection(":memory:")
    initialize_db(connection)
    yield connection
    connection.close()


class TestGetMetadata:
    """Tests for get_metadata function."""

    def test_returns_none_when_empty(self, conn: sqlite3.Connection) -> None:
        """Should return None when metadata table is empty."""
        result = get_metadata(conn)
        assert result is None

    def test_returns_metadata_when_exists(self, conn: sqlite3.Connection) -> None:
        """Should return metadata row when data exists."""
        # Insert metadata using upsert_metadata to ensure created_at is set
        upsert_metadata(conn, "./docs", "ollama", "llama3.2")

        result = get_metadata(conn)
        assert result is not None
        assert result["input_path"] == "./docs"
        assert result["llm_provider"] == "ollama"
        assert result["llm_model"] == "llama3.2"
        assert result["created_at"] is not None


class TestUpsertMetadata:
    """Tests for upsert_metadata function."""

    def test_inserts_when_empty(self, conn: sqlite3.Connection) -> None:
        """Should insert new metadata when table is empty."""
        upsert_metadata(conn, "./docs", "ollama", "llama3.2")

        result = get_metadata(conn)
        assert result is not None
        assert result["input_path"] == "./docs"
        assert result["llm_provider"] == "ollama"
        assert result["llm_model"] == "llama3.2"

    def test_updates_when_exists(self, conn: sqlite3.Connection) -> None:
        """Should update existing metadata."""
        # Insert initial data
        upsert_metadata(conn, "./docs", "ollama", "llama3.2")
        initial_result = get_metadata(conn)
        assert initial_result is not None
        initial_created_at = initial_result["created_at"]

        # Update
        upsert_metadata(conn, "./updated", "openai", "gpt-4")
        updated_result = get_metadata(conn)
        assert updated_result is not None
        assert updated_result["input_path"] == "./updated"
        assert updated_result["llm_provider"] == "openai"
        assert updated_result["llm_model"] == "gpt-4"
        # created_at should remain the same
        assert updated_result["created_at"] == initial_created_at

    def test_sets_created_at_on_insert(self, conn: sqlite3.Connection) -> None:
        """Should set created_at timestamp on initial insert."""
        upsert_metadata(conn, "./docs", "ollama", "llama3.2")

        result = get_metadata(conn)
        assert result is not None
        assert result["created_at"] is not None
        assert len(result["created_at"]) > 0


class TestClearMetadata:
    """Tests for clear_metadata function."""

    def test_deletes_metadata_record(self, conn: sqlite3.Connection) -> None:
        """Should delete metadata record."""
        # Insert metadata
        upsert_metadata(conn, "./docs", "ollama", "llama3.2")
        assert get_metadata(conn) is not None

        # Clear
        clear_metadata(conn)
        assert get_metadata(conn) is None

    def test_does_not_fail_when_empty(self, conn: sqlite3.Connection) -> None:
        """Should not fail when metadata is already empty."""
        clear_metadata(conn)  # Should not raise
        assert get_metadata(conn) is None
