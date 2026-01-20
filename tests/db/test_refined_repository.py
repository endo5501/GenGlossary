"""Tests for refined_repository module."""

import sqlite3

import pytest

from genglossary.db.refined_repository import (
    create_refined_term,
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
