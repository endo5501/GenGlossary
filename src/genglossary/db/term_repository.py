"""Repository for terms_extracted table CRUD operations."""

import sqlite3
from collections.abc import Sequence
from typing import cast

from genglossary.db.db_helpers import batch_insert


def create_term(
    conn: sqlite3.Connection,
    term_text: str,
    category: str | None = None,
) -> int:
    """Create a new extracted term record.

    Args:
        conn: Database connection.
        term_text: The extracted term text.
        category: Optional category of the term.

    Returns:
        int: The ID of the created term.

    Raises:
        sqlite3.IntegrityError: If term_text already exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO terms_extracted (term_text, category)
        VALUES (?, ?)
        """,
        (term_text, category),
    )
    return cast(int, cursor.lastrowid)


def get_term(conn: sqlite3.Connection, term_id: int) -> sqlite3.Row | None:
    """Get a term by ID.

    Args:
        conn: Database connection.
        term_id: The term ID to retrieve.

    Returns:
        sqlite3.Row | None: The term record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms_extracted WHERE id = ?", (term_id,))
    return cursor.fetchone()


def list_all_terms(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """List all terms: extracted terms plus required-only terms.

    Returns extracted terms combined with required terms that are not yet
    in terms_extracted. Required-only terms use negative IDs (negated
    terms_required.id) to distinguish them from extracted terms.

    Excluded terms are filtered out, but required terms override exclusion
    (a term in both required and excluded lists will be shown).

    Args:
        conn: Database connection.

    Returns:
        list[sqlite3.Row]: List of all term records ordered by term_text.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, term_text, category, user_notes FROM terms_extracted
        WHERE NOT EXISTS (
            SELECT 1 FROM terms_excluded
            WHERE terms_excluded.term_text = terms_extracted.term_text
        )
        OR EXISTS (
            SELECT 1 FROM terms_required
            WHERE terms_required.term_text = terms_extracted.term_text
        )
        UNION ALL
        SELECT -id, term_text, NULL AS category, '' AS user_notes FROM terms_required
        WHERE NOT EXISTS (
            SELECT 1 FROM terms_extracted
            WHERE terms_extracted.term_text = terms_required.term_text
        )
        ORDER BY term_text
        """
    )
    return cursor.fetchall()


def update_term(
    conn: sqlite3.Connection,
    term_id: int,
    term_text: str,
    category: str | None = None,
    user_notes: str | None = None,
) -> None:
    """Update an existing term record.

    Args:
        conn: Database connection.
        term_id: The term ID to update.
        term_text: The new term text.
        category: The new category (or None to set NULL).
        user_notes: The new user notes (None to preserve existing value).

    Raises:
        ValueError: If no term with the given ID exists.
    """
    cursor = conn.cursor()
    if user_notes is not None:
        cursor.execute(
            """
            UPDATE terms_extracted
            SET term_text = ?, category = ?, user_notes = ?
            WHERE id = ?
            """,
            (term_text, category, user_notes, term_id),
        )
    else:
        cursor.execute(
            """
            UPDATE terms_extracted
            SET term_text = ?, category = ?
            WHERE id = ?
            """,
            (term_text, category, term_id),
        )
    if cursor.rowcount == 0:
        raise ValueError(f"Term with id {term_id} not found")


def delete_term(conn: sqlite3.Connection, term_id: int) -> None:
    """Delete a term record.

    Args:
        conn: Database connection.
        term_id: The term ID to delete.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_extracted WHERE id = ?", (term_id,))


def delete_all_terms(conn: sqlite3.Connection) -> None:
    """Delete all term records.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_extracted")


def backup_user_notes(conn: sqlite3.Connection) -> dict[str, str]:
    """Backup user_notes for all terms with non-empty notes.

    Args:
        conn: Database connection.

    Returns:
        dict[str, str]: Mapping of term_text to user_notes.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT term_text, user_notes FROM terms_extracted WHERE user_notes != ''"
    )
    return {row["term_text"]: row["user_notes"] for row in cursor.fetchall()}


def restore_user_notes(
    conn: sqlite3.Connection, notes_map: dict[str, str]
) -> None:
    """Restore user_notes from a backup map.

    Args:
        conn: Database connection.
        notes_map: Mapping of term_text to user_notes.
    """
    cursor = conn.cursor()
    for term_text, user_notes in notes_map.items():
        cursor.execute(
            "UPDATE terms_extracted SET user_notes = ? WHERE term_text = ?",
            (user_notes, term_text),
        )


def create_terms_batch(
    conn: sqlite3.Connection,
    terms: Sequence[tuple[str, str | None]],
) -> None:
    """Create multiple term records in a batch.

    Args:
        conn: Database connection.
        terms: Sequence of tuples (term_text, category).

    Raises:
        sqlite3.IntegrityError: If any term_text already exists.
    """
    batch_insert(conn, "terms_extracted", ["term_text", "category"], terms)
