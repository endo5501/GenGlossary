"""Schemas for Provisional API."""

from pydantic import BaseModel, Field

from genglossary.models.term import TermOccurrence


class ProvisionalResponse(BaseModel):
    """Response schema for a provisional term."""

    id: int = Field(..., description="Term ID")
    term_name: str = Field(..., description="Term name")
    definition: str = Field(..., description="Term definition")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    occurrences: list[TermOccurrence] = Field(
        ..., description="List of term occurrences"
    )


class ProvisionalUpdateRequest(BaseModel):
    """Request schema for updating a provisional term."""

    definition: str = Field(..., description="New definition")
    confidence: float = Field(..., description="New confidence score (0.0 to 1.0)")
