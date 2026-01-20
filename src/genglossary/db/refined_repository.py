"""Repository for glossary_refined table CRUD operations."""

import sqlite3

from genglossary.db.glossary_helpers import (
    create_glossary_term,
    delete_all_glossary_terms,
    get_glossary_term,
    list_all_glossary_terms,
    update_glossary_term,
)
from genglossary.db.models import GlossaryTermRow
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
    return create_glossary_term(
        conn, "glossary_refined", term_name, definition, confidence, occurrences
    )


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
    return get_glossary_term(conn, "glossary_refined", term_id)


def list_all_refined(conn: sqlite3.Connection) -> list[GlossaryTermRow]:
    """List all refined terms.

    Args:
        conn: Database connection.

    Returns:
        list[GlossaryTermRow]: List of term records with deserialized occurrences.
    """
    return list_all_glossary_terms(conn, "glossary_refined")


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
    update_glossary_term(conn, "glossary_refined", term_id, definition, confidence)


def delete_all_refined(conn: sqlite3.Connection) -> None:
    """Delete all refined terms.

    Args:
        conn: Database connection.
    """
    delete_all_glossary_terms(conn, "glossary_refined")
