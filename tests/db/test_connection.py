"""Tests for database connection management."""

import sqlite3
from pathlib import Path

import pytest

from genglossary.db.connection import get_connection, transaction


class TestGetConnection:
    """Test get_connection function."""

    def test_get_connection_with_in_memory_db(self) -> None:
        """Test creating an in-memory database connection."""
        conn = get_connection(":memory:")

        assert isinstance(conn, sqlite3.Connection)
        # Verify foreign keys are enabled
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1

        conn.close()

    def test_get_connection_with_file_path(self, temp_db_path: Path) -> None:
        """Test creating a file-based database connection."""
        conn = get_connection(str(temp_db_path))

        assert isinstance(conn, sqlite3.Connection)
        assert temp_db_path.exists()

        conn.close()

    def test_get_connection_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test that get_connection creates parent directories if needed."""
        db_path = tmp_path / "subdir" / "db" / "test.db"

        conn = get_connection(str(db_path))

        assert db_path.exists()
        assert db_path.parent.exists()

        conn.close()

    def test_connection_row_factory_is_row(self, temp_db_path: Path) -> None:
        """Test that connection uses Row factory for dict-like access."""
        conn = get_connection(str(temp_db_path))

        # Create a test table and insert data
        conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'test')")

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        row = cursor.fetchone()

        # Row factory allows both index and key access
        assert row[0] == 1
        assert row["id"] == 1
        assert row["name"] == "test"

        conn.close()

    def test_connection_can_be_used_as_context_manager(
        self, temp_db_path: Path
    ) -> None:
        """Test that connection can be used with 'with' statement."""
        with get_connection(str(temp_db_path)) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")

        # Verify data was committed
        conn = get_connection(str(temp_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        assert cursor.fetchone()[0] == 1
        conn.close()


class TestTransaction:
    """Test transaction context manager."""

    def test_transaction_commits_on_success(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that transaction commits changes on successful completion."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")

        with transaction(in_memory_db):
            in_memory_db.execute("INSERT INTO test VALUES (1, 'test')")

        # Verify data was committed
        cursor = in_memory_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        assert cursor.fetchone()[0] == 1

    def test_transaction_rollback_on_exception(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that transaction rolls back changes when exception occurs."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        in_memory_db.commit()

        with pytest.raises(ValueError):
            with transaction(in_memory_db):
                in_memory_db.execute("INSERT INTO test VALUES (1, 'test')")
                raise ValueError("Test error")

        # Verify data was rolled back
        cursor = in_memory_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        assert cursor.fetchone()[0] == 0

    def test_transaction_re_raises_exception(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that transaction re-raises the original exception."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER)")

        with pytest.raises(RuntimeError, match="Original error"):
            with transaction(in_memory_db):
                raise RuntimeError("Original error")

    def test_transaction_with_multiple_operations(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that transaction handles multiple operations atomically."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        in_memory_db.commit()

        with pytest.raises(ValueError):
            with transaction(in_memory_db):
                in_memory_db.execute("INSERT INTO test VALUES (1, 'first')")
                in_memory_db.execute("INSERT INTO test VALUES (2, 'second')")
                in_memory_db.execute("INSERT INTO test VALUES (3, 'third')")
                raise ValueError("Error after multiple inserts")

        # All operations should be rolled back
        cursor = in_memory_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        assert cursor.fetchone()[0] == 0
