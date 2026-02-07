"""Schemas for Required Terms API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from genglossary.models.required_term import RequiredTerm


class RequiredTermResponse(BaseModel):
    """Response schema for a required term."""

    id: int = Field(..., description="Required term ID")
    term_text: str = Field(..., description="Term text")
    source: Literal["manual"] = Field(..., description="How the term was added")
    created_at: datetime = Field(..., description="When the term was added")

    @classmethod
    def from_model(cls, model: RequiredTerm) -> "RequiredTermResponse":
        """Create from RequiredTerm model.

        Args:
            model: RequiredTerm model instance.

        Returns:
            RequiredTermResponse: Response instance.
        """
        return cls(
            id=model.id,
            term_text=model.term_text,
            source=model.source,
            created_at=model.created_at,
        )

    @classmethod
    def from_models(cls, models: list[RequiredTerm]) -> list["RequiredTermResponse"]:
        """Create list from RequiredTerm models.

        Args:
            models: List of RequiredTerm model instances.

        Returns:
            list[RequiredTermResponse]: List of response instances.
        """
        return [cls.from_model(model) for model in models]


class RequiredTermListResponse(BaseModel):
    """Response schema for list of required terms."""

    items: list[RequiredTermResponse] = Field(
        ..., description="List of required terms"
    )
    total: int = Field(..., description="Total number of required terms")


class RequiredTermCreateRequest(BaseModel):
    """Request schema for creating a required term."""

    term_text: str = Field(..., description="Term text to require", min_length=1)

    @field_validator("term_text")
    @classmethod
    def validate_term_text(cls, v: str) -> str:
        """Validate and strip term text."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Term text cannot be empty or whitespace only")
        return stripped
