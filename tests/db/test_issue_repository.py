"""Tests for issue_repository module."""

import sqlite3

import pytest

from genglossary.db.issue_repository import (
    create_issue,
    delete_all_issues,
    get_issue,
    list_all_issues,
)
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
        issue_id = create_issue(
            db_with_schema,
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
        issue_id = create_issue(
            db_with_schema,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧です",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM glossary_issues WHERE id = ?", (issue_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["term_name"] == "量子コンピュータ"
        assert row["issue_type"] == "unclear"
        assert row["description"] == "定義が曖昧です"


class TestGetIssue:
    """Test get_issue function."""

    def test_get_issue_returns_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_issue returns issue data."""
        issue_id = create_issue(
            db_with_schema,
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


class TestListAllIssues:
    """Test list_all_issues function."""

    def test_list_all_issues_returns_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns empty list when no issues."""
        issues = list_all_issues(db_with_schema)

        assert issues == []

    def test_list_all_issues_returns_all_issues(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list returns all issues."""
        create_issue(
            db_with_schema,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧",
        )
        create_issue(
            db_with_schema,
            term_name="量子ビット",
            issue_type="contradiction",
            description="矛盾がある",
        )

        issues = list_all_issues(db_with_schema)

        assert len(issues) == 2
        assert issues[0]["term_name"] == "量子コンピュータ"
        assert issues[1]["term_name"] == "量子ビット"


class TestDeleteAllIssues:
    """Test delete_all_issues function."""

    def test_delete_all_issues_removes_all_records(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_issues removes all records."""
        create_issue(
            db_with_schema,
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が曖昧",
        )
        create_issue(
            db_with_schema,
            term_name="量子ビット",
            issue_type="contradiction",
            description="矛盾がある",
        )

        delete_all_issues(db_with_schema)

        issues = list_all_issues(db_with_schema)
        assert issues == []

    def test_delete_all_issues_on_empty_table(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_issues works on empty table."""
        delete_all_issues(db_with_schema)

        issues = list_all_issues(db_with_schema)
        assert issues == []
