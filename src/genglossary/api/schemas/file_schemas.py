"""Schemas for Files API."""

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    """Response schema for a document file."""

    id: int = Field(..., description="Document ID")
    file_path: str = Field(..., description="File path")
    content_hash: str = Field(..., description="Content hash")


class FileCreateRequest(BaseModel):
    """Request schema for creating a document file."""

    file_path: str = Field(..., description="File path relative to doc_root")


class DiffScanResponse(BaseModel):
    """Response schema for diff scan operation."""

    added: list[str] = Field(..., description="List of newly added file paths")
    modified: list[str] = Field(..., description="List of modified file paths")
    deleted: list[str] = Field(..., description="List of deleted file paths")
