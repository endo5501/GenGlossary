"""Utility functions for escaping user content in LLM prompts.

This module provides functions to prevent prompt injection attacks
by escaping user-provided content before inclusion in prompts.
"""


def escape_prompt_content(text: str, wrapper_tag: str = "data") -> str:
    """Escape user content for safe prompt inclusion.

    Escapes the wrapper tag (both opening and closing) to prevent
    prompt injection attacks where user content might break out
    of the designated data section.

    Args:
        text: User-provided text to escape.
        wrapper_tag: XML tag name used for wrapping.

    Returns:
        Escaped text safe for prompt inclusion.
    """
    # Escape closing tag first (order matters for nested cases)
    text = text.replace(f"</{wrapper_tag}>", f"&lt;/{wrapper_tag}&gt;")
    text = text.replace(f"<{wrapper_tag}>", f"&lt;{wrapper_tag}&gt;")
    return text


def wrap_user_data(text: str, wrapper_tag: str = "data") -> str:
    """Escape and wrap user data with XML tags for safe prompt inclusion.

    This function first escapes any instances of the wrapper tag within
    the text, then wraps the escaped content with the actual tags.

    Args:
        text: User-provided text to escape and wrap.
        wrapper_tag: XML tag name to use for wrapping.

    Returns:
        Escaped text wrapped in XML tags.
    """
    escaped = escape_prompt_content(text, wrapper_tag)
    return f"<{wrapper_tag}>{escaped}</{wrapper_tag}>"
