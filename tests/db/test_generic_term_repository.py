"""Tests for generic term repository functions."""

import sqlite3

import pytest
from pydantic import BaseModel

from genglossary.db.generic_term_repository import (
    add_term,
    bulk_add_terms,
    delete_term,
    get_all_terms,
    get_term_by_id,
    get_term_texts,
    term_exists,
)
from genglossary.db.schema import initialize_db
from genglossary.models.excluded_term import ExcludedTerm
from genglossary.models.required_term import RequiredTerm


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestAddTerm:
    """Test generic add_term function."""

    def test_add_term_to_excluded_returns_id_and_created(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        term_id, created = add_term(
            db_with_schema, "量子コンピュータ", "auto", "terms_excluded", ExcludedTerm
        )
        assert isinstance(term_id, int)
        assert term_id > 0
        assert created is True

    def test_add_term_to_required_returns_id_and_created(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        term_id, created = add_term(
            db_with_schema, "量子コンピュータ", "manual", "terms_required", RequiredTerm
        )
        assert isinstance(term_id, int)
        assert term_id > 0
        assert created is True

    def test_add_duplicate_term_returns_existing_id_with_false(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        term_id_1, created_1 = add_term(
            db_with_schema, "量子コンピュータ", "auto", "terms_excluded", ExcludedTerm
        )
        term_id_2, created_2 = add_term(
            db_with_schema, "量子コンピュータ", "manual", "terms_excluded", ExcludedTerm
        )
        assert term_id_1 == term_id_2
        assert created_1 is True
        assert created_2 is False


class TestDeleteTerm:
    """Test generic delete_term function."""

    def test_delete_existing_term_returns_true(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        term_id, _ = add_term(
            db_with_schema, "量子コンピュータ", "auto", "terms_excluded", ExcludedTerm
        )
        assert delete_term(db_with_schema, term_id, "terms_excluded") is True

    def test_delete_nonexistent_term_returns_false(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        assert delete_term(db_with_schema, 999, "terms_excluded") is False


class TestGetAllTerms:
    """Test generic get_all_terms function."""

    def test_returns_empty_list_when_no_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        terms = get_all_terms(db_with_schema, "terms_excluded", ExcludedTerm)
        assert terms == []

    def test_returns_all_terms_as_correct_model(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        add_term(db_with_schema, "用語1", "auto", "terms_excluded", ExcludedTerm)
        add_term(db_with_schema, "用語2", "manual", "terms_excluded", ExcludedTerm)

        terms = get_all_terms(db_with_schema, "terms_excluded", ExcludedTerm)

        assert len(terms) == 2
        assert all(isinstance(t, ExcludedTerm) for t in terms)
        assert {t.term_text for t in terms} == {"用語1", "用語2"}

    def test_works_with_required_term_model(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        add_term(db_with_schema, "用語1", "manual", "terms_required", RequiredTerm)

        terms = get_all_terms(db_with_schema, "terms_required", RequiredTerm)

        assert len(terms) == 1
        assert isinstance(terms[0], RequiredTerm)


class TestGetTermById:
    """Test generic get_term_by_id function."""

    def test_returns_term_when_exists(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        term_id, _ = add_term(
            db_with_schema, "量子コンピュータ", "manual", "terms_required", RequiredTerm
        )

        term = get_term_by_id(db_with_schema, term_id, "terms_required", RequiredTerm)

        assert term is not None
        assert term.id == term_id
        assert term.term_text == "量子コンピュータ"

    def test_returns_none_when_not_exists(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        term = get_term_by_id(db_with_schema, 999, "terms_excluded", ExcludedTerm)
        assert term is None


class TestTermExists:
    """Test generic term_exists function."""

    def test_returns_true_for_existing_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        add_term(db_with_schema, "量子コンピュータ", "auto", "terms_excluded", ExcludedTerm)
        assert term_exists(db_with_schema, "量子コンピュータ", "terms_excluded") is True

    def test_returns_false_for_nonexistent_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        assert term_exists(db_with_schema, "存在しない用語", "terms_excluded") is False


class TestGetTermTexts:
    """Test generic get_term_texts function."""

    def test_returns_empty_set_when_no_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        assert get_term_texts(db_with_schema, "terms_excluded") == set()

    def test_returns_set_of_term_texts(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        add_term(db_with_schema, "用語1", "auto", "terms_excluded", ExcludedTerm)
        add_term(db_with_schema, "用語2", "manual", "terms_excluded", ExcludedTerm)

        texts = get_term_texts(db_with_schema, "terms_excluded")
        assert texts == {"用語1", "用語2"}


class TestAddTermNoneRowGuard:
    """Test add_term raises RuntimeError when row lookup fails."""

    def test_add_term_raises_runtime_error_when_row_not_found(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """When INSERT does nothing and SELECT returns None, raise RuntimeError."""
        from unittest.mock import MagicMock, patch

        mock_cursor = MagicMock()
        # INSERT does nothing (conflict)
        mock_cursor.lastrowid = 0
        mock_cursor.rowcount = 0
        # SELECT returns None (unexpected)
        mock_cursor.fetchone.return_value = None

        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_conn.cursor.return_value = mock_cursor

        with pytest.raises(RuntimeError, match="terms_excluded.*テスト用語"):
            add_term(mock_conn, "テスト用語", "auto", "terms_excluded", ExcludedTerm)


class TestBulkAddTerms:
    """Test generic bulk_add_terms function."""

    def test_bulk_add_inserts_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        count = bulk_add_terms(
            db_with_schema, ["用語1", "用語2", "用語3"], "auto", "terms_excluded"
        )
        assert count == 3
        assert get_term_texts(db_with_schema, "terms_excluded") == {"用語1", "用語2", "用語3"}

    def test_bulk_add_skips_existing_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        add_term(db_with_schema, "用語1", "manual", "terms_excluded", ExcludedTerm)
        count = bulk_add_terms(
            db_with_schema, ["用語1", "用語2"], "auto", "terms_excluded"
        )
        assert count == 1

    def test_bulk_add_with_empty_list_returns_zero(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        count = bulk_add_terms(db_with_schema, [], "auto", "terms_excluded")
        assert count == 0

    def test_bulk_add_normalizes_whitespace(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        count = bulk_add_terms(
            db_with_schema, ["  用語1  ", "\t用語2\n"], "auto", "terms_excluded"
        )
        assert count == 2
        assert get_term_texts(db_with_schema, "terms_excluded") == {"用語1", "用語2"}

    def test_bulk_add_skips_empty_strings(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        count = bulk_add_terms(
            db_with_schema, ["用語1", "", "  ", "用語2"], "auto", "terms_excluded"
        )
        assert count == 2

    def test_bulk_add_deduplicates_after_normalization(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        count = bulk_add_terms(
            db_with_schema, ["用語1", "  用語1  ", "用語1"], "auto", "terms_excluded"
        )
        assert count == 1
