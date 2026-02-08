"""Schemas for Synonym Groups API."""

from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from genglossary.models.synonym import SynonymGroup, SynonymMember
from genglossary.models.term_validator import validate_term_text


class SynonymMemberResponse(BaseModel):
    """Response schema for a synonym group member."""

    id: int
    group_id: int
    term_text: str

    @classmethod
    def from_model(cls, model: SynonymMember) -> "SynonymMemberResponse":
        return cls(id=model.id, group_id=model.group_id, term_text=model.term_text)


class SynonymGroupResponse(BaseModel):
    """Response schema for a synonym group."""

    id: int
    primary_term_text: str
    members: list[SynonymMemberResponse]

    @classmethod
    def from_model(cls, model: SynonymGroup) -> "SynonymGroupResponse":
        return cls(
            id=model.id,
            primary_term_text=model.primary_term_text,
            members=[SynonymMemberResponse.from_model(m) for m in model.members],
        )

    @classmethod
    def from_models(cls, models: list[SynonymGroup]) -> list["SynonymGroupResponse"]:
        return [cls.from_model(model) for model in models]


class SynonymGroupListResponse(BaseModel):
    """Response schema for list of synonym groups."""

    items: list[SynonymGroupResponse] = Field(..., description="List of synonym groups")
    total: int = Field(..., description="Total number of groups")


class SynonymGroupCreateRequest(BaseModel):
    """Request schema for creating a synonym group."""

    primary_term_text: str = Field(..., min_length=1, description="Representative term")
    member_texts: list[str] = Field(..., min_length=1, description="Member term texts")

    @field_validator("primary_term_text")
    @classmethod
    def validate_primary(cls, v: str) -> str:
        return validate_term_text(v)

    @field_validator("member_texts")
    @classmethod
    def validate_members(cls, v: list[str]) -> list[str]:
        return [validate_term_text(t) for t in v]

    @model_validator(mode="after")
    def validate_primary_in_members(self) -> Self:
        if self.primary_term_text not in self.member_texts:
            raise ValueError(
                "primary_term_text must be included in member_texts"
            )
        return self


class SynonymGroupUpdateRequest(BaseModel):
    """Request schema for updating a synonym group's primary term."""

    primary_term_text: str = Field(..., min_length=1, description="New primary term")

    @field_validator("primary_term_text")
    @classmethod
    def validate_primary(cls, v: str) -> str:
        return validate_term_text(v)


class SynonymMemberCreateRequest(BaseModel):
    """Request schema for adding a member to a group."""

    term_text: str = Field(..., min_length=1, description="Term text to add")

    @field_validator("term_text")
    @classmethod
    def validate_term(cls, v: str) -> str:
        return validate_term_text(v)
