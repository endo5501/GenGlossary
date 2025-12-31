"""Tests for Document model."""

import pytest

from genglossary.models.document import Document


class TestDocument:
    """Test cases for Document model."""

    def test_create_document(self) -> None:
        """Test creating a Document with file_path and content."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3",
        )
        assert doc.file_path == "/path/to/file.txt"
        assert doc.content == "Line 1\nLine 2\nLine 3"

    def test_lines_property(self) -> None:
        """Test that lines property returns content split by newlines."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="First line\nSecond line\nThird line",
        )
        assert doc.lines == ["First line", "Second line", "Third line"]

    def test_lines_property_empty_content(self) -> None:
        """Test lines property with empty content."""
        doc = Document(file_path="/path/to/file.txt", content="")
        assert doc.lines == [""]

    def test_lines_property_single_line(self) -> None:
        """Test lines property with single line (no newlines)."""
        doc = Document(file_path="/path/to/file.txt", content="Single line")
        assert doc.lines == ["Single line"]

    def test_get_line_valid_index(self) -> None:
        """Test get_line with valid line number (1-based)."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3",
        )
        assert doc.get_line(1) == "Line 1"
        assert doc.get_line(2) == "Line 2"
        assert doc.get_line(3) == "Line 3"

    def test_get_line_invalid_index_zero(self) -> None:
        """Test get_line with line number 0 raises error."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2",
        )
        with pytest.raises(IndexError):
            doc.get_line(0)

    def test_get_line_invalid_index_negative(self) -> None:
        """Test get_line with negative line number raises error."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2",
        )
        with pytest.raises(IndexError):
            doc.get_line(-1)

    def test_get_line_invalid_index_too_large(self) -> None:
        """Test get_line with line number exceeding content raises error."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2",
        )
        with pytest.raises(IndexError):
            doc.get_line(3)

    def test_get_context_default(self) -> None:
        """Test get_context with default context_lines (1 line before/after)."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        )
        context = doc.get_context(3)
        assert context == ["Line 2", "Line 3", "Line 4"]

    def test_get_context_custom_lines(self) -> None:
        """Test get_context with custom context_lines."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        )
        context = doc.get_context(3, context_lines=2)
        assert context == ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]

    def test_get_context_at_start(self) -> None:
        """Test get_context at the start of document."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        )
        context = doc.get_context(1)
        assert context == ["Line 1", "Line 2"]

    def test_get_context_at_end(self) -> None:
        """Test get_context at the end of document."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        )
        context = doc.get_context(5)
        assert context == ["Line 4", "Line 5"]

    def test_get_context_invalid_line_number(self) -> None:
        """Test get_context with invalid line number raises error."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2",
        )
        with pytest.raises(IndexError):
            doc.get_context(0)
        with pytest.raises(IndexError):
            doc.get_context(3)

    def test_get_context_zero_context_lines(self) -> None:
        """Test get_context with zero context_lines returns just the line."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3",
        )
        context = doc.get_context(2, context_lines=0)
        assert context == ["Line 2"]

    def test_line_count_property(self) -> None:
        """Test line_count property returns correct count."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3",
        )
        assert doc.line_count == 3

    def test_line_count_empty_document(self) -> None:
        """Test line_count for empty document."""
        doc = Document(file_path="/path/to/file.txt", content="")
        assert doc.line_count == 1  # Empty string splits to [""]
