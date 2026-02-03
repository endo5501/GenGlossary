"""Repository for terms_extracted table CRUD operations."""

import sqlite3
from collections.abc import Sequence
from typing import cast

from genglossary.db.db_helpers import batch_insert


def create_term(
    conn: sqlite3.Connection,
    term_text: str,
    category: str | None = None,
) -> int:
    """Create a new extracted term record.

    Args:
        conn: Database connection.
        term_text: The extracted term text.
        category: Optional category of the term.

    Returns:
        int: The ID of the created term.

    Raises:
        sqlite3.IntegrityError: If term_text already exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO terms_extracted (term_text, category)
        VALUES (?, ?)
        """,
        (term_text, category),
    )
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


def list_all_terms(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """List all extracted terms, excluding those in the excluded terms list.

    Args:
        conn: Database connection.

    Returns:
        list[sqlite3.Row]: List of all term records ordered by id,
            excluding terms that are in the terms_excluded table.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM terms_extracted
        WHERE NOT EXISTS (
            SELECT 1 FROM terms_excluded
            WHERE terms_excluded.term_text = terms_extracted.term_text
        )
        ORDER BY id
        """
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

    Raises:
        ValueError: If no term with the given ID exists.
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
    if cursor.rowcount == 0:
        raise ValueError(f"Term with id {term_id} not found")


def delete_term(conn: sqlite3.Connection, term_id: int) -> None:
    """Delete a term record.

    Args:
        conn: Database connection.
        term_id: The term ID to delete.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_extracted WHERE id = ?", (term_id,))


def delete_all_terms(conn: sqlite3.Connection) -> None:
    """Delete all term records.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_extracted")


def create_terms_batch(
    conn: sqlite3.Connection,
    terms: Sequence[tuple[str, str | None]],
) -> None:
    """Create multiple term records in a batch.

    Args:
        conn: Database connection.
        terms: Sequence of tuples (term_text, category).

    Raises:
        sqlite3.IntegrityError: If any term_text already exists.
    """
    batch_insert(conn, "terms_extracted", ["term_text", "category"], terms)
