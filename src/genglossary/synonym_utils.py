"""Shared utility functions for synonym group lookups."""

from genglossary.models.synonym import SynonymGroup


def build_synonym_lookup(
    synonym_groups: list[SynonymGroup] | None,
) -> dict[str, list[str]]:
    """Build a mapping from primary term to its synonym texts.

    Args:
        synonym_groups: List of synonym groups.

    Returns:
        dict mapping primary_term_text to list of other member texts.
    """
    if not synonym_groups:
        return {}
    result: dict[str, list[str]] = {}
    for group in synonym_groups:
        others = [
            m.term_text
            for m in group.members
            if m.term_text != group.primary_term_text
        ]
        if others:
            result[group.primary_term_text] = others
    return result


def build_non_primary_set(
    synonym_groups: list[SynonymGroup] | None,
) -> set[str]:
    """Build a set of non-primary synonym member texts.

    Args:
        synonym_groups: List of synonym groups.

    Returns:
        Set of term texts that are non-primary members.
    """
    if not synonym_groups:
        return set()
    non_primary: set[str] = set()
    for group in synonym_groups:
        for member in group.members:
            if member.term_text != group.primary_term_text:
                non_primary.add(member.term_text)
    return non_primary


def get_synonyms_for_primary(
    synonym_groups: list[SynonymGroup] | None,
    term_name: str,
) -> list[str]:
    """Get synonyms for a specific primary term.

    Args:
        synonym_groups: List of synonym groups.
        term_name: The primary term to look up.

    Returns:
        List of synonym texts for the term, or empty list if not found.
    """
    if not synonym_groups:
        return []
    for group in synonym_groups:
        if group.primary_term_text == term_name:
            return [
                m.term_text
                for m in group.members
                if m.term_text != group.primary_term_text
            ]
    return []
