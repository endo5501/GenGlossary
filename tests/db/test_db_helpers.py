"""Tests for db_helpers module."""

import sqlite3

import pytest

from genglossary.db.db_helpers import batch_insert


class TestBatchInsert:
    """Tests for batch_insert helper function."""

    @pytest.fixture
    def conn(self) -> sqlite3.Connection:
        """Create an in-memory database connection with a test table."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value INTEGER
            )
            """
        )
        return conn

    def test_batch_insert_inserts_all_rows(self, conn: sqlite3.Connection) -> None:
        """Test that batch_insert inserts all provided rows."""
        data = [
            ("item1", 10),
            ("item2", 20),
            ("item3", 30),
        ]

        batch_insert(conn, "test_table", ["name", "value"], data)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test_table ORDER BY id")
        rows = cursor.fetchall()

        assert len(rows) == 3
        assert rows[0]["name"] == "item1"
        assert rows[1]["name"] == "item2"
        assert rows[2]["name"] == "item3"

    def test_batch_insert_with_empty_list_does_nothing(
        self, conn: sqlite3.Connection
    ) -> None:
        """Test that batch_insert does nothing when given an empty list."""
        batch_insert(conn, "test_table", ["name", "value"], [])

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM test_table")
        row = cursor.fetchone()
        assert row["count"] == 0

    def test_batch_insert_stores_values_correctly(
        self, conn: sqlite3.Connection
    ) -> None:
        """Test that batch_insert stores all values correctly."""
        data = [
            ("alpha", 100),
            ("beta", None),
        ]

        batch_insert(conn, "test_table", ["name", "value"], data)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test_table ORDER BY id")
        rows = cursor.fetchall()

        assert rows[0]["name"] == "alpha"
        assert rows[0]["value"] == 100
        assert rows[1]["name"] == "beta"
        assert rows[1]["value"] is None

    def test_batch_insert_with_single_column(self, conn: sqlite3.Connection) -> None:
        """Test batch_insert with a single column."""
        # Create a simpler table
        conn.execute(
            """
            CREATE TABLE single_col (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
            """
        )
        data = [("only_name",), ("another",)]

        batch_insert(conn, "single_col", ["name"], data)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM single_col ORDER BY id")
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert rows[0]["name"] == "only_name"
        assert rows[1]["name"] == "another"

    def test_batch_insert_with_many_columns(self, conn: sqlite3.Connection) -> None:
        """Test batch_insert with many columns."""
        conn.execute(
            """
            CREATE TABLE multi_col (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                col1 TEXT,
                col2 TEXT,
                col3 TEXT,
                col4 INTEGER
            )
            """
        )
        data = [
            ("a", "b", "c", 1),
            ("d", "e", "f", 2),
        ]

        batch_insert(conn, "multi_col", ["col1", "col2", "col3", "col4"], data)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM multi_col ORDER BY id")
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert rows[0]["col1"] == "a"
        assert rows[0]["col4"] == 1
        assert rows[1]["col3"] == "f"

    def test_batch_insert_raises_on_integrity_error(
        self, conn: sqlite3.Connection
    ) -> None:
        """Test that batch_insert raises IntegrityError on constraint violation."""
        conn.execute(
            """
            CREATE TABLE unique_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )

        # Insert first item
        batch_insert(conn, "unique_table", ["name"], [("duplicate",)])

        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            batch_insert(conn, "unique_table", ["name"], [("duplicate",)])
