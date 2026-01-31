"""Utility functions for escaping user content in LLM prompts.

This module provides functions to prevent prompt injection attacks
by escaping user-provided content before inclusion in prompts.
"""


def escape_prompt_content(text: str, wrapper_tag: str = "data") -> str:
    """Escape user content for safe prompt inclusion.

    Args:
        text: User-provided text to escape.
        wrapper_tag: XML tag name used for wrapping.

    Returns:
        Escaped text safe for prompt inclusion.
    """
    raise NotImplementedError()


def wrap_user_data(text: str, wrapper_tag: str = "data") -> str:
    """Escape and wrap user data with XML tags for safe prompt inclusion.

    Args:
        text: User-provided text to escape and wrap.
        wrapper_tag: XML tag name to use for wrapping.

    Returns:
        Escaped text wrapped in XML tags.
    """
    raise NotImplementedError()
