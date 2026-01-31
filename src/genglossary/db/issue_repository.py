"""Repository for glossary_issues table CRUD operations."""

import sqlite3
from collections.abc import Sequence
from typing import cast

from genglossary.db.db_helpers import batch_insert


def create_issue(
    conn: sqlite3.Connection,
    term_name: str,
    issue_type: str,
    description: str,
) -> int:
    """Create a new glossary issue.

    Args:
        conn: Database connection.
        term_name: The term name this issue relates to.
        issue_type: Type of issue (e.g., "unclear", "contradiction").
        description: Description of the issue.

    Returns:
        int: The ID of the created issue.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO glossary_issues
        (term_name, issue_type, description)
        VALUES (?, ?, ?)
        """,
        (
            term_name,
            issue_type,
            description,
        ),
    )
    return cast(int, cursor.lastrowid)


def get_issue(conn: sqlite3.Connection, issue_id: int) -> sqlite3.Row | None:
    """Get an issue by ID.

    Args:
        conn: Database connection.
        issue_id: The issue ID to retrieve.

    Returns:
        sqlite3.Row | None: The issue record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM glossary_issues WHERE id = ?", (issue_id,))
    return cursor.fetchone()


def list_all_issues(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """List all issues.

    Args:
        conn: Database connection.

    Returns:
        list[sqlite3.Row]: List of all issue records.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM glossary_issues ORDER BY id")
    return cursor.fetchall()


def delete_all_issues(conn: sqlite3.Connection) -> None:
    """Delete all issues from the glossary_issues table.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM glossary_issues")


def create_issues_batch(
    conn: sqlite3.Connection,
    issues: Sequence[tuple[str, str, str]],
) -> None:
    """Create multiple issue records in a batch.

    Args:
        conn: Database connection.
        issues: List of tuples (term_name, issue_type, description).
    """
    batch_insert(
        conn, "glossary_issues", ["term_name", "issue_type", "description"], issues
    )
