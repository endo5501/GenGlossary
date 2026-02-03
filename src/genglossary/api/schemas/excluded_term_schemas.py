"""Schemas for Excluded Terms API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from genglossary.models.excluded_term import ExcludedTerm


class ExcludedTermResponse(BaseModel):
    """Response schema for an excluded term."""

    id: int = Field(..., description="Excluded term ID")
    term_text: str = Field(..., description="Term text")
    source: Literal["auto", "manual"] = Field(..., description="How the term was added")
    created_at: datetime = Field(..., description="When the term was added")

    @classmethod
    def from_model(cls, model: ExcludedTerm) -> "ExcludedTermResponse":
        """Create from ExcludedTerm model.

        Args:
            model: ExcludedTerm model instance.

        Returns:
            ExcludedTermResponse: Response instance.
        """
        return cls(
            id=model.id,
            term_text=model.term_text,
            source=model.source,
            created_at=model.created_at,
        )

    @classmethod
    def from_models(cls, models: list[ExcludedTerm]) -> list["ExcludedTermResponse"]:
        """Create list from ExcludedTerm models.

        Args:
            models: List of ExcludedTerm model instances.

        Returns:
            list[ExcludedTermResponse]: List of response instances.
        """
        return [cls.from_model(model) for model in models]


class ExcludedTermListResponse(BaseModel):
    """Response schema for list of excluded terms."""

    items: list[ExcludedTermResponse] = Field(
        ..., description="List of excluded terms"
    )
    total: int = Field(..., description="Total number of excluded terms")


class ExcludedTermCreateRequest(BaseModel):
    """Request schema for creating an excluded term."""

    term_text: str = Field(..., description="Term text to exclude", min_length=1)

    @field_validator("term_text")
    @classmethod
    def validate_term_text(cls, v: str) -> str:
        """Validate and strip term text."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Term text cannot be empty or whitespace only")
        return stripped
