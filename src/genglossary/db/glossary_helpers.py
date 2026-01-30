"""Shared helper functions for glossary repositories.

This module provides common CRUD operations for glossary_provisional
and glossary_refined tables to reduce code duplication.
"""

import sqlite3
from typing import Literal, cast

from genglossary.db.models import (
    GlossaryTermRow,
    deserialize_occurrences,
    serialize_occurrences,
)
from genglossary.models.term import TermOccurrence

# Type for glossary table names
GlossaryTable = Literal["glossary_provisional", "glossary_refined"]

# Allowed table names for SQL injection prevention
ALLOWED_TABLES: set[str] = {"glossary_provisional", "glossary_refined"}


def _validate_table_name(table_name: str) -> None:
    """Validate that the table name is allowed.

    Args:
        table_name: The table name to validate.

    Raises:
        ValueError: If the table name is not in the allowed list.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")


def create_glossary_term(
    conn: sqlite3.Connection,
    table_name: GlossaryTable,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence],
) -> int:
    """Create a new glossary term in the specified table.

    Args:
        conn: Database connection.
        table_name: The glossary table ("glossary_provisional" or "glossary_refined").
        term_name: The term name.
        definition: The term definition.
        confidence: Confidence score (0.0 to 1.0).
        occurrences: List of term occurrences.

    Returns:
        int: The ID of the created term.

    Raises:
        sqlite3.IntegrityError: If term_name already exists.
        ValueError: If table_name is not allowed.
    """
    _validate_table_name(table_name)

    cursor = conn.cursor()
    occurrences_json = serialize_occurrences(occurrences)

    cursor.execute(
        f"""
        INSERT INTO {table_name}
        (term_name, definition, confidence, occurrences)
        VALUES (?, ?, ?, ?)
        """,
        (term_name, definition, confidence, occurrences_json),
    )
    return cast(int, cursor.lastrowid)


def get_glossary_term(
    conn: sqlite3.Connection, table_name: GlossaryTable, term_id: int
) -> GlossaryTermRow | None:
    """Get a glossary term by ID from the specified table.

    Args:
        conn: Database connection.
        table_name: The glossary table ("glossary_provisional" or "glossary_refined").
        term_id: The term ID to retrieve.

    Returns:
        GlossaryTermRow | None: The term record with deserialized occurrences,
            or None if not found.

    Raises:
        ValueError: If table_name is not allowed.
    """
    _validate_table_name(table_name)

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    return GlossaryTermRow(
        id=row["id"],
        term_name=row["term_name"],
        definition=row["definition"],
        confidence=row["confidence"],
        occurrences=deserialize_occurrences(row["occurrences"]),
    )


def list_all_glossary_terms(
    conn: sqlite3.Connection, table_name: GlossaryTable
) -> list[GlossaryTermRow]:
    """List all glossary terms from the specified table.

    Args:
        conn: Database connection.
        table_name: The glossary table ("glossary_provisional" or "glossary_refined").

    Returns:
        list[GlossaryTermRow]: List of term records with deserialized occurrences.

    Raises:
        ValueError: If table_name is not allowed.
    """
    _validate_table_name(table_name)

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
    rows = cursor.fetchall()

    return [
        GlossaryTermRow(
            id=row["id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=deserialize_occurrences(row["occurrences"]),
        )
        for row in rows
    ]


def update_glossary_term(
    conn: sqlite3.Connection,
    table_name: GlossaryTable,
    term_id: int,
    definition: str,
    confidence: float,
) -> None:
    """Update a glossary term's definition and confidence.

    Args:
        conn: Database connection.
        table_name: The glossary table ("glossary_provisional" or "glossary_refined").
        term_id: The term ID to update.
        definition: The new definition.
        confidence: The new confidence score (0.0 to 1.0).

    Raises:
        ValueError: If table_name is not allowed or if no term with the given ID exists.
    """
    _validate_table_name(table_name)

    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE {table_name}
        SET definition = ?, confidence = ?
        WHERE id = ?
        """,
        (definition, confidence, term_id),
    )
    if cursor.rowcount == 0:
        raise ValueError(f"Term with id {term_id} not found in {table_name}")


def delete_all_glossary_terms(
    conn: sqlite3.Connection, table_name: GlossaryTable
) -> None:
    """Delete all glossary terms from the specified table.

    Args:
        conn: Database connection.
        table_name: The glossary table ("glossary_provisional" or "glossary_refined").

    Raises:
        ValueError: If table_name is not allowed.
    """
    _validate_table_name(table_name)

    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name}")
