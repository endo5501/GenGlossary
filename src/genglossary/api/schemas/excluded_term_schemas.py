"""Schemas for Excluded Terms API."""

from typing import Literal

from pydantic import Field

from genglossary.api.schemas.term_base_schemas import (
    TermCreateRequestBase,
    TermListResponseBase,
    TermResponseBase,
)
from genglossary.models.excluded_term import ExcludedTerm


class ExcludedTermResponse(TermResponseBase):
    """Response schema for an excluded term."""

    source: Literal["auto", "manual"] = Field(..., description="How the term was added")

    @classmethod
    def from_model(cls, model: ExcludedTerm) -> "ExcludedTermResponse":  # type: ignore[override]
        return cls(
            id=model.id,
            term_text=model.term_text,
            source=model.source,
            created_at=model.created_at,
        )

    @classmethod
    def from_models(cls, models: list[ExcludedTerm]) -> list["ExcludedTermResponse"]:  # type: ignore[override]
        return [cls.from_model(model) for model in models]


class ExcludedTermListResponse(TermListResponseBase[ExcludedTermResponse]):
    """Response schema for list of excluded terms."""

    items: list[ExcludedTermResponse] = Field(
        ..., description="List of excluded terms"
    )


class ExcludedTermCreateRequest(TermCreateRequestBase):
    """Request schema for creating an excluded term."""

    pass
