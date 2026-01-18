"""Repository for terms_extracted table CRUD operations."""

import sqlite3
from typing import cast


def create_term(
    conn: sqlite3.Connection,
    run_id: int,
    term_text: str,
    category: str | None = None,
) -> int:
    """Create a new extracted term record.

    Args:
        conn: Database connection.
        run_id: The run ID this term belongs to.
        term_text: The extracted term text.
        category: Optional category of the term.

    Returns:
        int: The ID of the created term.

    Raises:
        sqlite3.IntegrityError: If (run_id, term_text) already exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO terms_extracted (run_id, term_text, category)
        VALUES (?, ?, ?)
        """,
        (run_id, term_text, category),
    )
    conn.commit()
    return cast(int, cursor.lastrowid)


def get_term(conn: sqlite3.Connection, term_id: int) -> sqlite3.Row | None:
    """Get a term by ID.

    Args:
        conn: Database connection.
        term_id: The term ID to retrieve.

    Returns:
        sqlite3.Row | None: The term record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms_extracted WHERE id = ?", (term_id,))
    return cursor.fetchone()


def list_terms_by_run(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    """List all extracted terms for a specific run.

    Args:
        conn: Database connection.
        run_id: The run ID to filter by.

    Returns:
        list[sqlite3.Row]: List of term records for the specified run.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM terms_extracted WHERE run_id = ? ORDER BY id",
        (run_id,),
    )
    return cursor.fetchall()


def update_term(
    conn: sqlite3.Connection,
    term_id: int,
    term_text: str,
    category: str | None = None,
) -> None:
    """Update an existing term record.

    Args:
        conn: Database connection.
        term_id: The term ID to update.
        term_text: The new term text.
        category: The new category (or None to set NULL).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE terms_extracted
        SET term_text = ?, category = ?
        WHERE id = ?
        """,
        (term_text, category, term_id),
    )
    conn.commit()


def delete_term(conn: sqlite3.Connection, term_id: int) -> None:
    """Delete a term record.

    Args:
        conn: Database connection.
        term_id: The term ID to delete.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_extracted WHERE id = ?", (term_id,))
    conn.commit()
