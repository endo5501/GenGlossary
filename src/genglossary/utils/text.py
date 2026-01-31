"""Text utility functions for CJK and Unicode processing."""

# Unicode ranges for CJK character detection
CJK_RANGES: list[tuple[str, str]] = [
    ("\u4e00", "\u9fff"),  # CJK Unified Ideographs
    ("\u3040", "\u309f"),  # Hiragana
    ("\u30a0", "\u30ff"),  # Katakana
    ("\uac00", "\ud7af"),  # Korean Hangul
]


def is_cjk_char(char: str) -> bool:
    """Check if a single character is CJK.

    Args:
        char: A single character to check.

    Returns:
        True if the character is in a CJK range.
    """
    return any(start <= char <= end for start, end in CJK_RANGES)


def contains_cjk(text: str) -> bool:
    """Check if text contains CJK (Chinese, Japanese, Korean) characters.

    Args:
        text: The text to check.

    Returns:
        True if the text contains CJK characters.
    """
    return any(is_cjk_char(char) for char in text)
