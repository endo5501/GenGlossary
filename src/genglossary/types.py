"""Common type definitions for genglossary package."""

from collections.abc import Callable

# Type alias for progress callback: (current, total) -> None
ProgressCallback = Callable[[int, int], None]

# Type alias for progress callback with term name: (current, total, term_name) -> None
TermProgressCallback = Callable[[int, int, str], None]
