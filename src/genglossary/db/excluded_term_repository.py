"""Repository for terms_excluded table CRUD operations.

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
from genglossary.models.excluded_term import ExcludedTerm

_TABLE = "terms_excluded"


def add_excluded_term(
    conn: sqlite3.Connection,
    term_text: str,
    source: Literal["auto", "manual"],
) -> tuple[int, bool]:
    """Add a term to the exclusion list."""
    return add_term(conn, term_text, source, _TABLE, ExcludedTerm)


def delete_excluded_term(conn: sqlite3.Connection, term_id: int) -> bool:
    """Delete a term from the exclusion list."""
    return _delete_term(conn, term_id, _TABLE)


def get_all_excluded_terms(conn: sqlite3.Connection) -> list[ExcludedTerm]:
    """Get all excluded terms."""
    return get_all_terms(conn, _TABLE, ExcludedTerm)


def get_excluded_term_by_id(
    conn: sqlite3.Connection, term_id: int
) -> ExcludedTerm | None:
    """Get an excluded term by its ID."""
    return get_term_by_id(conn, term_id, _TABLE, ExcludedTerm)


def term_exists_in_excluded(conn: sqlite3.Connection, term_text: str) -> bool:
    """Check if a term exists in the exclusion list."""
    return term_exists(conn, term_text, _TABLE)


def get_excluded_term_texts(conn: sqlite3.Connection) -> set[str]:
    """Get all excluded term texts as a set."""
    return get_term_texts(conn, _TABLE)


def bulk_add_excluded_terms(
    conn: sqlite3.Connection,
    terms: list[str],
    source: Literal["auto", "manual"],
) -> int:
    """Add multiple terms to the exclusion list."""
    return bulk_add_terms(conn, terms, source, _TABLE)
