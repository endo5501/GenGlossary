"""Custom exceptions for GenGlossary."""


class GenGlossaryError(Exception):
    """Base exception for GenGlossary."""


class FileSizeExceededError(GenGlossaryError):
    """Raised when a file exceeds the maximum allowed size."""

    def __init__(self, file_path: str, file_size: int, max_size: int) -> None:
        """Initialize FileSizeExceededError.

        Args:
            file_path: Path to the file that exceeded the limit.
            file_size: Actual file size in bytes.
            max_size: Maximum allowed size in bytes.
        """
        self.file_path = file_path
        self.file_size = file_size
        self.max_size = max_size
        super().__init__(
            f"File size {file_size} bytes exceeds limit {max_size} bytes: {file_path}"
        )


class PathTraversalError(GenGlossaryError):
    """Raised when a path attempts to escape the allowed directory."""

    def __init__(self, file_path: str, base_path: str) -> None:
        """Initialize PathTraversalError.

        Args:
            file_path: Path that attempted to escape.
            base_path: The base directory that should contain the file.
        """
        self.file_path = file_path
        self.base_path = base_path
        super().__init__(
            f"Path '{file_path}' is outside the allowed directory '{base_path}'"
        )


class ExcludedFileError(GenGlossaryError):
    """Raised when attempting to load an excluded file."""

    def __init__(self, file_path: str, pattern: str) -> None:
        """Initialize ExcludedFileError.

        Args:
            file_path: Path to the excluded file.
            pattern: The exclusion pattern that matched.
        """
        self.file_path = file_path
        self.pattern = pattern
        super().__init__(f"File '{file_path}' is excluded by pattern '{pattern}'")
