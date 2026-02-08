"""Sanitize error messages before DB persistence and API exposure."""

import re

# Paths that indicate sensitive filesystem locations (2+ segments required)
_UNIX_PATH_PREFIXES = r"/(?:home|Users|var|tmp|etc|opt)"
_WINDOWS_PATH_PREFIX = r"[A-Za-z]:"

# URL pattern to match and preserve HTTP/HTTPS URLs
_URL_PATTERN = r"https?://\S+"

# Path pattern for sensitive filesystem paths (2+ segments)
_PATH_ONLY = rf"(?:{_UNIX_PATH_PREFIXES}|{_WINDOWS_PATH_PREFIX})(?:[/\\]\S+)+"

# Combined pattern: URLs matched first (preserved), then paths (masked)
_COMBINED_PATTERN = re.compile(rf"(?P<url>{_URL_PATTERN})|(?P<path>{_PATH_ONLY})")

# Control characters except \n (0x0a) and \t (0x09)
_CONTROL_CHAR_PATTERN = re.compile(
    r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]"
)

_TRUNCATION_SUFFIX = "...(truncated)"


def sanitize_error_message(
    error: Exception,
    prefix: str | None = None,
    max_length: int = 1024,
) -> str:
    """Sanitize an exception into a safe error message string.

    Processing order:
    1. Extract and sanitize message text
    2. Format with prefix and class name
    3. Length truncation

    Args:
        error: The exception to sanitize.
        prefix: Optional prefix (e.g. "Failed to start execution thread").
        max_length: Maximum length of the result (default: 1024).

    Returns:
        Sanitized error message string.
    """
    class_name = type(error).__name__
    msg = str(error)

    # Sanitize message (all operations are safe for empty strings)
    msg = msg.encode("utf-8", "replace").decode("utf-8")
    msg = _CONTROL_CHAR_PATTERN.sub("", msg)
    msg = _mask_paths(msg)
    msg = msg.strip()

    # Format with prefix and class name
    if prefix and msg:
        formatted = f"{prefix}: {msg} ({class_name})"
    elif prefix:
        formatted = f"{prefix} ({class_name})"
    elif msg:
        formatted = f"{msg} ({class_name})"
    else:
        formatted = class_name

    # Length truncation
    if len(formatted) > max_length:
        if max_length <= len(_TRUNCATION_SUFFIX):
            formatted = formatted[:max_length]
        else:
            formatted = formatted[: max_length - len(_TRUNCATION_SUFFIX)] + _TRUNCATION_SUFFIX

    return formatted


def _mask_paths(msg: str) -> str:
    """Mask sensitive filesystem paths in the message.

    Uses alternation to match URLs first (preserved) then filesystem paths
    (masked). This prevents path patterns inside URLs from being masked.

    Args:
        msg: Message to process.

    Returns:
        Message with paths masked.
    """

    def _replacer(match: re.Match) -> str:  # type: ignore[type-arg]
        if match.group("url"):
            return match.group("url")
        return "<path>"

    return _COMBINED_PATTERN.sub(_replacer, msg)
