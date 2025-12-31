"""Document loader for reading documents from files and directories."""

from pathlib import Path

from genglossary.models.document import Document


class DocumentLoader:
    """Loads documents from files and directories.

    Attributes:
        supported_extensions: List of file extensions to load.
    """

    def __init__(
        self,
        supported_extensions: list[str] | None = None,
    ) -> None:
        """Initialize the DocumentLoader.

        Args:
            supported_extensions: List of file extensions to support.
                Defaults to [".txt", ".md"].
        """
        self.supported_extensions = supported_extensions or [".txt", ".md"]

    def load_file(self, path: str) -> Document:
        """Load a single file as a Document.

        Args:
            path: The path to the file.

        Returns:
            A Document object containing the file content.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not supported.
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if file_path.suffix not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file extension: {file_path.suffix}. "
                f"Supported: {self.supported_extensions}"
            )

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
        """
        dir_path = Path(path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        documents: list[Document] = []

        if recursive:
            files = dir_path.rglob("*")
        else:
            files = dir_path.glob("*")

        for file_path in files:
            if file_path.is_file() and file_path.suffix in self.supported_extensions:
                content = file_path.read_text(encoding="utf-8")
                documents.append(
                    Document(file_path=str(file_path), content=content)
                )

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
