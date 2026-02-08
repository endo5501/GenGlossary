"""Repository functions for synonym group tables."""

import sqlite3
from typing import cast

from genglossary.models.synonym import SynonymGroup, SynonymMember


def create_group(
    conn: sqlite3.Connection,
    primary_term_text: str,
    member_texts: list[str],
) -> int:
    """Create a synonym group with members.

    Args:
        conn: Database connection.
        primary_term_text: The representative term for the group.
        member_texts: List of term texts to include as members.

    Returns:
        The ID of the created group.

    Raises:
        sqlite3.IntegrityError: If any member term already belongs to another group.
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO term_synonym_groups (primary_term_text) VALUES (?)",
        (primary_term_text,),
    )
    group_id = cast(int, cursor.lastrowid)

    for term_text in member_texts:
        cursor.execute(
            "INSERT INTO term_synonym_members (group_id, term_text) VALUES (?, ?)",
            (group_id, term_text),
        )

    return group_id


def delete_group(conn: sqlite3.Connection, group_id: int) -> bool:
    """Delete a synonym group and its members (via CASCADE).

    Args:
        conn: Database connection.
        group_id: The ID of the group to delete.

    Returns:
        True if a group was deleted, False if not found.
    """
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM term_synonym_groups WHERE id = ?", (group_id,)
    )
    return cursor.rowcount > 0


def add_member(
    conn: sqlite3.Connection, group_id: int, term_text: str
) -> int:
    """Add a member to an existing synonym group.

    Args:
        conn: Database connection.
        group_id: The ID of the group.
        term_text: The term text to add.

    Returns:
        The ID of the created member.

    Raises:
        sqlite3.IntegrityError: If the term already belongs to a group.
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO term_synonym_members (group_id, term_text) VALUES (?, ?)",
        (group_id, term_text),
    )
    return cast(int, cursor.lastrowid)


def remove_member(
    conn: sqlite3.Connection, group_id: int, member_id: int
) -> bool:
    """Remove a member from a synonym group.

    Args:
        conn: Database connection.
        group_id: The expected group ID the member belongs to.
        member_id: The ID of the member to remove.

    Returns:
        True if a member was removed, False if not found.

    Raises:
        ValueError: If the member exists but belongs to a different group.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT group_id FROM term_synonym_members WHERE id = ?", (member_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return False
    if row["group_id"] != group_id:
        raise ValueError(
            f"Member {member_id} does not belong to group {group_id}"
        )
    cursor.execute(
        "DELETE FROM term_synonym_members WHERE id = ?", (member_id,)
    )
    return cursor.rowcount > 0


def update_primary_term(
    conn: sqlite3.Connection, group_id: int, new_primary_text: str
) -> bool:
    """Update the primary term of a synonym group.

    Args:
        conn: Database connection.
        group_id: The ID of the group.
        new_primary_text: The new primary term text.

    Returns:
        True if the group was updated, False if not found.
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE term_synonym_groups SET primary_term_text = ? WHERE id = ?",
        (new_primary_text, group_id),
    )
    return cursor.rowcount > 0


def list_groups(conn: sqlite3.Connection) -> list[SynonymGroup]:
    """List all synonym groups with their members.

    Args:
        conn: Database connection.

    Returns:
        List of all synonym groups ordered by ID.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, primary_term_text, created_at FROM term_synonym_groups ORDER BY id"
    )
    group_rows = cursor.fetchall()

    groups: list[SynonymGroup] = []
    for row in group_rows:
        group_id = row["id"]
        cursor.execute(
            "SELECT id, group_id, term_text, created_at FROM term_synonym_members WHERE group_id = ? ORDER BY id",
            (group_id,),
        )
        member_rows = cursor.fetchall()
        members = [
            SynonymMember(
                id=m["id"],
                group_id=m["group_id"],
                term_text=m["term_text"],
            )
            for m in member_rows
        ]
        groups.append(
            SynonymGroup(
                id=group_id,
                primary_term_text=row["primary_term_text"],
                members=members,
            )
        )

    return groups


def get_synonyms_for_term(
    conn: sqlite3.Connection, term_text: str
) -> list[str]:
    """Get all synonyms for a given term (excluding the term itself).

    Args:
        conn: Database connection.
        term_text: The term text to look up.

    Returns:
        List of synonym term texts, excluding the input term.
        Returns empty list if the term is not in any group.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT group_id FROM term_synonym_members WHERE term_text = ?",
        (term_text,),
    )
    row = cursor.fetchone()
    if row is None:
        return []

    group_id = row["group_id"]
    cursor.execute(
        "SELECT term_text FROM term_synonym_members WHERE group_id = ? AND term_text != ?",
        (group_id, term_text),
    )
    return [r["term_text"] for r in cursor.fetchall()]
