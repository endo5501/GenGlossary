"""Repository for terms_excluded table CRUD operations."""

import sqlite3
from datetime import datetime
from typing import Literal, cast

from genglossary.models.excluded_term import ExcludedTerm


def add_excluded_term(
    conn: sqlite3.Connection,
    term_text: str,
    source: Literal["auto", "manual"],
) -> tuple[int, bool]:
    """Add a term to the exclusion list.

    If the term already exists, returns the existing term's ID without
    raising an error.

    Args:
        conn: Database connection.
        term_text: The term text to exclude.
        source: How the term was added ('auto' or 'manual').

    Returns:
        tuple[int, bool]: A tuple of (term_id, created) where created is True
            if a new term was inserted, False if the term already existed.
    """
    cursor = conn.cursor()

    # Try to insert, on conflict return existing ID
    cursor.execute(
        """
        INSERT INTO terms_excluded (term_text, source)
        VALUES (?, ?)
        ON CONFLICT(term_text) DO NOTHING
        """,
        (term_text, source),
    )

    if cursor.lastrowid and cursor.rowcount > 0:
        return cast(int, cursor.lastrowid), True

    # Term already exists, get its ID
    cursor.execute(
        "SELECT id FROM terms_excluded WHERE term_text = ?",
        (term_text,),
    )
    row = cursor.fetchone()
    return cast(int, row["id"]), False


def delete_excluded_term(conn: sqlite3.Connection, term_id: int) -> bool:
    """Delete a term from the exclusion list.

    Args:
        conn: Database connection.
        term_id: The ID of the term to delete.

    Returns:
        bool: True if a term was deleted, False if no term with that ID exists.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_excluded WHERE id = ?", (term_id,))
    return cursor.rowcount > 0


def get_all_excluded_terms(conn: sqlite3.Connection) -> list[ExcludedTerm]:
    """Get all excluded terms.

    Args:
        conn: Database connection.

    Returns:
        list[ExcludedTerm]: List of all excluded terms ordered by ID.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms_excluded ORDER BY id")
    rows = cursor.fetchall()

    return [
        ExcludedTerm(
            id=row["id"],
            term_text=row["term_text"],
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def get_excluded_term_by_id(
    conn: sqlite3.Connection, term_id: int
) -> ExcludedTerm | None:
    """Get an excluded term by its ID.

    Args:
        conn: Database connection.
        term_id: The ID of the term to retrieve.

    Returns:
        ExcludedTerm | None: The excluded term if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms_excluded WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    return ExcludedTerm(
        id=row["id"],
        term_text=row["term_text"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def term_exists_in_excluded(conn: sqlite3.Connection, term_text: str) -> bool:
    """Check if a term exists in the exclusion list.

    Args:
        conn: Database connection.
        term_text: The term text to check.

    Returns:
        bool: True if the term exists in the exclusion list.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM terms_excluded WHERE term_text = ?",
        (term_text,),
    )
    return cursor.fetchone() is not None


def get_excluded_term_texts(conn: sqlite3.Connection) -> set[str]:
    """Get all excluded term texts as a set.

    This is optimized for filtering during term extraction.

    Args:
        conn: Database connection.

    Returns:
        set[str]: Set of all excluded term texts.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT term_text FROM terms_excluded")
    return {row["term_text"] for row in cursor.fetchall()}


def bulk_add_excluded_terms(
    conn: sqlite3.Connection,
    terms: list[str],
    source: Literal["auto", "manual"],
) -> int:
    """Add multiple terms to the exclusion list.

    Skips terms that already exist in the exclusion list.
    Normalizes term texts by stripping leading/trailing whitespace
    and skipping empty strings.

    Args:
        conn: Database connection.
        terms: List of term texts to add.
        source: How the terms were added ('auto' or 'manual').

    Returns:
        int: Number of terms actually added (excluding duplicates).
    """
    if not terms:
        return 0

    # Normalize: strip whitespace and filter empty strings
    normalized_terms = [t.strip() for t in terms if t.strip()]

    if not normalized_terms:
        return 0

    cursor = conn.cursor()
    added_count = 0

    for term_text in normalized_terms:
        cursor.execute(
            """
            INSERT INTO terms_excluded (term_text, source)
            VALUES (?, ?)
            ON CONFLICT(term_text) DO NOTHING
            """,
            (term_text, source),
        )
        if cursor.rowcount > 0:
            added_count += 1

    return added_count
