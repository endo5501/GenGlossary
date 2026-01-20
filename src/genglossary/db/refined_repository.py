"""Repository for glossary_refined table CRUD operations."""

import sqlite3
from typing import cast

from genglossary.db.models import (
    GlossaryTermRow,
    deserialize_occurrences,
    serialize_occurrences,
)
from genglossary.models.term import TermOccurrence


def create_refined_term(
    conn: sqlite3.Connection,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence],
) -> int:
    """Create a new refined glossary term.

    Args:
        conn: Database connection.
        term_name: The term name.
        definition: The term definition.
        confidence: Confidence score (0.0 to 1.0).
        occurrences: List of term occurrences.

    Returns:
        int: The ID of the created term.

    Raises:
        sqlite3.IntegrityError: If term_name already exists.
    """
    cursor = conn.cursor()
    occurrences_json = serialize_occurrences(occurrences)

    cursor.execute(
        """
        INSERT INTO glossary_refined
        (term_name, definition, confidence, occurrences)
        VALUES (?, ?, ?, ?)
        """,
        (term_name, definition, confidence, occurrences_json),
    )
    conn.commit()
    return cast(int, cursor.lastrowid)


def get_refined_term(
    conn: sqlite3.Connection, term_id: int
) -> GlossaryTermRow | None:
    """Get a refined term by ID.

    Args:
        conn: Database connection.
        term_id: The term ID to retrieve.

    Returns:
        GlossaryTermRow | None: The term record with deserialized occurrences,
            or None if not found.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM glossary_refined WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    # Deserialize occurrences from JSON
    return GlossaryTermRow(
        id=row["id"],
        term_name=row["term_name"],
        definition=row["definition"],
        confidence=row["confidence"],
        occurrences=deserialize_occurrences(row["occurrences"]),
    )


def list_all_refined(conn: sqlite3.Connection) -> list[GlossaryTermRow]:
    """List all refined terms.

    Args:
        conn: Database connection.

    Returns:
        list[GlossaryTermRow]: List of term records with deserialized occurrences.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM glossary_refined ORDER BY id")
    rows = cursor.fetchall()

    # Deserialize occurrences for each row
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


def update_refined_term(
    conn: sqlite3.Connection,
    term_id: int,
    definition: str,
    confidence: float,
) -> None:
    """Update a refined term's definition and confidence.

    Args:
        conn: Database connection.
        term_id: The term ID to update.
        definition: The new definition.
        confidence: The new confidence score (0.0 to 1.0).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE glossary_refined
        SET definition = ?, confidence = ?
        WHERE id = ?
        """,
        (definition, confidence, term_id),
    )
    conn.commit()


def delete_all_refined(conn: sqlite3.Connection) -> None:
    """Delete all refined terms.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM glossary_refined")
    conn.commit()
