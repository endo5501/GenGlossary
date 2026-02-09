"""Base schemas shared by Excluded Terms and Required Terms APIs."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

from genglossary.models.term_validator import validate_term_text

T = TypeVar("T", bound=BaseModel)


class TermResponseBase(BaseModel):
    """Base response schema for a term (excluded or required)."""

    id: int = Field(..., description="Term ID")
    term_text: str = Field(..., description="Term text")
    source: str = Field(..., description="How the term was added")
    created_at: datetime = Field(..., description="When the term was added")

    @classmethod
    def from_model(cls, model: BaseModel) -> "TermResponseBase":
        """Create from a term model."""
        return cls(
            id=model.id,  # type: ignore[attr-defined]
            term_text=model.term_text,  # type: ignore[attr-defined]
            source=model.source,  # type: ignore[attr-defined]
            created_at=model.created_at,  # type: ignore[attr-defined]
        )

    @classmethod
    def from_models(cls, models: list) -> list["TermResponseBase"]:
        """Create list from term models."""
        return [cls.from_model(model) for model in models]


class TermListResponseBase(BaseModel, Generic[T]):
    """Base response schema for list of terms."""

    items: list[T] = Field(..., description="List of terms")
    total: int = Field(..., description="Total number of terms")


class TermCreateRequestBase(BaseModel):
    """Base request schema for creating a term."""

    term_text: str = Field(..., description="Term text", min_length=1)

    @field_validator("term_text")
    @classmethod
    def validate_term_text_field(cls, v: str) -> str:
        """Validate and strip term text."""
        return validate_term_text(v)
