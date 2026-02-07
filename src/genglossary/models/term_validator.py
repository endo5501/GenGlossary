"""Shared validator for term_text field used by ExcludedTerm and RequiredTerm."""


def validate_term_text(v: str) -> str:
    """Validate and normalize term text.

    Args:
        v: The term text to validate.

    Returns:
        The validated and stripped term text.

    Raises:
        ValueError: If the term text is empty or contains only whitespace.
    """
    stripped = v.strip()
    if not stripped:
        raise ValueError("Term text cannot be empty")
    return stripped
