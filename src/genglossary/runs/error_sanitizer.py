"""Sanitize error messages before DB persistence and API exposure."""

import re

# Paths that indicate sensitive filesystem locations (2+ segments required)
_UNIX_PATH_PREFIXES = r"/(?:home|Users|var|tmp|etc|opt)"
_WINDOWS_PATH_PREFIX = r"[A-Z]:"

# Match filesystem paths with 2+ segments, but not URLs
_PATH_PATTERN = re.compile(
    rf"(?<!:/)(?<!://)(?:{_UNIX_PATH_PREFIXES}|{_WINDOWS_PATH_PREFIX})(?:[/\\]\S+)+"
)

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
    1. Empty message fallback to exception class name
    2. UTF-8 normalization
    3. Control character removal (preserving newline/tab)
    4. Sensitive path masking
    5. Length truncation

    Args:
        error: The exception to sanitize.
        prefix: Optional prefix (e.g. "Failed to start execution thread").
        max_length: Maximum length of the result (default: 1024).

    Returns:
        Sanitized error message string.
    """
    class_name = type(error).__name__
    raw_msg = str(error)

    # 1. Empty message fallback
    if not raw_msg.strip():
        msg = ""
    else:
        msg = raw_msg

    # 2. UTF-8 normalization
    if msg:
        msg = msg.encode("utf-8", "replace").decode("utf-8")

    # 3. Control character removal
    if msg:
        msg = _CONTROL_CHAR_PATTERN.sub("", msg)

    # 4. Path masking
    if msg:
        msg = _mask_paths(msg)

    # 5. Format with prefix and class name
    if prefix and msg:
        formatted = f"{prefix}: {msg} ({class_name})"
    elif prefix:
        formatted = f"{prefix} ({class_name})"
    elif msg:
        formatted = f"{msg} ({class_name})"
    else:
        formatted = class_name

    # 6. Length truncation
    if len(formatted) > max_length:
        formatted = formatted[: max_length - len(_TRUNCATION_SUFFIX)] + _TRUNCATION_SUFFIX

    return formatted


def _mask_paths(msg: str) -> str:
    """Mask sensitive filesystem paths in the message.

    Replaces Unix paths (/home/..., /Users/..., etc.) and Windows paths
    (C:\\..., D:\\...) with '<path>'. URLs (http://, https://) are preserved.

    Args:
        msg: Message to process.

    Returns:
        Message with paths masked.
    """
    return _PATH_PATTERN.sub("<path>", msg)
