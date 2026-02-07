"""Repository for terms_required table CRUD operations.

Thin wrapper around generic_term_repository functions.
"""

import sqlite3
from typing import Literal

from genglossary.db.generic_term_repository import (
    add_term,
    bulk_add_terms,
    delete_term as _delete_term,
    get_all_terms,
    get_term_by_id,
    get_term_texts,
    term_exists,
)
from genglossary.models.required_term import RequiredTerm

_TABLE = "terms_required"


def add_required_term(
    conn: sqlite3.Connection,
    term_text: str,
    source: Literal["manual"],
) -> tuple[int, bool]:
    """Add a term to the required list."""
    return add_term(conn, term_text, source, _TABLE, RequiredTerm)


def delete_required_term(conn: sqlite3.Connection, term_id: int) -> bool:
    """Delete a term from the required list."""
    return _delete_term(conn, term_id, _TABLE)


def get_all_required_terms(conn: sqlite3.Connection) -> list[RequiredTerm]:
    """Get all required terms."""
    return get_all_terms(conn, _TABLE, RequiredTerm)


def get_required_term_by_id(
    conn: sqlite3.Connection, term_id: int
) -> RequiredTerm | None:
    """Get a required term by its ID."""
    return get_term_by_id(conn, term_id, _TABLE, RequiredTerm)


def term_exists_in_required(conn: sqlite3.Connection, term_text: str) -> bool:
    """Check if a term exists in the required list."""
    return term_exists(conn, term_text, _TABLE)


def get_required_term_texts(conn: sqlite3.Connection) -> set[str]:
    """Get all required term texts as a set."""
    return get_term_texts(conn, _TABLE)


def bulk_add_required_terms(
    conn: sqlite3.Connection,
    terms: list[str],
    source: Literal["manual"],
) -> int:
    """Add multiple terms to the required list."""
    return bulk_add_terms(conn, terms, source, _TABLE)
