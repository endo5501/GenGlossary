"""Repository for glossary_provisional table CRUD operations."""

import sqlite3
from typing import cast

from genglossary.db.models import (
    GlossaryTermRow,
    deserialize_occurrences,
    serialize_occurrences,
)
from genglossary.models.term import TermOccurrence


def create_provisional_term(
    conn: sqlite3.Connection,
    run_id: int,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence],
) -> int:
    """Create a new provisional glossary term.

    Args:
        conn: Database connection.
        run_id: The run ID this term belongs to.
        term_name: The term name.
        definition: The term definition.
        confidence: Confidence score (0.0 to 1.0).
        occurrences: List of term occurrences.

    Returns:
        int: The ID of the created term.

    Raises:
        sqlite3.IntegrityError: If (run_id, term_name) already exists.
    """
    cursor = conn.cursor()
    occurrences_json = serialize_occurrences(occurrences)

    cursor.execute(
        """
        INSERT INTO glossary_provisional
        (run_id, term_name, definition, confidence, occurrences)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, term_name, definition, confidence, occurrences_json),
    )
    conn.commit()
    return cast(int, cursor.lastrowid)


def get_provisional_term(
    conn: sqlite3.Connection, term_id: int
) -> GlossaryTermRow | None:
    """Get a provisional term by ID.

    Args:
        conn: Database connection.
        term_id: The term ID to retrieve.

    Returns:
        GlossaryTermRow | None: The term record with deserialized occurrences,
            or None if not found.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM glossary_provisional WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    # Deserialize occurrences from JSON
    return GlossaryTermRow(
        id=row["id"],
        run_id=row["run_id"],
        term_name=row["term_name"],
        definition=row["definition"],
        confidence=row["confidence"],
        occurrences=deserialize_occurrences(row["occurrences"]),
    )


def list_provisional_terms_by_run(
    conn: sqlite3.Connection, run_id: int
) -> list[GlossaryTermRow]:
    """List all provisional terms for a specific run.

    Args:
        conn: Database connection.
        run_id: The run ID to filter by.

    Returns:
        list[GlossaryTermRow]: List of term records with deserialized occurrences.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM glossary_provisional WHERE run_id = ? ORDER BY id",
        (run_id,),
    )
    rows = cursor.fetchall()

    # Deserialize occurrences for each row
    return [
        GlossaryTermRow(
            id=row["id"],
            run_id=row["run_id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=deserialize_occurrences(row["occurrences"]),
        )
        for row in rows
    ]


def update_provisional_term(
    conn: sqlite3.Connection,
    term_id: int,
    definition: str,
    confidence: float,
) -> None:
    """Update a provisional term's definition and confidence.

    Args:
        conn: Database connection.
        term_id: The term ID to update.
        definition: The new definition.
        confidence: The new confidence score (0.0 to 1.0).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE glossary_provisional
        SET definition = ?, confidence = ?
        WHERE id = ?
        """,
        (definition, confidence, term_id),
    )
    conn.commit()
