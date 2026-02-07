"""Synonym group models for linking related terms."""

from pydantic import BaseModel, field_validator

from genglossary.models.term_validator import validate_term_text


class SynonymMember(BaseModel):
    """Represents a member of a synonym group.

    Attributes:
        id: Unique identifier for the member.
        group_id: ID of the synonym group this member belongs to.
        term_text: The term text of this member.
    """

    id: int
    group_id: int
    term_text: str

    @field_validator("term_text")
    @classmethod
    def validate_term_text_field(cls, v: str) -> str:
        return validate_term_text(v)


class SynonymGroup(BaseModel):
    """Represents a group of synonym terms.

    Attributes:
        id: Unique identifier for the group.
        primary_term_text: The representative term for this group.
        members: List of synonym members in this group.
    """

    id: int
    primary_term_text: str
    members: list[SynonymMember]

    @field_validator("primary_term_text")
    @classmethod
    def validate_primary_term_text_field(cls, v: str) -> str:
        return validate_term_text(v)
