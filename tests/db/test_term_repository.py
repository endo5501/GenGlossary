"""Tests for term_repository module."""

import sqlite3

import pytest

from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import (
    create_term,
    delete_all_terms,
    delete_term,
    get_term,
    list_all_terms,
    update_term,
)


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateTerm:
    """Test create_term function."""

    def test_create_term_returns_term_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_term returns a term ID."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        assert isinstance(term_id, int)
        assert term_id > 0

    def test_create_term_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_term stores data correctly."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM terms_extracted WHERE id = ?", (term_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["term_text"] == "量子コンピュータ"
        assert row["category"] == "technical_term"

    def test_create_term_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that term_text must be unique."""
        create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        with pytest.raises(sqlite3.IntegrityError):
            create_term(
                db_with_schema,
                term_text="量子コンピュータ",
                category="technical_term",
            )


class TestGetTerm:
    """Test get_term function."""

    def test_get_term_returns_term_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_term returns term data."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        term = get_term(db_with_schema, term_id)

        assert term is not None
        assert term["id"] == term_id
        assert term["term_text"] == "量子コンピュータ"

    def test_get_term_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_term returns None for non-existent ID."""
        term = get_term(db_with_schema, 999)

        assert term is None


class TestListAllTerms:
    """Test list_all_terms function."""

    def test_list_all_terms_returns_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms returns empty list when no terms."""
        terms = list_all_terms(db_with_schema)

        assert terms == []

    def test_list_all_terms_returns_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms returns all terms."""
        create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )
        create_term(
            db_with_schema,
            term_text="量子ビット",
            category="technical_term",
        )

        terms = list_all_terms(db_with_schema)

        assert len(terms) == 2


class TestUpdateTerm:
    """Test update_term function."""

    def test_update_term_updates_text_and_category(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term updates term_text and category."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="量子計算機",
            category="updated_category",
        )

        term = get_term(db_with_schema, term_id)
        assert term is not None
        assert term["term_text"] == "量子計算機"
        assert term["category"] == "updated_category"

    def test_update_term_with_none_category_sets_null(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term sets category to NULL when None is provided."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="量子コンピュータ",
            category=None,
        )

        term = get_term(db_with_schema, term_id)
        assert term is not None
        assert term["category"] is None

    def test_update_term_with_nonexistent_id_raises_error(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term raises ValueError for non-existent term ID."""
        with pytest.raises(ValueError, match="Term with id 999 not found"):
            update_term(
                db_with_schema,
                term_id=999,
                term_text="存在しない用語",
                category="category",
            )


class TestDeleteTerm:
    """Test delete_term function."""

    def test_delete_term_removes_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_term removes the term."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        delete_term(db_with_schema, term_id)

        term = get_term(db_with_schema, term_id)
        assert term is None

    def test_delete_term_with_nonexistent_id_does_nothing(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_term does nothing for non-existent term ID."""
        delete_term(db_with_schema, 999)

        term = get_term(db_with_schema, 999)
        assert term is None

    def test_delete_term_removes_from_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that deleted term is removed from list_all_terms."""
        term_id_1 = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )
        term_id_2 = create_term(
            db_with_schema,
            term_text="量子ビット",
            category="technical_term",
        )

        delete_term(db_with_schema, term_id_1)

        terms = list_all_terms(db_with_schema)
        assert len(terms) == 1
        assert terms[0]["id"] == term_id_2


class TestDeleteAllTerms:
    """Test delete_all_terms function."""

    def test_delete_all_terms_removes_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_terms removes all terms."""
        create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )
        create_term(
            db_with_schema,
            term_text="量子ビット",
            category="technical_term",
        )

        assert len(list_all_terms(db_with_schema)) == 2

        delete_all_terms(db_with_schema)

        assert len(list_all_terms(db_with_schema)) == 0

    def test_delete_all_terms_does_not_fail_when_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_terms does not fail when table is empty."""
        delete_all_terms(db_with_schema)  # Should not raise

        assert len(list_all_terms(db_with_schema)) == 0
