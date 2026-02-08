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
    should_exclude: bool = False,
    exclusion_reason: str | None = None,
) -> int:
    """Create a new glossary issue.

    Args:
        conn: Database connection.
        term_name: The term name this issue relates to.
        issue_type: Type of issue (e.g., "unclear", "contradiction").
        description: Description of the issue.
        should_exclude: Whether the term should be excluded.
        exclusion_reason: Reason for exclusion, if applicable.

    Returns:
        int: The ID of the created issue.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO glossary_issues
        (term_name, issue_type, description, should_exclude, exclusion_reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            term_name,
            issue_type,
            description,
            1 if should_exclude else 0,
            exclusion_reason,
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
    issues: Sequence[tuple[str, str, str] | tuple[str, str, str, bool, str | None]],
) -> None:
    """Create multiple issue records in a batch.

    Args:
        conn: Database connection.
        issues: List of tuples. Either 3-element (term_name, issue_type, description)
            or 5-element (term_name, issue_type, description, should_exclude, exclusion_reason).
    """
    if not issues:
        return
    if len(issues[0]) == 5:
        normalized = [
            (t[0], t[1], t[2], 1 if t[3] else 0, t[4])  # type: ignore[index]
            for t in issues
        ]
        batch_insert(
            conn,
            "glossary_issues",
            ["term_name", "issue_type", "description", "should_exclude", "exclusion_reason"],
            normalized,
        )
    else:
        batch_insert(
            conn, "glossary_issues", ["term_name", "issue_type", "description"], issues
        )
