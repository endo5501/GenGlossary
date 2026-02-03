"""Tests for excluded_term_repository module."""

import sqlite3

import pytest

from genglossary.db.excluded_term_repository import (
    add_excluded_term,
    bulk_add_excluded_terms,
    delete_excluded_term,
    get_all_excluded_terms,
    get_excluded_term_texts,
    term_exists_in_excluded,
)
from genglossary.db.schema import initialize_db


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestAddExcludedTerm:
    """Test add_excluded_term function."""

    def test_add_excluded_term_returns_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that add_excluded_term returns the term ID."""
        term_id = add_excluded_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="auto",
        )

        assert isinstance(term_id, int)
        assert term_id > 0

    def test_add_excluded_term_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that add_excluded_term stores data correctly."""
        term_id = add_excluded_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="manual",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM terms_excluded WHERE id = ?", (term_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["term_text"] == "量子コンピュータ"
        assert row["source"] == "manual"
        assert row["created_at"] is not None

    def test_add_existing_term_returns_existing_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that adding an existing term returns its ID without error."""
        term_id_1 = add_excluded_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="auto",
        )

        # Adding the same term should return the existing ID
        term_id_2 = add_excluded_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="manual",  # source is different, but term exists
        )

        assert term_id_1 == term_id_2


class TestDeleteExcludedTerm:
    """Test delete_excluded_term function."""

    def test_delete_excluded_term_removes_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_excluded_term removes the term."""
        term_id = add_excluded_term(
            db_with_schema,
            term_text="量子コンピュータ",
            source="auto",
        )

        result = delete_excluded_term(db_with_schema, term_id)

        assert result is True
        assert not term_exists_in_excluded(db_with_schema, "量子コンピュータ")

    def test_delete_nonexistent_term_returns_false(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that deleting non-existent term returns False."""
        result = delete_excluded_term(db_with_schema, 999)

        assert result is False


class TestGetAllExcludedTerms:
    """Test get_all_excluded_terms function."""

    def test_get_all_returns_empty_list_when_no_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_all_excluded_terms returns empty list when no terms."""
        terms = get_all_excluded_terms(db_with_schema)

        assert terms == []

    def test_get_all_returns_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_all_excluded_terms returns all terms."""
        add_excluded_term(db_with_schema, "用語1", "auto")
        add_excluded_term(db_with_schema, "用語2", "manual")

        terms = get_all_excluded_terms(db_with_schema)

        assert len(terms) == 2
        term_texts = [t.term_text for t in terms]
        assert "用語1" in term_texts
        assert "用語2" in term_texts

    def test_get_all_returns_excluded_term_models(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_all_excluded_terms returns ExcludedTerm models."""
        add_excluded_term(db_with_schema, "用語1", "auto")

        terms = get_all_excluded_terms(db_with_schema)

        assert len(terms) == 1
        term = terms[0]
        assert term.id is not None
        assert term.term_text == "用語1"
        assert term.source == "auto"
        assert term.created_at is not None


class TestTermExistsInExcluded:
    """Test term_exists_in_excluded function."""

    def test_exists_returns_true_for_existing_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that exists returns True for existing term."""
        add_excluded_term(db_with_schema, "量子コンピュータ", "auto")

        assert term_exists_in_excluded(db_with_schema, "量子コンピュータ") is True

    def test_exists_returns_false_for_nonexistent_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that exists returns False for non-existent term."""
        assert term_exists_in_excluded(db_with_schema, "存在しない用語") is False


class TestGetExcludedTermTexts:
    """Test get_excluded_term_texts function."""

    def test_returns_empty_set_when_no_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that returns empty set when no excluded terms."""
        texts = get_excluded_term_texts(db_with_schema)

        assert texts == set()

    def test_returns_set_of_term_texts(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that returns set of all excluded term texts."""
        add_excluded_term(db_with_schema, "用語1", "auto")
        add_excluded_term(db_with_schema, "用語2", "manual")
        add_excluded_term(db_with_schema, "用語3", "auto")

        texts = get_excluded_term_texts(db_with_schema)

        assert texts == {"用語1", "用語2", "用語3"}


class TestBulkAddExcludedTerms:
    """Test bulk_add_excluded_terms function."""

    def test_bulk_add_inserts_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add inserts all terms."""
        terms = ["用語1", "用語2", "用語3"]

        count = bulk_add_excluded_terms(db_with_schema, terms, "auto")

        assert count == 3
        texts = get_excluded_term_texts(db_with_schema)
        assert texts == {"用語1", "用語2", "用語3"}

    def test_bulk_add_skips_existing_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add skips already existing terms."""
        add_excluded_term(db_with_schema, "用語1", "manual")

        terms = ["用語1", "用語2", "用語3"]
        count = bulk_add_excluded_terms(db_with_schema, terms, "auto")

        # Only 2 new terms should be added
        assert count == 2

    def test_bulk_add_with_empty_list_returns_zero(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add with empty list returns 0."""
        count = bulk_add_excluded_terms(db_with_schema, [], "auto")

        assert count == 0

    def test_bulk_add_sets_correct_source(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that bulk_add sets the correct source for all terms."""
        terms = ["用語1", "用語2"]
        bulk_add_excluded_terms(db_with_schema, terms, "auto")

        all_terms = get_all_excluded_terms(db_with_schema)
        for term in all_terms:
            assert term.source == "auto"
