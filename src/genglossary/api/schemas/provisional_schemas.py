"""Schemas for Provisional API."""

from pydantic import BaseModel, Field

from genglossary.api.schemas.common import GlossaryTermResponse

# Use common glossary term response schema
ProvisionalResponse = GlossaryTermResponse


class ProvisionalUpdateRequest(BaseModel):
    """Request schema for updating a provisional term."""

    definition: str = Field(..., description="New definition")
    confidence: float = Field(..., description="New confidence score (0.0 to 1.0)")
