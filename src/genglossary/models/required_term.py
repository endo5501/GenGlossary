"""RequiredTerm model for representing required terms in glossary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from genglossary.models.term_validator import validate_term_text


class RequiredTerm(BaseModel):
    """Represents a required term that must always appear in the glossary.

    Required terms are manually added by the user to ensure they always
    appear in the term list, regardless of SudachiPy analysis or LLM
    classification results.

    Attributes:
        id: Unique identifier for the required term.
        term_text: The term text to always include.
        source: How the term was added (currently 'manual' only).
        created_at: Timestamp when the term was added to the required list.
    """

    id: int
    term_text: str
    source: Literal["manual"]
    created_at: datetime

    @field_validator("term_text")
    @classmethod
    def validate_term_text_field(cls, v: str) -> str:
        return validate_term_text(v)
