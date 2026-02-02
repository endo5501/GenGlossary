"""Schemas for Files API."""

from typing import Any

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    """Response schema for a document file (without content)."""

    id: int = Field(..., description="Document ID")
    file_name: str = Field(..., description="File name")
    content_hash: str = Field(..., description="Content hash")

    @classmethod
    def from_db_row(cls, row: Any) -> "FileResponse":
        """Create from database row.

        Args:
            row: Database row (sqlite3.Row or dict-like).

        Returns:
            FileResponse: Response instance.
        """
        return cls(
            id=row["id"],
            file_name=row["file_name"],
            content_hash=row["content_hash"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["FileResponse"]:
        """Create list from database rows.

        Args:
            rows: List of database rows (sqlite3.Row or dict-like).

        Returns:
            list[FileResponse]: List of response instances.
        """
        return [cls.from_db_row(row) for row in rows]


class FileDetailResponse(FileResponse):
    """Response schema for a document file with content.

    Inherits id, file_name, content_hash from FileResponse.
    """

    content: str = Field(..., description="File content")

    @classmethod
    def from_db_row(cls, row: Any) -> "FileDetailResponse":
        """Create from database row.

        Args:
            row: Database row (sqlite3.Row or dict-like).

        Returns:
            FileDetailResponse: Response instance.
        """
        return cls(
            id=row["id"],
            file_name=row["file_name"],
            content_hash=row["content_hash"],
            content=row["content"],
        )


class FileCreateRequest(BaseModel):
    """Request schema for creating a document file with content."""

    file_name: str = Field(..., description="Relative file path (POSIX format, e.g., 'chapter1/intro.md')")
    content: str = Field(..., description="File content")


class FileCreateBulkRequest(BaseModel):
    """Request schema for creating multiple document files."""

    files: list[FileCreateRequest] = Field(
        ..., description="List of files to create"
    )


class DiffScanResponse(BaseModel):
    """Response schema for diff scan operation.

    Note: This is deprecated for GUI mode since files are stored with content in DB.
    """

    added: list[str] = Field(..., description="List of newly added file names")
    modified: list[str] = Field(..., description="List of modified file names")
    deleted: list[str] = Field(..., description="List of deleted file names")
