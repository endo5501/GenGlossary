"""Schemas for Terms API."""

from pydantic import BaseModel, Field


class TermResponse(BaseModel):
    """Response schema for a term."""

    id: int = Field(..., description="Term ID")
    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")


class TermCreateRequest(BaseModel):
    """Request schema for creating a term."""

    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")


class TermUpdateRequest(BaseModel):
    """Request schema for updating a term."""

    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")
