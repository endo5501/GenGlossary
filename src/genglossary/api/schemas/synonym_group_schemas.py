"""Schemas for Synonym Groups API."""

from pydantic import BaseModel, Field

from genglossary.models.synonym import SynonymGroup, SynonymMember


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


class SynonymGroupUpdateRequest(BaseModel):
    """Request schema for updating a synonym group's primary term."""

    primary_term_text: str = Field(..., min_length=1, description="New primary term")


class SynonymMemberCreateRequest(BaseModel):
    """Request schema for adding a member to a group."""

    term_text: str = Field(..., min_length=1, description="Term text to add")
