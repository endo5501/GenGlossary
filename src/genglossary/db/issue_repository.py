"""Repository for glossary_issues table CRUD operations."""

import sqlite3
from typing import cast


def create_issue(
    conn: sqlite3.Connection,
    run_id: int,
    term_name: str,
    issue_type: str,
    description: str,
    should_exclude: bool = False,
    exclusion_reason: str | None = None,
) -> int:
    """Create a new glossary issue.

    Args:
        conn: Database connection.
        run_id: The run ID this issue belongs to.
        term_name: The term name this issue relates to.
        issue_type: Type of issue (e.g., "unclear", "contradiction").
        description: Description of the issue.
        should_exclude: Whether the term should be excluded from glossary.
        exclusion_reason: Reason for exclusion if should_exclude is True.

    Returns:
        int: The ID of the created issue.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO glossary_issues
        (run_id, term_name, issue_type, description, should_exclude, exclusion_reason)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            term_name,
            issue_type,
            description,
            1 if should_exclude else 0,
            exclusion_reason,
        ),
    )
    conn.commit()
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


def list_issues_by_run(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    """List all issues for a specific run.

    Args:
        conn: Database connection.
        run_id: The run ID to filter by.

    Returns:
        list[sqlite3.Row]: List of issue records for the specified run.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM glossary_issues WHERE run_id = ? ORDER BY id",
        (run_id,),
    )
    return cursor.fetchall()
