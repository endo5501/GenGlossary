"""Document loader for reading documents from files and directories."""

import fnmatch
import os
from pathlib import Path

from genglossary.exceptions import (
    ExcludedFileError,
    FileSizeExceededError,
    PathTraversalError,
)
from genglossary.models.document import Document
from genglossary.utils.path_utils import to_safe_relative_path

# Default patterns for files that should be excluded for security
DEFAULT_EXCLUDED_PATTERNS = [
    ".env",
    ".env.*",
    "credentials*",
    "*.key",
    "*.pem",
    "*.p12",
    "*.pfx",
    "secrets*",
    ".git*",
]

# Default maximum file size (10MB)
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentLoader:
    """Loads documents from files and directories.

    Attributes:
        supported_extensions: List of file extensions to load.
        max_file_size: Maximum file size in bytes (None for unlimited).
        excluded_patterns: List of glob patterns for excluded files.
        validate_path: Whether to validate paths to prevent directory traversal.
    """

    def __init__(
        self,
        supported_extensions: list[str] | None = None,
        max_file_size: int | None = DEFAULT_MAX_FILE_SIZE,
        excluded_patterns: list[str] | None = None,
        validate_path: bool = True,
    ) -> None:
        """Initialize the DocumentLoader.

        Args:
            supported_extensions: List of file extensions to support.
                Defaults to [".txt", ".md"].
            max_file_size: Maximum file size in bytes. Defaults to 10MB.
                Set to None for unlimited.
            excluded_patterns: List of glob patterns for excluded files.
                Defaults to security-sensitive patterns (.env, *.key, etc.).
                Set to [] to disable exclusion.
            validate_path: Whether to validate paths to prevent directory
                traversal attacks. Defaults to True.
        """
        self.supported_extensions = supported_extensions or [".txt", ".md"]
        self.max_file_size = max_file_size
        self.excluded_patterns = (
            excluded_patterns if excluded_patterns is not None
            else DEFAULT_EXCLUDED_PATTERNS
        )
        self.validate_path = validate_path

    def _is_excluded(self, file_path: Path, base_path: Path | None = None) -> str | None:
        """Check if a file or any of its parent directories matches exclusion pattern.

        This checks both the filename and all path components relative to base_path
        to ensure files inside excluded directories (e.g., .git/config) are also excluded.

        Args:
            file_path: The file path to check.
            base_path: Optional base path to check relative path components.

        Returns:
            The matching pattern if excluded, None otherwise.
        """
        # Check filename
        filename = file_path.name
        for pattern in self.excluded_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return pattern

        # Check path components (for excluding entire directories like .git/)
        if base_path:
            try:
                relative_path = file_path.resolve().relative_to(base_path.resolve())
                for part in relative_path.parts:
                    for pattern in self.excluded_patterns:
                        if fnmatch.fnmatch(part, pattern):
                            return pattern
            except ValueError:
                pass

        return None

    def _exceeds_file_size(self, file_path: Path) -> bool:
        """Check if file size exceeds the limit.

        Args:
            file_path: The file path to check.

        Returns:
            True if the file exceeds the limit, False otherwise.
        """
        if self.max_file_size is None:
            return False

        try:
            file_size = file_path.stat().st_size
            return file_size > self.max_file_size
        except OSError:
            return True

    def _check_file_size(self, file_path: Path) -> None:
        """Check if file size is within limits.

        Args:
            file_path: The file path to check.

        Raises:
            FileSizeExceededError: If the file exceeds the size limit.
        """
        if self.max_file_size is None:
            return

        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise FileSizeExceededError(
                str(file_path), file_size, self.max_file_size
            )

    def _validate_path_in_directory(
        self, file_path: Path, base_path: Path
    ) -> None:
        """Validate that file_path is within base_path.

        Uses Path.is_relative_to() after resolving symlinks to detect
        directory traversal attacks.

        Args:
            file_path: The file path to validate.
            base_path: The base directory that should contain the file.

        Raises:
            PathTraversalError: If the file is outside the base directory.
        """
        if not self.validate_path:
            return

        resolved_base = Path(os.path.realpath(base_path))
        resolved_file = Path(os.path.realpath(file_path))

        try:
            resolved_file.relative_to(resolved_base)
        except ValueError:
            raise PathTraversalError(str(file_path), str(base_path))

    def load_file(self, path: str, base_path: str | None = None) -> Document:
        """Load a single file as a Document.

        Args:
            path: The path to the file.
            base_path: Optional base path for path validation.

        Returns:
            A Document object containing the file content.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not supported.
            FileSizeExceededError: If the file exceeds the size limit.
            ExcludedFileError: If the file matches an exclusion pattern.
            PathTraversalError: If the file is outside the base directory.
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if file_path.suffix not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file extension: {file_path.suffix}. "
                f"Supported: {self.supported_extensions}"
            )

        # Check exclusion pattern
        matched_pattern = self._is_excluded(file_path)
        if matched_pattern:
            raise ExcludedFileError(str(file_path), matched_pattern)

        # Check file size
        self._check_file_size(file_path)

        # Validate path if base_path provided
        if base_path:
            self._validate_path_in_directory(file_path, Path(base_path))

        content = file_path.read_text(encoding="utf-8")
        return Document(file_path=str(file_path), content=content)

    def load_directory(
        self,
        path: str,
        recursive: bool = True,
    ) -> list[Document]:
        """Load all supported files from a directory.

        Args:
            path: The path to the directory.
            recursive: Whether to search subdirectories recursively.

        Returns:
            A list of Document objects.

        Raises:
            FileNotFoundError: If the directory does not exist.
            NotADirectoryError: If the path is not a directory.
            PathTraversalError: If any file attempts to escape the directory.
        """
        dir_path = Path(path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        documents: list[Document] = []

        files = dir_path.rglob("*") if recursive else dir_path.glob("*")

        for file_path in files:
            if not file_path.is_file():
                continue

            if file_path.suffix not in self.supported_extensions:
                continue

            # Skip excluded or oversized files silently
            if self._is_excluded(file_path, dir_path):
                continue

            if self._exceeds_file_size(file_path):
                continue

            self._validate_path_in_directory(file_path, dir_path)

            try:
                content = file_path.read_text(encoding="utf-8")
                # Convert to relative path to prevent privacy leaks
                # when file paths are sent to external LLM services
                relative_path = to_safe_relative_path(file_path, dir_path)
                documents.append(
                    Document(file_path=relative_path, content=content)
                )
            except (OSError, UnicodeDecodeError):
                # Skip files that can't be read
                continue
            except ValueError:
                # Skip files outside the directory (e.g., symlinks pointing outside)
                # This is caught from to_safe_relative_path() when the resolved
                # path is not within the base directory
                continue

        return documents

    def load_documents(
        self,
        paths: list[str],
        recursive: bool = True,
    ) -> list[Document]:
        """Load documents from multiple file and directory paths.

        Args:
            paths: List of file and/or directory paths.
            recursive: Whether to search directories recursively.

        Returns:
            A list of Document objects.
        """
        documents: list[Document] = []

        for path in paths:
            path_obj = Path(path)
            if path_obj.is_file():
                documents.append(self.load_file(path))
            elif path_obj.is_dir():
                documents.extend(self.load_directory(path, recursive=recursive))

        return documents
