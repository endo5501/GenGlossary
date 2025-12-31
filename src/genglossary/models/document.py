"""Document model for representing loaded documents."""

from pydantic import BaseModel, computed_field


class Document(BaseModel):
    """Represents a loaded document with its content and metadata.

    Attributes:
        file_path: The path to the source file.
        content: The full text content of the document.
    """

    file_path: str
    content: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def lines(self) -> list[str]:
        """Split content into lines."""
        return self.content.split("\n")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_count(self) -> int:
        """Return the number of lines in the document."""
        return len(self.lines)

    def get_line(self, line_number: int) -> str:
        """Get a specific line by line number (1-based).

        Args:
            line_number: The line number (1-based index).

        Returns:
            The content of the specified line.

        Raises:
            IndexError: If line_number is out of range.
        """
        if line_number < 1 or line_number > self.line_count:
            raise IndexError(
                f"Line number {line_number} out of range (1-{self.line_count})"
            )
        return self.lines[line_number - 1]

    def get_context(self, line_number: int, context_lines: int = 1) -> list[str]:
        """Get a line with surrounding context.

        Args:
            line_number: The center line number (1-based index).
            context_lines: Number of lines to include before and after.

        Returns:
            A list of lines including the specified line and its context.

        Raises:
            IndexError: If line_number is out of range.
        """
        if line_number < 1 or line_number > self.line_count:
            raise IndexError(
                f"Line number {line_number} out of range (1-{self.line_count})"
            )

        start = max(0, line_number - 1 - context_lines)
        end = min(self.line_count, line_number + context_lines)
        return self.lines[start:end]
