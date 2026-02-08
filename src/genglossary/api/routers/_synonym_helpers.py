"""Helper functions for synonym group data in API responses."""

import sqlite3

from genglossary.db.synonym_repository import list_groups


def build_aliases_map(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Build a mapping of primary term names to their alias texts.

    Args:
        conn: Project database connection.

    Returns:
        Dict mapping primary_term_text to list of non-primary member texts.
    """
    groups = list_groups(conn)
    aliases_map: dict[str, list[str]] = {}
    for group in groups:
        aliases = [
            m.term_text
            for m in group.members
            if m.term_text != group.primary_term_text
        ]
        if aliases:
            aliases_map[group.primary_term_text] = aliases
    return aliases_map
