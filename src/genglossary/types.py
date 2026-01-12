"""Common type definitions for genglossary package."""

from collections.abc import Callable

# Type alias for progress callback: (current, total) -> None
ProgressCallback = Callable[[int, int], None]
