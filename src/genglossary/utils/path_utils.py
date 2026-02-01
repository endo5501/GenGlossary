"""Path utilities for secure file operations."""

from pathlib import Path


def to_safe_relative_path(file_path: Path | str, root: Path | str) -> str:
    """Convert file path to safe relative path in POSIX format.

    This function:
    1. Resolves both paths to absolute paths
    2. Validates that file_path is within root (prevents path traversal)
    3. Converts to relative path
    4. Returns in POSIX format (forward slashes)

    Args:
        file_path: Target file path (absolute or relative).
        root: Root directory path.

    Returns:
        Relative path in POSIX format (using /).

    Raises:
        ValueError: If file is outside root directory.
    """
    resolved_file = Path(file_path).resolve()
    resolved_root = Path(root).resolve()

    if not resolved_file.is_relative_to(resolved_root):
        # Don't include the absolute path in error message to prevent leakage
        raise ValueError("Path is outside root directory")

    return resolved_file.relative_to(resolved_root).as_posix()
