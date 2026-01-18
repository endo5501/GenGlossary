"""Repository for glossary_refined table CRUD operations."""

import sqlite3
from typing import TypedDict, cast

from genglossary.db.models import deserialize_occurrences, serialize_occurrences
from genglossary.models.term import TermOccurrence


class RefinedTermRow(TypedDict):
    """Typed dict for refined term row with deserialized occurrences."""

    id: int
    run_id: int
    term_name: str
    definition: str
    confidence: float
    occurrences: list[TermOccurrence]


def create_refined_term(
    conn: sqlite3.Connection,
    run_id: int,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence],
) -> int:
    """Create a new refined glossary term.

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
        INSERT INTO glossary_refined
        (run_id, term_name, definition, confidence, occurrences)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, term_name, definition, confidence, occurrences_json),
    )
    conn.commit()
    return cast(int, cursor.lastrowid)


def get_refined_term(
    conn: sqlite3.Connection, term_id: int
) -> RefinedTermRow | None:
    """Get a refined term by ID.

    Args:
        conn: Database connection.
        term_id: The term ID to retrieve.

    Returns:
        RefinedTermRow | None: The term record with deserialized occurrences,
            or None if not found.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM glossary_refined WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    # Deserialize occurrences from JSON
    return RefinedTermRow(
        id=row["id"],
        run_id=row["run_id"],
        term_name=row["term_name"],
        definition=row["definition"],
        confidence=row["confidence"],
        occurrences=deserialize_occurrences(row["occurrences"]),
    )


def list_refined_terms_by_run(
    conn: sqlite3.Connection, run_id: int
) -> list[RefinedTermRow]:
    """List all refined terms for a specific run.

    Args:
        conn: Database connection.
        run_id: The run ID to filter by.

    Returns:
        list[RefinedTermRow]: List of term records with deserialized occurrences.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM glossary_refined WHERE run_id = ? ORDER BY id",
        (run_id,),
    )
    rows = cursor.fetchall()

    # Deserialize occurrences for each row
    return [
        RefinedTermRow(
            id=row["id"],
            run_id=row["run_id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=deserialize_occurrences(row["occurrences"]),
        )
        for row in rows
    ]
