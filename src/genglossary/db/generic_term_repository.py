"""Generic repository functions for term tables (excluded/required)."""

import sqlite3
from datetime import datetime
from typing import TypeVar, cast

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def add_term(
    conn: sqlite3.Connection,
    term_text: str,
    source: str,
    table: str,
    model_type: type[T],
) -> tuple[int, bool]:
    """Add a term to the specified table.

    If the term already exists, returns the existing term's ID without
    raising an error.

    Args:
        conn: Database connection.
        term_text: The term text to add.
        source: How the term was added.
        table: The database table name.
        model_type: The Pydantic model type (unused, kept for API consistency).

    Returns:
        tuple[int, bool]: A tuple of (term_id, created) where created is True
            if a new term was inserted, False if the term already existed.
    """
    cursor = conn.cursor()

    cursor.execute(
        f"""
        INSERT INTO {table} (term_text, source)
        VALUES (?, ?)
        ON CONFLICT(term_text) DO NOTHING
        """,
        (term_text, source),
    )

    if cursor.lastrowid and cursor.rowcount > 0:
        return cast(int, cursor.lastrowid), True

    cursor.execute(
        f"SELECT id FROM {table} WHERE term_text = ?",
        (term_text,),
    )
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError(
            f"Failed to retrieve term from {table}: '{term_text}'"
        )
    return cast(int, row["id"]), False


def delete_term(conn: sqlite3.Connection, term_id: int, table: str) -> bool:
    """Delete a term from the specified table.

    Args:
        conn: Database connection.
        term_id: The ID of the term to delete.
        table: The database table name.

    Returns:
        bool: True if a term was deleted, False if no term with that ID exists.
    """
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (term_id,))
    return cursor.rowcount > 0


def get_all_terms(
    conn: sqlite3.Connection, table: str, model_type: type[T]
) -> list[T]:
    """Get all terms from the specified table.

    Args:
        conn: Database connection.
        table: The database table name.
        model_type: The Pydantic model type to construct.

    Returns:
        list[T]: List of all terms ordered by ID.
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} ORDER BY id")
    rows = cursor.fetchall()

    return [
        model_type(
            id=row["id"],
            term_text=row["term_text"],
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def get_term_by_id(
    conn: sqlite3.Connection, term_id: int, table: str, model_type: type[T]
) -> T | None:
    """Get a term by its ID from the specified table.

    Args:
        conn: Database connection.
        term_id: The ID of the term to retrieve.
        table: The database table name.
        model_type: The Pydantic model type to construct.

    Returns:
        T | None: The term if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    return model_type(
        id=row["id"],
        term_text=row["term_text"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def term_exists(conn: sqlite3.Connection, term_text: str, table: str) -> bool:
    """Check if a term exists in the specified table.

    Args:
        conn: Database connection.
        term_text: The term text to check.
        table: The database table name.

    Returns:
        bool: True if the term exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT 1 FROM {table} WHERE term_text = ?",
        (term_text,),
    )
    return cursor.fetchone() is not None


def get_term_texts(conn: sqlite3.Connection, table: str) -> set[str]:
    """Get all term texts as a set from the specified table.

    Args:
        conn: Database connection.
        table: The database table name.

    Returns:
        set[str]: Set of all term texts.
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT term_text FROM {table}")
    return {row["term_text"] for row in cursor.fetchall()}


def bulk_add_terms(
    conn: sqlite3.Connection,
    terms: list[str],
    source: str,
    table: str,
) -> int:
    """Add multiple terms to the specified table.

    Skips terms that already exist. Normalizes term texts by stripping
    leading/trailing whitespace and skipping empty strings.

    Args:
        conn: Database connection.
        terms: List of term texts to add.
        source: How the terms were added.
        table: The database table name.

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
            f"""
            INSERT INTO {table} (term_text, source)
            VALUES (?, ?)
            ON CONFLICT(term_text) DO NOTHING
            """,
            (term_text, source),
        )
        if cursor.rowcount > 0:
            added_count += 1

    return added_count
