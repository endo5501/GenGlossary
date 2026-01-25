"""API response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from genglossary.models.term import TermOccurrence


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")


class VersionResponse(BaseModel):
    """Version information response."""

    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


class GlossaryTermResponse(BaseModel):
    """Common schema for glossary terms (provisional and refined)."""

    id: int = Field(..., description="Term ID")
    term_name: str = Field(..., description="Term name")
    definition: str = Field(..., description="Term definition")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    occurrences: list[TermOccurrence] = Field(
        ..., description="List of term occurrences"
    )

    @classmethod
    def from_db_row(cls, row: Any) -> "GlossaryTermResponse":
        """Create from database row.

        Args:
            row: Database row (GlossaryTermRow or dict-like) with deserialized occurrences.

        Returns:
            GlossaryTermResponse: Response instance.
        """
        return cls(
            id=row["id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=row["occurrences"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["GlossaryTermResponse"]:
        """Create list from database rows.

        Args:
            rows: List of database rows (GlossaryTermRow or dict-like).

        Returns:
            list[GlossaryTermResponse]: List of response instances.
        """
        return [cls.from_db_row(row) for row in rows]
