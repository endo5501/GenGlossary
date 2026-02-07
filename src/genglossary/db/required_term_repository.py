"""Repository for terms_required table CRUD operations."""

import sqlite3
from datetime import datetime
from typing import Literal, cast

from genglossary.models.required_term import RequiredTerm


def add_required_term(
    conn: sqlite3.Connection,
    term_text: str,
    source: Literal["manual"],
) -> tuple[int, bool]:
    """Add a term to the required list.

    If the term already exists, returns the existing term's ID without
    raising an error.

    Args:
        conn: Database connection.
        term_text: The term text to require.
        source: How the term was added (currently 'manual' only).

    Returns:
        tuple[int, bool]: A tuple of (term_id, created) where created is True
            if a new term was inserted, False if the term already existed.
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO terms_required (term_text, source)
        VALUES (?, ?)
        ON CONFLICT(term_text) DO NOTHING
        """,
        (term_text, source),
    )

    if cursor.lastrowid and cursor.rowcount > 0:
        return cast(int, cursor.lastrowid), True

    cursor.execute(
        "SELECT id FROM terms_required WHERE term_text = ?",
        (term_text,),
    )
    row = cursor.fetchone()
    return cast(int, row["id"]), False


def delete_required_term(conn: sqlite3.Connection, term_id: int) -> bool:
    """Delete a term from the required list.

    Args:
        conn: Database connection.
        term_id: The ID of the term to delete.

    Returns:
        bool: True if a term was deleted, False if no term with that ID exists.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_required WHERE id = ?", (term_id,))
    return cursor.rowcount > 0


def get_all_required_terms(conn: sqlite3.Connection) -> list[RequiredTerm]:
    """Get all required terms.

    Args:
        conn: Database connection.

    Returns:
        list[RequiredTerm]: List of all required terms ordered by ID.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms_required ORDER BY id")
    rows = cursor.fetchall()

    return [
        RequiredTerm(
            id=row["id"],
            term_text=row["term_text"],
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def get_required_term_by_id(
    conn: sqlite3.Connection, term_id: int
) -> RequiredTerm | None:
    """Get a required term by its ID.

    Args:
        conn: Database connection.
        term_id: The ID of the term to retrieve.

    Returns:
        RequiredTerm | None: The required term if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms_required WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    return RequiredTerm(
        id=row["id"],
        term_text=row["term_text"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def term_exists_in_required(conn: sqlite3.Connection, term_text: str) -> bool:
    """Check if a term exists in the required list.

    Args:
        conn: Database connection.
        term_text: The term text to check.

    Returns:
        bool: True if the term exists in the required list.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM terms_required WHERE term_text = ?",
        (term_text,),
    )
    return cursor.fetchone() is not None


def get_required_term_texts(conn: sqlite3.Connection) -> set[str]:
    """Get all required term texts as a set.

    This is optimized for merging during term extraction.

    Args:
        conn: Database connection.

    Returns:
        set[str]: Set of all required term texts.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT term_text FROM terms_required")
    return {row["term_text"] for row in cursor.fetchall()}


def bulk_add_required_terms(
    conn: sqlite3.Connection,
    terms: list[str],
    source: Literal["manual"],
) -> int:
    """Add multiple terms to the required list.

    Skips terms that already exist in the required list.
    Normalizes term texts by stripping leading/trailing whitespace
    and skipping empty strings.

    Args:
        conn: Database connection.
        terms: List of term texts to add.
        source: How the terms were added (currently 'manual' only).

    Returns:
        int: Number of terms actually added (excluding duplicates).
    """
    if not terms:
        return 0

    normalized_terms = [t.strip() for t in terms if t.strip()]

    if not normalized_terms:
        return 0

    cursor = conn.cursor()
    added_count = 0

    for term_text in normalized_terms:
        cursor.execute(
            """
            INSERT INTO terms_required (term_text, source)
            VALUES (?, ?)
            ON CONFLICT(term_text) DO NOTHING
            """,
            (term_text, source),
        )
        if cursor.rowcount > 0:
            added_count += 1

    return added_count
