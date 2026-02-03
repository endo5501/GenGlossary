"""Tests for term_repository module."""

import sqlite3

import pytest

from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import (
    create_term,
    create_terms_batch,
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

    def test_list_all_terms_excludes_terms_in_excluded_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms excludes terms that are in excluded list."""
        from genglossary.db.excluded_term_repository import add_excluded_term

        # Create terms
        create_term(db_with_schema, term_text="量子コンピュータ", category="technical")
        create_term(db_with_schema, term_text="量子ビット", category="technical")
        create_term(db_with_schema, term_text="重ね合わせ", category="concept")

        # Add one term to excluded list
        add_excluded_term(db_with_schema, "量子ビット", "manual")

        # list_all_terms should exclude "量子ビット"
        terms = list_all_terms(db_with_schema)

        assert len(terms) == 2
        term_texts = [t["term_text"] for t in terms]
        assert "量子コンピュータ" in term_texts
        assert "重ね合わせ" in term_texts
        assert "量子ビット" not in term_texts

    def test_list_all_terms_returns_all_when_no_excluded_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms returns all terms when excluded list is empty."""
        # Create terms
        create_term(db_with_schema, term_text="量子コンピュータ", category="technical")
        create_term(db_with_schema, term_text="量子ビット", category="technical")

        # No excluded terms added

        terms = list_all_terms(db_with_schema)

        assert len(terms) == 2

    def test_list_all_terms_only_excludes_exact_match(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms only excludes exact text match, not partial."""
        from genglossary.db.excluded_term_repository import add_excluded_term

        # Create terms
        create_term(db_with_schema, term_text="量子コンピュータ", category="technical")
        create_term(db_with_schema, term_text="量子", category="technical")

        # Exclude only "量子" (not "量子コンピュータ")
        add_excluded_term(db_with_schema, "量子", "manual")

        terms = list_all_terms(db_with_schema)

        # "量子コンピュータ" should still be included
        assert len(terms) == 1
        assert terms[0]["term_text"] == "量子コンピュータ"


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


class TestCreateTermsBatch:
    """Test create_terms_batch function."""

    def test_create_terms_batch_inserts_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch inserts all terms."""
        terms = [
            ("量子コンピュータ", "technical_term"),
            ("量子ビット", "technical_term"),
            ("重ね合わせ", "concept"),
        ]

        create_terms_batch(db_with_schema, terms)

        all_terms = list_all_terms(db_with_schema)
        assert len(all_terms) == 3
        term_texts = [t["term_text"] for t in all_terms]
        assert "量子コンピュータ" in term_texts
        assert "量子ビット" in term_texts
        assert "重ね合わせ" in term_texts

    def test_create_terms_batch_stores_category(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch stores category correctly."""
        terms = [
            ("量子コンピュータ", "technical_term"),
            ("重ね合わせ", None),
        ]

        create_terms_batch(db_with_schema, terms)

        all_terms = list_all_terms(db_with_schema)
        term_map = {t["term_text"]: t["category"] for t in all_terms}
        assert term_map["量子コンピュータ"] == "technical_term"
        assert term_map["重ね合わせ"] is None

    def test_create_terms_batch_with_empty_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch handles empty list."""
        create_terms_batch(db_with_schema, [])

        all_terms = list_all_terms(db_with_schema)
        assert len(all_terms) == 0

    def test_create_terms_batch_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch raises error on duplicate term_text."""
        terms = [
            ("量子コンピュータ", "technical_term"),
            ("量子コンピュータ", "concept"),  # Duplicate
        ]

        with pytest.raises(sqlite3.IntegrityError):
            create_terms_batch(db_with_schema, terms)
