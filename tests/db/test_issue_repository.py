"""Tests for issue_repository module."""

import sqlite3

import pytest

from genglossary.db.issue_repository import (
    create_issue,
    get_issue,
    list_issues_by_run,
)
from genglossary.db.run_repository import create_run
from genglossary.db.schema import initialize_db


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateIssue:
    """Test create_issue function."""

    def test_create_issue_returns_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_issue returns an ID."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        issue_id = create_issue(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧です",
        )

        assert isinstance(issue_id, int)
        assert issue_id > 0

    def test_create_issue_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_issue stores data correctly."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        issue_id = create_issue(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧です",
            should_exclude=True,
            exclusion_reason="一般的すぎる",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM glossary_issues WHERE id = ?", (issue_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["run_id"] == run_id
        assert row["term_name"] == "量子コンピュータ"
        assert row["issue_type"] == "unclear"
        assert row["description"] == "定義が曖昧です"
        assert row["should_exclude"] == 1  # SQLite stores boolean as 0/1
        assert row["exclusion_reason"] == "一般的すぎる"

    def test_create_issue_with_defaults(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_issue uses default values."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        issue_id = create_issue(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧です",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM glossary_issues WHERE id = ?", (issue_id,))
        row = cursor.fetchone()

        assert row["should_exclude"] == 0
        assert row["exclusion_reason"] is None


class TestGetIssue:
    """Test get_issue function."""

    def test_get_issue_returns_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_issue returns issue data."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        issue_id = create_issue(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧です",
        )

        issue = get_issue(db_with_schema, issue_id)

        assert issue is not None
        assert issue["id"] == issue_id
        assert issue["term_name"] == "量子コンピュータ"
        assert issue["issue_type"] == "unclear"

    def test_get_issue_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_issue returns None for non-existent ID."""
        issue = get_issue(db_with_schema, 999)

        assert issue is None


class TestListIssuesByRun:
    """Test list_issues_by_run function."""

    def test_list_issues_by_run_returns_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns empty list when no issues."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        issues = list_issues_by_run(db_with_schema, run_id)

        assert issues == []

    def test_list_issues_by_run_returns_all_issues(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns all issues for a run."""
        run_id = create_run(db_with_schema, "/path/to/doc.txt", "ollama", "llama3.2")

        create_issue(
            db_with_schema,
            run_id=run_id,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧",
        )
        create_issue(
            db_with_schema,
            run_id=run_id,
            term_name="量子ビット",
            issue_type="contradiction",
            description="矛盾がある",
        )

        issues = list_issues_by_run(db_with_schema, run_id)

        assert len(issues) == 2
        assert issues[0]["term_name"] == "量子コンピュータ"
        assert issues[1]["term_name"] == "量子ビット"
