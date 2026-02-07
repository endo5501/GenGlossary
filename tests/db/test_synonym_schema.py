"""Tests for synonym group database schema."""

import sqlite3

import pytest

from genglossary.db.schema import initialize_db


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestSynonymGroupsTableExists:
    """Test that schema creates synonym tables."""

    def test_term_synonym_groups_table_exists(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='term_synonym_groups'"
        )
        assert cursor.fetchone() is not None

    def test_term_synonym_members_table_exists(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='term_synonym_members'"
        )
        assert cursor.fetchone() is not None


class TestSynonymGroupsTableColumns:
    """Test that synonym tables have expected columns."""

    def test_groups_has_expected_columns(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(term_synonym_groups)")
        columns = {row[1] for row in cursor.fetchall()}
        assert columns == {"id", "primary_term_text", "created_at"}

    def test_members_has_expected_columns(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(term_synonym_members)")
        columns = {row[1] for row in cursor.fetchall()}
        assert columns == {"id", "group_id", "term_text", "created_at"}


class TestSynonymMembersConstraints:
    """Test constraints on synonym member table."""

    def test_term_text_is_unique(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """A term can belong to at most one synonym group."""
        cursor = db_with_schema.cursor()
        cursor.execute(
            "INSERT INTO term_synonym_groups (primary_term_text) VALUES (?)",
            ("田中太郎",),
        )
        group_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO term_synonym_members (group_id, term_text) VALUES (?, ?)",
            (group_id, "田中"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO term_synonym_members (group_id, term_text) VALUES (?, ?)",
                (group_id, "田中"),
            )

    def test_foreign_key_cascade_delete(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Deleting a group should cascade delete its members."""
        cursor = db_with_schema.cursor()
        cursor.execute(
            "INSERT INTO term_synonym_groups (primary_term_text) VALUES (?)",
            ("田中太郎",),
        )
        group_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO term_synonym_members (group_id, term_text) VALUES (?, ?)",
            (group_id, "田中太郎"),
        )
        cursor.execute(
            "INSERT INTO term_synonym_members (group_id, term_text) VALUES (?, ?)",
            (group_id, "田中"),
        )

        cursor.execute(
            "DELETE FROM term_synonym_groups WHERE id = ?", (group_id,)
        )

        cursor.execute(
            "SELECT COUNT(*) FROM term_synonym_members WHERE group_id = ?",
            (group_id,),
        )
        assert cursor.fetchone()[0] == 0
