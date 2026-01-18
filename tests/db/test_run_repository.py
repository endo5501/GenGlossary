"""Tests for run_repository module."""

import sqlite3
from datetime import datetime

import pytest

from genglossary.db.run_repository import (
    complete_run,
    create_run,
    fail_run,
    get_latest_run,
    get_run,
    list_runs,
    update_run_status,
)
from genglossary.db.schema import initialize_db


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized.

    Args:
        in_memory_db: Base in-memory database fixture.

    Returns:
        sqlite3.Connection: Database with schema initialized.
    """
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateRun:
    """Test create_run function."""

    def test_create_run_returns_run_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_run returns a run ID."""
        run_id = create_run(
            db_with_schema,
            input_path="/path/to/doc.txt",
            llm_provider="ollama",
            llm_model="llama3.2",
        )

        assert isinstance(run_id, int)
        assert run_id > 0

    def test_create_run_stores_data(self, db_with_schema: sqlite3.Connection) -> None:
        """Test that create_run stores data correctly."""
        run_id = create_run(
            db_with_schema,
            input_path="/path/to/doc.txt",
            llm_provider="ollama",
            llm_model="llama3.2",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["input_path"] == "/path/to/doc.txt"
        assert row["llm_provider"] == "ollama"
        assert row["llm_model"] == "llama3.2"
        assert row["status"] == "running"
        assert row["started_at"] is not None
        assert row["completed_at"] is None
        assert row["error_message"] is None


class TestGetRun:
    """Test get_run function."""

    def test_get_run_returns_run_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_run returns run data."""
        run_id = create_run(
            db_with_schema,
            input_path="/path/to/doc.txt",
            llm_provider="ollama",
            llm_model="llama3.2",
        )

        run = get_run(db_with_schema, run_id)

        assert run is not None
        assert run["id"] == run_id
        assert run["input_path"] == "/path/to/doc.txt"
        assert run["llm_provider"] == "ollama"
        assert run["llm_model"] == "llama3.2"
        assert run["status"] == "running"

    def test_get_run_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_run returns None for non-existent ID."""
        run = get_run(db_with_schema, 999)

        assert run is None


class TestUpdateRunStatus:
    """Test update_run_status function."""

    def test_update_run_status_changes_status(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_run_status changes the status."""
        run_id = create_run(
            db_with_schema,
            input_path="/path/to/doc.txt",
            llm_provider="ollama",
            llm_model="llama3.2",
        )

        update_run_status(db_with_schema, run_id, "completed")

        run = get_run(db_with_schema, run_id)
        assert run["status"] == "completed"


class TestCompleteRun:
    """Test complete_run function."""

    def test_complete_run_sets_status_and_timestamp(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that complete_run sets status to 'completed' and sets timestamp."""
        run_id = create_run(
            db_with_schema,
            input_path="/path/to/doc.txt",
            llm_provider="ollama",
            llm_model="llama3.2",
        )

        complete_run(db_with_schema, run_id)

        run = get_run(db_with_schema, run_id)
        assert run["status"] == "completed"
        assert run["completed_at"] is not None
        assert run["error_message"] is None


class TestFailRun:
    """Test fail_run function."""

    def test_fail_run_sets_status_and_error(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that fail_run sets status to 'failed' and stores error message."""
        run_id = create_run(
            db_with_schema,
            input_path="/path/to/doc.txt",
            llm_provider="ollama",
            llm_model="llama3.2",
        )

        error_msg = "LLM API connection failed"
        fail_run(db_with_schema, run_id, error_msg)

        run = get_run(db_with_schema, run_id)
        assert run["status"] == "failed"
        assert run["completed_at"] is not None
        assert run["error_message"] == error_msg


class TestListRuns:
    """Test list_runs function."""

    def test_list_runs_returns_empty_for_empty_db(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_runs returns empty list for empty database."""
        runs = list_runs(db_with_schema)

        assert runs == []

    def test_list_runs_returns_all_runs(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_runs returns all runs."""
        run_id1 = create_run(
            db_with_schema, "/path/to/doc1.txt", "ollama", "llama3.2"
        )
        run_id2 = create_run(
            db_with_schema, "/path/to/doc2.txt", "openai", "gpt-4"
        )

        runs = list_runs(db_with_schema)

        assert len(runs) == 2
        assert runs[0]["id"] == run_id1
        assert runs[1]["id"] == run_id2

    def test_list_runs_ordered_by_id_desc(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_runs returns runs ordered by ID descending."""
        run_id1 = create_run(
            db_with_schema, "/path/to/doc1.txt", "ollama", "llama3.2"
        )
        run_id2 = create_run(
            db_with_schema, "/path/to/doc2.txt", "openai", "gpt-4"
        )

        runs = list_runs(db_with_schema)

        # Most recent (highest ID) should be first
        assert runs[0]["id"] == run_id2
        assert runs[1]["id"] == run_id1

    def test_list_runs_with_limit(self, db_with_schema: sqlite3.Connection) -> None:
        """Test that list_runs respects limit parameter."""
        create_run(db_with_schema, "/path/to/doc1.txt", "ollama", "llama3.2")
        create_run(db_with_schema, "/path/to/doc2.txt", "ollama", "llama3.2")
        create_run(db_with_schema, "/path/to/doc3.txt", "ollama", "llama3.2")

        runs = list_runs(db_with_schema, limit=2)

        assert len(runs) == 2


class TestGetLatestRun:
    """Test get_latest_run function."""

    def test_get_latest_run_returns_none_for_empty_db(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_latest_run returns None for empty database."""
        run = get_latest_run(db_with_schema)

        assert run is None

    def test_get_latest_run_returns_most_recent(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_latest_run returns the most recent run."""
        create_run(db_with_schema, "/path/to/doc1.txt", "ollama", "llama3.2")
        run_id2 = create_run(
            db_with_schema, "/path/to/doc2.txt", "openai", "gpt-4"
        )

        run = get_latest_run(db_with_schema)

        assert run is not None
        assert run["id"] == run_id2
        assert run["input_path"] == "/path/to/doc2.txt"
