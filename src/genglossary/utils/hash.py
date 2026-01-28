"""Hash utility functions."""

import hashlib


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of text content.

    Args:
        content: Text content to hash.

    Returns:
        str: Hexadecimal hash string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
