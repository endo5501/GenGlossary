"""Tests for refined_repository module."""

import sqlite3

import pytest

from genglossary.db.refined_repository import (
    create_refined_term,
    create_refined_terms_batch,
    delete_all_refined,
    get_refined_term,
    list_all_refined,
    update_refined_term,
)
from genglossary.db.schema import initialize_db
from genglossary.models.term import TermOccurrence


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateRefinedTerm:
    """Test create_refined_term function."""

    def test_create_refined_term_returns_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_refined_term returns an ID."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_refined_term(
            db_with_schema,
            term_name="量子コンピュータ",
            definition="量子力学の原理を利用したコンピュータ",
            confidence=0.98,
            occurrences=occurrences,
        )

        assert isinstance(term_id, int)
        assert term_id > 0

    def test_create_refined_term_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_refined_term stores data correctly."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_refined_term(
            db_with_schema,
            term_name="量子コンピュータ",
            definition="量子力学の原理を利用したコンピュータ",
            confidence=0.98,
            occurrences=occurrences,
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM glossary_refined WHERE id = ?", (term_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["term_name"] == "量子コンピュータ"
        assert row["definition"] == "量子力学の原理を利用したコンピュータ"
        assert row["confidence"] == 0.98
        assert row["occurrences"] is not None

    def test_create_refined_term_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that term_name must be unique."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        create_refined_term(
            db_with_schema,
            term_name="量子コンピュータ",
            definition="定義1",
            confidence=0.98,
            occurrences=occurrences,
        )

        with pytest.raises(sqlite3.IntegrityError):
            create_refined_term(
                db_with_schema,
                term_name="量子コンピュータ",
                definition="定義2",
                confidence=0.95,
                occurrences=occurrences,
            )


class TestGetRefinedTerm:
    """Test get_refined_term function."""

    def test_get_refined_term_returns_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_refined_term returns data with deserialized occurrences."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_refined_term(
            db_with_schema,
            term_name="量子コンピュータ",
            definition="量子力学の原理を利用したコンピュータ",
            confidence=0.98,
            occurrences=occurrences,
        )

        term = get_refined_term(db_with_schema, term_id)

        assert term is not None
        assert term["term_name"] == "量子コンピュータ"
        assert len(term["occurrences"]) == 1
        assert isinstance(term["occurrences"][0], TermOccurrence)
        assert term["occurrences"][0].line_number == 1

    def test_get_refined_term_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_refined_term returns None for non-existent ID."""
        term = get_refined_term(db_with_schema, 999)

        assert term is None


class TestListAllRefined:
    """Test list_all_refined function."""

    def test_list_all_refined_returns_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns empty list when no terms."""
        terms = list_all_refined(db_with_schema)

        assert terms == []

    def test_list_all_refined_returns_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns all terms with deserialized occurrences."""
        occurrences1 = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context1"
            )
        ]
        occurrences2 = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=2, context="Context2"
            )
        ]

        create_refined_term(
            db_with_schema,
            term_name="量子コンピュータ",
            definition="定義1",
            confidence=0.98,
            occurrences=occurrences1,
        )
        create_refined_term(
            db_with_schema,
            term_name="量子ビット",
            definition="定義2",
            confidence=0.95,
            occurrences=occurrences2,
        )

        terms = list_all_refined(db_with_schema)

        assert len(terms) == 2
        assert all(isinstance(term["occurrences"][0], TermOccurrence) for term in terms)


class TestUpdateRefinedTerm:
    """Test update_refined_term function."""

    def test_update_refined_term_updates_definition_and_confidence(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_refined_term updates definition and confidence."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_refined_term(
            db_with_schema,
            term_name="量子コンピュータ",
            definition="古い定義",
            confidence=0.85,
            occurrences=occurrences,
        )

        update_refined_term(
            db_with_schema,
            term_id=term_id,
            definition="新しい定義",
            confidence=0.98,
        )

        term = get_refined_term(db_with_schema, term_id)
        assert term is not None
        assert term["definition"] == "新しい定義"
        assert term["confidence"] == 0.98
        assert term["term_name"] == "量子コンピュータ"

    def test_update_refined_term_with_nonexistent_id_raises_error(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_refined_term raises ValueError for non-existent ID."""
        with pytest.raises(
            ValueError, match="Term with id 999 not found in glossary_refined"
        ):
            update_refined_term(
                db_with_schema,
                term_id=999,
                definition="存在しない定義",
                confidence=0.5,
            )


class TestDeleteAllRefined:
    """Test delete_all_refined function."""

    def test_delete_all_refined_removes_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_refined removes all terms."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        create_refined_term(
            db_with_schema,
            term_name="量子コンピュータ",
            definition="定義1",
            confidence=0.98,
            occurrences=occurrences,
        )
        create_refined_term(
            db_with_schema,
            term_name="量子ビット",
            definition="定義2",
            confidence=0.95,
            occurrences=occurrences,
        )

        delete_all_refined(db_with_schema)

        terms = list_all_refined(db_with_schema)
        assert terms == []

    def test_delete_all_refined_on_empty_table_does_nothing(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_refined does nothing on empty table."""
        delete_all_refined(db_with_schema)

        terms = list_all_refined(db_with_schema)
        assert terms == []


class TestCreateRefinedTermsBatch:
    """Test create_refined_terms_batch function."""

    def test_create_refined_terms_batch_inserts_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_refined_terms_batch inserts all terms."""
        occ1 = [TermOccurrence(document_path="/doc1.txt", line_number=1, context="C1")]
        occ2 = [TermOccurrence(document_path="/doc2.txt", line_number=2, context="C2")]
        occ3 = [TermOccurrence(document_path="/doc3.txt", line_number=3, context="C3")]

        terms = [
            ("量子コンピュータ", "定義1", 0.98, occ1),
            ("量子ビット", "定義2", 0.95, occ2),
            ("重ね合わせ", "定義3", 0.90, occ3),
        ]

        create_refined_terms_batch(db_with_schema, terms)

        all_terms = list_all_refined(db_with_schema)
        assert len(all_terms) == 3
        term_names = [t["term_name"] for t in all_terms]
        assert "量子コンピュータ" in term_names
        assert "量子ビット" in term_names
        assert "重ね合わせ" in term_names

    def test_create_refined_terms_batch_stores_data_correctly(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_refined_terms_batch stores data correctly."""
        occ = [TermOccurrence(document_path="/doc.txt", line_number=1, context="Ctx")]

        terms = [
            ("量子コンピュータ", "量子力学を利用したコンピュータ", 0.98, occ),
        ]

        create_refined_terms_batch(db_with_schema, terms)

        term = get_refined_term(db_with_schema, 1)
        assert term is not None
        assert term["term_name"] == "量子コンピュータ"
        assert term["definition"] == "量子力学を利用したコンピュータ"
        assert term["confidence"] == 0.98
        assert len(term["occurrences"]) == 1

    def test_create_refined_terms_batch_with_empty_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_refined_terms_batch handles empty list."""
        create_refined_terms_batch(db_with_schema, [])

        all_terms = list_all_refined(db_with_schema)
        assert len(all_terms) == 0

    def test_create_refined_terms_batch_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_refined_terms_batch raises error on duplicate term_name."""
        import sqlite3 as sql

        occ = [TermOccurrence(document_path="/doc.txt", line_number=1, context="Ctx")]
        terms = [
            ("量子コンピュータ", "定義1", 0.98, occ),
            ("量子コンピュータ", "定義2", 0.95, occ),  # Duplicate
        ]

        with pytest.raises(sql.IntegrityError):
            create_refined_terms_batch(db_with_schema, terms)
