"""Schemas for Files API."""

from typing import Any

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    """Response schema for a document file."""

    id: int = Field(..., description="Document ID")
    file_path: str = Field(..., description="File path")
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
            file_path=row["file_path"],
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


class FileCreateRequest(BaseModel):
    """Request schema for creating a document file."""

    file_path: str = Field(..., description="File path relative to doc_root")


class DiffScanResponse(BaseModel):
    """Response schema for diff scan operation."""

    added: list[str] = Field(..., description="List of newly added file paths")
    modified: list[str] = Field(..., description="List of modified file paths")
    deleted: list[str] = Field(..., description="List of deleted file paths")
