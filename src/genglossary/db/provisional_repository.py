"""Repository for glossary_provisional table CRUD operations."""

import sqlite3
from collections.abc import Sequence

from genglossary.db.glossary_helpers import (
    create_glossary_term,
    create_glossary_terms_batch,
    delete_all_glossary_terms,
    get_glossary_term,
    list_all_glossary_terms,
    update_glossary_term,
)
from genglossary.db.models import GlossaryTermRow
from genglossary.models.term import TermOccurrence


def create_provisional_term(
    conn: sqlite3.Connection,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence],
) -> int:
    """Create a new provisional glossary term.

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
        conn, "glossary_provisional", term_name, definition, confidence, occurrences
    )


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
    return get_glossary_term(conn, "glossary_provisional", term_id)


def list_all_provisional(conn: sqlite3.Connection) -> list[GlossaryTermRow]:
    """List all provisional terms.

    Args:
        conn: Database connection.

    Returns:
        list[GlossaryTermRow]: List of term records with deserialized occurrences.
    """
    return list_all_glossary_terms(conn, "glossary_provisional")


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
    update_glossary_term(conn, "glossary_provisional", term_id, definition, confidence)


def delete_all_provisional(conn: sqlite3.Connection) -> None:
    """Delete all provisional terms.

    Args:
        conn: Database connection.
    """
    delete_all_glossary_terms(conn, "glossary_provisional")


def create_provisional_terms_batch(
    conn: sqlite3.Connection,
    terms: Sequence[tuple[str, str, float, list[TermOccurrence]]],
) -> None:
    """Create multiple provisional glossary terms in a batch.

    Args:
        conn: Database connection.
        terms: List of tuples (term_name, definition, confidence, occurrences).

    Raises:
        sqlite3.IntegrityError: If any term_name already exists.
    """
    create_glossary_terms_batch(conn, "glossary_provisional", terms)
