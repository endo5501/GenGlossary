"""Tests for required_term_repository module."""

import sqlite3

import pytest

from genglossary.db.required_term_repository import (
    add_required_term,
    bulk_add_required_terms,
    delete_required_term,
    get_all_required_terms,
    get_required_term_by_id,
    get_required_term_texts,
    term_exists_in_required,
)
from genglossary.db.schema import initialize_db


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestSchemaCreatesRequiredTermsTable:
    """Test that schema creates terms_required table."""

    def test_terms_required_table_exists(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that terms_required table is created by schema initialization."""
        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='terms_required'"
        )
        assert cursor.fetchone() is not None

    def test_terms_required_has_expected_columns(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that terms_required table has the expected columns."""
        cursor = db_with_schema.cursor()
        cursor.execute("PRAGMA table_info(terms_required)")
        columns = {row[1] for row in cursor.fetchall()}
        assert columns == {"id", "term_text", "source", "created_at"}

    def test_terms_required_term_text_is_unique(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that term_text has a UNIQUE constraint."""
        cursor = db_with_schema.cursor()
        cursor.execute(
            "INSERT INTO terms_required (term_text, source) VALUES (?, ?)",
            ("テスト用語", "manual"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO terms_required (term_text, source) VALUES (?, ?)",
                ("テスト用語", "manual"),
            )


class TestAddRequiredTerm:
    """Test add_required_term function."""

    def test_add_required_term_returns_id_and_created_flag(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that add_required_term returns tuple of (term_id, created)."""
        term_id, created = add_required_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="manual",
        )

        assert isinstance(term_id, int)
        assert term_id > 0
        assert created is True

    def test_add_required_term_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that add_required_term stores data correctly."""
        term_id, _ = add_required_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="manual",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM terms_required WHERE id = ?", (term_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["term_text"] == "量子コンピュータ"
        assert row["source"] == "manual"
        assert row["created_at"] is not None

    def test_add_existing_term_returns_existing_id_with_false_flag(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that adding an existing term returns its ID with created=False."""
        term_id_1, created_1 = add_required_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="manual",
        )

        term_id_2, created_2 = add_required_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="manual",
        )

        assert term_id_1 == term_id_2
        assert created_1 is True
        assert created_2 is False


class TestGetRequiredTermById:
    """Test get_required_term_by_id function."""

    def test_returns_term_when_exists(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_required_term_by_id returns the term when it exists."""
        term_id, _ = add_required_term(db_with_schema, "量子コンピュータ", "manual")

        term = get_required_term_by_id(db_with_schema, term_id)

        assert term is not None
        assert term.id == term_id
        assert term.term_text == "量子コンピュータ"
        assert term.source == "manual"
        assert term.created_at is not None

    def test_returns_none_when_not_exists(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_required_term_by_id returns None for non-existent ID."""
        term = get_required_term_by_id(db_with_schema, 999)

        assert term is None


class TestDeleteRequiredTerm:
    """Test delete_required_term function."""

    def test_delete_required_term_removes_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_required_term removes the term."""
        term_id, _ = add_required_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="manual",
        )

        result = delete_required_term(db_with_schema, term_id)

        assert result is True
        assert not term_exists_in_required(db_with_schema, "量子コンピュータ")

    def test_delete_nonexistent_term_returns_false(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that deleting non-existent term returns False."""
        result = delete_required_term(db_with_schema, 999)

        assert result is False


class TestGetAllRequiredTerms:
    """Test get_all_required_terms function."""

    def test_get_all_returns_empty_list_when_no_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_all_required_terms returns empty list when no terms."""
        terms = get_all_required_terms(db_with_schema)

        assert terms == []

    def test_get_all_returns_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_all_required_terms returns all terms."""
        add_required_term(db_with_schema, "用語1", "manual")
        add_required_term(db_with_schema, "用語2", "manual")

        terms = get_all_required_terms(db_with_schema)

        assert len(terms) == 2
        term_texts = [t.term_text for t in terms]
        assert "用語1" in term_texts
        assert "用語2" in term_texts

    def test_get_all_returns_required_term_models(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_all_required_terms returns RequiredTerm models."""
        add_required_term(db_with_schema, "用語1", "manual")

        terms = get_all_required_terms(db_with_schema)

        assert len(terms) == 1
        term = terms[0]
        assert term.id is not None
        assert term.term_text == "用語1"
        assert term.source == "manual"
        assert term.created_at is not None


class TestTermExistsInRequired:
    """Test term_exists_in_required function."""

    def test_exists_returns_true_for_existing_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that exists returns True for existing term."""
        add_required_term(db_with_schema, "量子コンピュータ", "manual")

        assert term_exists_in_required(db_with_schema, "量子コンピュータ") is True

    def test_exists_returns_false_for_nonexistent_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that exists returns False for non-existent term."""
        assert term_exists_in_required(db_with_schema, "存在しない用語") is False


class TestGetRequiredTermTexts:
    """Test get_required_term_texts function."""

    def test_returns_empty_set_when_no_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that returns empty set when no required terms."""
        texts = get_required_term_texts(db_with_schema)

        assert texts == set()

    def test_returns_set_of_term_texts(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that returns set of all required term texts."""
        add_required_term(db_with_schema, "用語1", "manual")
        add_required_term(db_with_schema, "用語2", "manual")
        add_required_term(db_with_schema, "用語3", "manual")

        texts = get_required_term_texts(db_with_schema)

        assert texts == {"用語1", "用語2", "用語3"}


class TestBulkAddRequiredTerms:
    """Test bulk_add_required_terms function."""

    def test_bulk_add_inserts_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add inserts all terms."""
        terms = ["用語1", "用語2", "用語3"]

        count = bulk_add_required_terms(db_with_schema, terms, "manual")

        assert count == 3
        texts = get_required_term_texts(db_with_schema)
        assert texts == {"用語1", "用語2", "用語3"}

    def test_bulk_add_skips_existing_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add skips already existing terms."""
        add_required_term(db_with_schema, "用語1", "manual")

        terms = ["用語1", "用語2", "用語3"]
        count = bulk_add_required_terms(db_with_schema, terms, "manual")

        assert count == 2

    def test_bulk_add_with_empty_list_returns_zero(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add with empty list returns 0."""
        count = bulk_add_required_terms(db_with_schema, [], "manual")

        assert count == 0

    def test_bulk_add_normalizes_whitespace(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add strips leading/trailing whitespace."""
        terms = ["  用語1  ", "\t用語2\n", "用語3"]

        count = bulk_add_required_terms(db_with_schema, terms, "manual")

        assert count == 3
        texts = get_required_term_texts(db_with_schema)
        assert texts == {"用語1", "用語2", "用語3"}

    def test_bulk_add_skips_empty_strings(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add skips empty strings and whitespace-only strings."""
        terms = ["用語1", "", "  ", "用語2", "\t\n"]

        count = bulk_add_required_terms(db_with_schema, terms, "manual")

        assert count == 2
        texts = get_required_term_texts(db_with_schema)
        assert texts == {"用語1", "用語2"}

    def test_bulk_add_deduplicates_after_normalization(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add handles duplicates that appear after normalization."""
        terms = ["用語1", "  用語1  ", "用語1"]

        count = bulk_add_required_terms(db_with_schema, terms, "manual")

        assert count == 1
        texts = get_required_term_texts(db_with_schema)
        assert texts == {"用語1"}
