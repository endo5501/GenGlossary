"""Tests for provisional_repository module."""

import sqlite3

import pytest

from genglossary.db.provisional_repository import (
    create_provisional_term,
    get_provisional_term,
    list_provisional_terms_by_run,
    update_provisional_term,
)
from genglossary.db.run_repository import create_run
from genglossary.db.schema import initialize_db
from genglossary.models.term import TermOccurrence


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateProvisionalTerm:
    """Test create_provisional_term function."""

    def test_create_provisional_term_returns_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_provisional_term returns an ID."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_provisional_term(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            definition="量子力学の原理を利用したコンピュータ",
            confidence=0.95,
            occurrences=occurrences,
        )

        assert isinstance(term_id, int)
        assert term_id > 0

    def test_create_provisional_term_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_provisional_term stores data correctly."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_provisional_term(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            definition="量子力学の原理を利用したコンピュータ",
            confidence=0.95,
            occurrences=occurrences,
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM glossary_provisional WHERE id = ?", (term_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["run_id"] == run_id
        assert row["term_name"] == "量子コンピュータ"
        assert row["definition"] == "量子力学の原理を利用したコンピュータ"
        assert row["confidence"] == 0.95
        assert row["occurrences"] is not None

    def test_create_provisional_term_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that (run_id, term_name) must be unique."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        create_provisional_term(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            definition="定義1",
            confidence=0.95,
            occurrences=occurrences,
        )

        with pytest.raises(sqlite3.IntegrityError):
            create_provisional_term(
                db_with_schema,
                run_id=run_id,
                term_name="量子コンピュータ",
                definition="定義2",
                confidence=0.90,
                occurrences=occurrences,
            )


class TestGetProvisionalTerm:
    """Test get_provisional_term function."""

    def test_get_provisional_term_returns_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_provisional_term returns data with deserialized occurrences."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_provisional_term(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            definition="量子力学の原理を利用したコンピュータ",
            confidence=0.95,
            occurrences=occurrences,
        )

        term = get_provisional_term(db_with_schema, term_id)

        assert term is not None
        assert term["term_name"] == "量子コンピュータ"
        assert len(term["occurrences"]) == 1
        assert isinstance(term["occurrences"][0], TermOccurrence)
        assert term["occurrences"][0].line_number == 1

    def test_get_provisional_term_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_provisional_term returns None for non-existent ID."""
        term = get_provisional_term(db_with_schema, 999)

        assert term is None


class TestListProvisionalTermsByRun:
    """Test list_provisional_terms_by_run function."""

    def test_list_provisional_terms_by_run_returns_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns empty list when no terms."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        terms = list_provisional_terms_by_run(db_with_schema, run_id)

        assert terms == []

    def test_list_provisional_terms_by_run_returns_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns all terms with deserialized occurrences."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

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

        create_provisional_term(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            definition="定義1",
            confidence=0.95,
            occurrences=occurrences1,
        )
        create_provisional_term(
            db_with_schema,
            run_id=run_id,
            term_name="量子ビット",
            definition="定義2",
            confidence=0.90,
            occurrences=occurrences2,
        )

        terms = list_provisional_terms_by_run(db_with_schema, run_id)

        assert len(terms) == 2
        assert all(isinstance(term["occurrences"][0], TermOccurrence) for term in terms)


class TestUpdateProvisionalTerm:
    """Test update_provisional_term function."""

    def test_update_provisional_term_updates_definition_and_confidence(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_provisional_term updates definition and confidence."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="Context"
            )
        ]

        term_id = create_provisional_term(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            definition="古い定義",
            confidence=0.80,
            occurrences=occurrences,
        )

        update_provisional_term(
            db_with_schema,
            term_id=term_id,
            definition="新しい定義",
            confidence=0.95,
        )

        term = get_provisional_term(db_with_schema, term_id)
        assert term is not None
        assert term["definition"] == "新しい定義"
        assert term["confidence"] == 0.95
        assert term["term_name"] == "量子コンピュータ"

    def test_update_provisional_term_with_nonexistent_id_does_nothing(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_provisional_term does nothing for non-existent ID."""
        update_provisional_term(
            db_with_schema,
            term_id=999,
            definition="存在しない定義",
            confidence=0.5,
        )

        term = get_provisional_term(db_with_schema, 999)
        assert term is None
