"""Schemas for Refined API."""

from pydantic import BaseModel, Field

from genglossary.models.term import TermOccurrence


class RefinedResponse(BaseModel):
    """Response schema for a refined term."""

    id: int = Field(..., description="Term ID")
    term_name: str = Field(..., description="Term name")
    definition: str = Field(..., description="Term definition")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    occurrences: list[TermOccurrence] = Field(
        ..., description="List of term occurrences"
    )
