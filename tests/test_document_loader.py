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


class TestDocumentLoaderValidation:
    """Test cases for DocumentLoader validation features."""

    # ===== File Size Limit Tests =====

    def test_max_file_size_default(self) -> None:
        """Test default max file size is 10MB."""
        loader = DocumentLoader()
        assert loader.max_file_size == 10 * 1024 * 1024

    def test_max_file_size_custom(self) -> None:
        """Test custom max file size."""
        loader = DocumentLoader(max_file_size=1024)
        assert loader.max_file_size == 1024

    def test_max_file_size_none_means_unlimited(self) -> None:
        """Test max_file_size=None means no limit."""
        loader = DocumentLoader(max_file_size=None)
        assert loader.max_file_size is None

    def test_load_file_exceeds_max_size(self, tmp_path: Path) -> None:
        """Test loading a file that exceeds max size raises error."""
        from genglossary.exceptions import FileSizeExceededError

        file_path = tmp_path / "large.txt"
        file_path.write_text("x" * 2000)  # 2000 bytes

        loader = DocumentLoader(max_file_size=1000)
        with pytest.raises(FileSizeExceededError, match="File size .* exceeds limit"):
            loader.load_file(str(file_path))

    def test_load_file_within_max_size(self, tmp_path: Path) -> None:
        """Test loading a file within max size succeeds."""
        file_path = tmp_path / "small.txt"
        file_path.write_text("x" * 500)

        loader = DocumentLoader(max_file_size=1000)
        doc = loader.load_file(str(file_path))
        assert len(doc.content) == 500

    def test_load_file_unlimited_size(self, tmp_path: Path) -> None:
        """Test loading large file with unlimited size."""
        file_path = tmp_path / "large.txt"
        file_path.write_text("x" * 100000)

        loader = DocumentLoader(max_file_size=None)
        doc = loader.load_file(str(file_path))
        assert len(doc.content) == 100000

    def test_load_directory_skips_large_files(self, tmp_path: Path) -> None:
        """Test directory loading skips files exceeding size limit."""
        (tmp_path / "small.txt").write_text("x" * 100)
        (tmp_path / "large.txt").write_text("x" * 2000)

        loader = DocumentLoader(max_file_size=1000)
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("small.txt")

    # ===== Path Traversal Prevention Tests =====

    def test_validate_path_default_enabled(self) -> None:
        """Test path validation is enabled by default."""
        loader = DocumentLoader()
        assert loader.validate_path is True

    def test_validate_path_disabled(self) -> None:
        """Test path validation can be disabled."""
        loader = DocumentLoader(validate_path=False)
        assert loader.validate_path is False

    def test_load_directory_blocks_symlink_escape(self, tmp_path: Path) -> None:
        """Test symlink pointing outside directory is blocked."""
        from genglossary.exceptions import PathTraversalError

        # Create a file outside the directory
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret content")

        # Create doc directory with symlink pointing outside
        doc_dir = tmp_path / "docs"
        doc_dir.mkdir()
        symlink = doc_dir / "link.txt"
        symlink.symlink_to(outside_file)

        loader = DocumentLoader()
        with pytest.raises(PathTraversalError, match="outside.*directory"):
            loader.load_directory(str(doc_dir))

    def test_load_directory_allows_internal_symlink(self, tmp_path: Path) -> None:
        """Test symlink within directory is allowed."""
        (tmp_path / "original.txt").write_text("content")
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(tmp_path / "original.txt")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        # Both original and symlink should be loaded
        assert len(docs) >= 1

    def test_load_directory_validate_path_disabled_allows_escape(
        self, tmp_path: Path
    ) -> None:
        """Test symlink escape is allowed when validation is disabled."""
        # Create a file outside the directory
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret content")

        # Create doc directory with symlink pointing outside
        doc_dir = tmp_path / "docs"
        doc_dir.mkdir()
        symlink = doc_dir / "link.txt"
        symlink.symlink_to(outside_file)

        loader = DocumentLoader(validate_path=False)
        docs = loader.load_directory(str(doc_dir))

        assert len(docs) == 1
        assert docs[0].content == "secret content"

    # ===== Excluded File Pattern Tests =====

    def test_excluded_patterns_default(self) -> None:
        """Test default excluded patterns include sensitive files."""
        loader = DocumentLoader()
        assert ".env" in loader.excluded_patterns
        assert "*.key" in loader.excluded_patterns
        assert "*.pem" in loader.excluded_patterns

    def test_excluded_patterns_custom(self) -> None:
        """Test custom excluded patterns."""
        loader = DocumentLoader(excluded_patterns=["*.secret", "private*"])
        assert "*.secret" in loader.excluded_patterns
        assert "private*" in loader.excluded_patterns
        assert ".env" not in loader.excluded_patterns

    def test_excluded_patterns_empty_disables_exclusion(self) -> None:
        """Test empty excluded patterns list disables file exclusion."""
        loader = DocumentLoader(excluded_patterns=[])
        assert loader.excluded_patterns == []

    def test_load_directory_excludes_env_file(self, tmp_path: Path) -> None:
        """Test .env file is excluded by default."""
        (tmp_path / ".env").write_text("SECRET=value")
        (tmp_path / "readme.txt").write_text("readme")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("readme.txt")

    def test_load_directory_excludes_key_file(self, tmp_path: Path) -> None:
        """Test *.key file is excluded by default."""
        (tmp_path / "server.key").write_text("private key")
        (tmp_path / "readme.txt").write_text("readme")

        # Add .key to supported extensions to test exclusion
        loader = DocumentLoader(supported_extensions=[".txt", ".key"])
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("readme.txt")

    def test_load_directory_excludes_credentials_file(self, tmp_path: Path) -> None:
        """Test credentials* file is excluded by default."""
        (tmp_path / "credentials.txt").write_text("user:pass")
        (tmp_path / "readme.txt").write_text("readme")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("readme.txt")

    def test_load_directory_excludes_env_variants(self, tmp_path: Path) -> None:
        """Test .env.* variants are excluded."""
        (tmp_path / ".env.local").write_text("LOCAL=1")
        (tmp_path / ".env.production").write_text("PROD=1")
        (tmp_path / "readme.txt").write_text("readme")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("readme.txt")

    def test_load_directory_excludes_files_in_git_directory(
        self, tmp_path: Path
    ) -> None:
        """Test files inside .git directory are excluded."""
        # Create .git directory with files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config content")
        (git_dir / "HEAD").write_text("ref: refs/heads/main")

        # Create normal files
        (tmp_path / "readme.txt").write_text("readme")

        # Support files without extension to test exclusion
        loader = DocumentLoader(supported_extensions=[".txt", ""])
        docs = loader.load_directory(str(tmp_path))

        # Only readme.txt should be loaded, .git/* should be excluded
        assert len(docs) == 1
        assert docs[0].file_path.endswith("readme.txt")

    def test_load_directory_excludes_files_in_nested_excluded_dir(
        self, tmp_path: Path
    ) -> None:
        """Test files inside nested excluded directories are excluded."""
        # Create deeply nested .git directory
        nested = tmp_path / "subdir" / ".git" / "objects"
        nested.mkdir(parents=True)
        (nested / "abc123").write_text("pack content")

        # Create normal file
        (tmp_path / "readme.txt").write_text("readme")

        loader = DocumentLoader(supported_extensions=[".txt", ""])
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("readme.txt")

    def test_load_file_raises_for_excluded_file(self, tmp_path: Path) -> None:
        """Test load_file raises error for excluded file."""
        from genglossary.exceptions import ExcludedFileError

        # Create .env file but with .txt extension for supported_extensions check
        # Actually, .env doesn't have .txt extension, so we need to add it
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=value")

        # We need to add no extension or use a pattern that matches
        loader = DocumentLoader(supported_extensions=["", ".env"])
        with pytest.raises(ExcludedFileError, match="excluded"):
            loader.load_file(str(env_file))

    def test_load_directory_custom_exclusion_pattern(self, tmp_path: Path) -> None:
        """Test custom exclusion pattern works."""
        (tmp_path / "public.txt").write_text("public")
        (tmp_path / "private_data.txt").write_text("private")

        loader = DocumentLoader(excluded_patterns=["private*"])
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("public.txt")

    def test_load_directory_no_exclusion(self, tmp_path: Path) -> None:
        """Test loading with no exclusion patterns."""
        (tmp_path / ".env").write_text("SECRET=value")
        (tmp_path / "readme.txt").write_text("readme")

        # Empty exclusions and add empty extension support
        loader = DocumentLoader(
            supported_extensions=[".txt", ""],
            excluded_patterns=[]
        )
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 2

    # ===== Combined Validation Tests =====

    def test_all_validations_applied(self, tmp_path: Path) -> None:
        """Test all validations are applied together."""
        # Create various files
        (tmp_path / "valid.txt").write_text("valid content")
        (tmp_path / ".env").write_text("SECRET=value")  # excluded
        (tmp_path / "large.txt").write_text("x" * 10000)  # too large

        loader = DocumentLoader(
            max_file_size=1000,
            excluded_patterns=[".env"],
        )
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].file_path.endswith("valid.txt")
