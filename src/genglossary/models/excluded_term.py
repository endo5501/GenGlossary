"""ExcludedTerm model for representing excluded terms from glossary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class ExcludedTerm(BaseModel):
    """Represents an excluded term that should be skipped during extraction.

    Excluded terms are either:
    - Automatically added when LLM classifies a term as common_noun
    - Manually added by the user

    Attributes:
        id: Unique identifier for the excluded term.
        term_text: The term text to exclude.
        source: How the term was added ('auto' for LLM classification, 'manual' for user).
        created_at: Timestamp when the term was added to the exclusion list.
    """

    id: int
    term_text: str
    source: Literal["auto", "manual"]
    created_at: datetime

    @field_validator("term_text")
    @classmethod
    def validate_term_text(cls, v: str) -> str:
        """Validate and normalize the term text.

        Args:
            v: The term text to validate.

        Returns:
            The validated and stripped term text.

        Raises:
            ValueError: If the term text is empty or contains only whitespace.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Term text cannot be empty")
        return stripped
