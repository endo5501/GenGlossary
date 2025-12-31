"""Tests for DocumentLoader."""

from pathlib import Path

import pytest

from genglossary.document_loader import DocumentLoader
from genglossary.models.document import Document


class TestDocumentLoader:
    """Test cases for DocumentLoader."""

    def test_supported_extensions_default(self) -> None:
        """Test default supported extensions."""
        loader = DocumentLoader()
        assert ".txt" in loader.supported_extensions
        assert ".md" in loader.supported_extensions

    def test_supported_extensions_custom(self) -> None:
        """Test custom supported extensions."""
        loader = DocumentLoader(supported_extensions=[".rst", ".adoc"])
        assert ".rst" in loader.supported_extensions
        assert ".adoc" in loader.supported_extensions
        assert ".txt" not in loader.supported_extensions

    def test_load_file_txt(self, tmp_path: Path) -> None:
        """Test loading a .txt file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3")

        loader = DocumentLoader()
        doc = loader.load_file(str(file_path))

        assert isinstance(doc, Document)
        assert doc.file_path == str(file_path)
        assert doc.content == "Line 1\nLine 2\nLine 3"
        assert doc.lines == ["Line 1", "Line 2", "Line 3"]

    def test_load_file_md(self, tmp_path: Path) -> None:
        """Test loading a .md file."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Header\n\nParagraph text.")

        loader = DocumentLoader()
        doc = loader.load_file(str(file_path))

        assert isinstance(doc, Document)
        assert doc.content == "# Header\n\nParagraph text."

    def test_load_file_not_found(self) -> None:
        """Test loading a non-existent file raises error."""
        loader = DocumentLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_file("/nonexistent/path/file.txt")

    def test_load_file_unsupported_extension(self, tmp_path: Path) -> None:
        """Test loading a file with unsupported extension raises error."""
        file_path = tmp_path / "test.py"
        file_path.write_text("print('hello')")

        loader = DocumentLoader()
        with pytest.raises(ValueError, match="Unsupported file extension"):
            loader.load_file(str(file_path))

    def test_load_file_empty(self, tmp_path: Path) -> None:
        """Test loading an empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")

        loader = DocumentLoader()
        doc = loader.load_file(str(file_path))

        assert doc.content == ""
        assert doc.lines == [""]

    def test_load_file_with_encoding(self, tmp_path: Path) -> None:
        """Test loading a file with specific encoding."""
        file_path = tmp_path / "test.txt"
        content = "日本語テキスト"
        file_path.write_text(content, encoding="utf-8")

        loader = DocumentLoader()
        doc = loader.load_file(str(file_path))

        assert doc.content == content

    def test_load_directory_single_file(self, tmp_path: Path) -> None:
        """Test loading a directory with a single file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Content")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].content == "Content"

    def test_load_directory_multiple_files(self, tmp_path: Path) -> None:
        """Test loading a directory with multiple files."""
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "file2.md").write_text("Content 2")
        (tmp_path / "file3.txt").write_text("Content 3")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 3
        contents = {doc.content for doc in docs}
        assert contents == {"Content 1", "Content 2", "Content 3"}

    def test_load_directory_filters_by_extension(self, tmp_path: Path) -> None:
        """Test that directory loading filters by supported extensions."""
        (tmp_path / "included.txt").write_text("Included")
        (tmp_path / "included.md").write_text("Also included")
        (tmp_path / "excluded.py").write_text("Excluded")
        (tmp_path / "excluded.json").write_text("{}")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 2
        file_paths = {doc.file_path for doc in docs}
        assert any("included.txt" in path for path in file_paths)
        assert any("included.md" in path for path in file_paths)

    def test_load_directory_recursive(self, tmp_path: Path) -> None:
        """Test recursive directory loading."""
        # Create subdirectory structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.txt").write_text("Root content")
        (subdir / "sub.txt").write_text("Sub content")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path), recursive=True)

        assert len(docs) == 2
        contents = {doc.content for doc in docs}
        assert contents == {"Root content", "Sub content"}

    def test_load_directory_non_recursive(self, tmp_path: Path) -> None:
        """Test non-recursive directory loading."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.txt").write_text("Root content")
        (subdir / "sub.txt").write_text("Sub content")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path), recursive=False)

        assert len(docs) == 1
        assert docs[0].content == "Root content"

    def test_load_directory_empty(self, tmp_path: Path) -> None:
        """Test loading an empty directory."""
        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 0

    def test_load_directory_not_found(self) -> None:
        """Test loading a non-existent directory raises error."""
        loader = DocumentLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_directory("/nonexistent/directory")

    def test_load_directory_is_file(self, tmp_path: Path) -> None:
        """Test loading a file path as directory raises error."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("Content")

        loader = DocumentLoader()
        with pytest.raises(NotADirectoryError):
            loader.load_directory(str(file_path))

    def test_load_documents_mixed_paths(self, tmp_path: Path) -> None:
        """Test loading from mixed file and directory paths."""
        # Create directory with files
        subdir = tmp_path / "docs"
        subdir.mkdir()
        (subdir / "doc1.txt").write_text("Doc 1")
        (subdir / "doc2.txt").write_text("Doc 2")

        # Create standalone file
        single_file = tmp_path / "single.txt"
        single_file.write_text("Single")

        loader = DocumentLoader()
        docs = loader.load_documents([str(single_file), str(subdir)])

        assert len(docs) == 3
        contents = {doc.content for doc in docs}
        assert contents == {"Doc 1", "Doc 2", "Single"}

    def test_load_documents_empty_list(self) -> None:
        """Test loading with empty paths list."""
        loader = DocumentLoader()
        docs = loader.load_documents([])

        assert len(docs) == 0

    def test_load_documents_recursive(self, tmp_path: Path) -> None:
        """Test load_documents with recursive option."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.txt").write_text("Root")
        (subdir / "nested.txt").write_text("Nested")

        loader = DocumentLoader()
        docs = loader.load_documents([str(tmp_path)], recursive=True)

        assert len(docs) == 2
