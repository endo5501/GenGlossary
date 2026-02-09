"""Schemas for Required Terms API."""

from typing import Literal

from pydantic import Field

from genglossary.api.schemas.term_base_schemas import (
    TermCreateRequestBase,
    TermListResponseBase,
    TermResponseBase,
)
from genglossary.models.required_term import RequiredTerm


class RequiredTermResponse(TermResponseBase):
    """Response schema for a required term."""

    source: Literal["manual"] = Field(..., description="How the term was added")

    @classmethod
    def from_model(cls, model: RequiredTerm) -> "RequiredTermResponse":  # type: ignore[override]
        return cls(
            id=model.id,
            term_text=model.term_text,
            source=model.source,
            created_at=model.created_at,
        )

    @classmethod
    def from_models(cls, models: list[RequiredTerm]) -> list["RequiredTermResponse"]:  # type: ignore[override]
        return [cls.from_model(model) for model in models]


class RequiredTermListResponse(TermListResponseBase[RequiredTermResponse]):
    """Response schema for list of required terms."""

    items: list[RequiredTermResponse] = Field(
        ..., description="List of required terms"
    )


class RequiredTermCreateRequest(TermCreateRequestBase):
    """Request schema for creating a required term."""

    pass
