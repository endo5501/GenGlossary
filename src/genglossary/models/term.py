"""Term and TermOccurrence models for representing glossary terms."""

from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_validator


class TermCategory(str, Enum):
    """Category of a term for classification.

    Used in the two-phase LLM classification process.
    COMMON_NOUN is the category that gets filtered out.
    """

    PERSON_NAME = "person_name"
    """Person names - both real and fictional"""

    PLACE_NAME = "place_name"
    """Place names - countries, cities, regions"""

    ORGANIZATION = "organization"
    """Organization and group names - companies, military units, orders"""

    TITLE = "title"
    """Titles and positions - ranks, honorifics"""

    TECHNICAL_TERM = "technical_term"
    """Technical and domain-specific terms"""

    COMMON_NOUN = "common_noun"
    """Common nouns - excluded from glossary"""


class TermOccurrence(BaseModel):
    """Represents a single occurrence of a term in a document.

    Attributes:
        document_path: The path to the document containing this occurrence.
        line_number: The line number where the term appears (1-based).
        context: The surrounding text context for this occurrence.
    """

    document_path: str
    line_number: int = Field(gt=0)
    context: str


class Term(BaseModel):
    """Represents a glossary term with its definition and occurrences.

    Attributes:
        name: The term name.
        definition: The definition of the term.
        occurrences: List of places where the term appears.
        confidence: Confidence score for the definition (0.0 to 1.0).
    """

    name: str
    definition: str = ""
    occurrences: list[TermOccurrence] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize the term name."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Term name cannot be empty")
        return stripped

    @computed_field  # type: ignore[prop-decorator]
    @property
    def occurrence_count(self) -> int:
        """Return the number of occurrences of this term."""
        return len(self.occurrences)

    def add_occurrence(self, occurrence: TermOccurrence) -> None:
        """Add an occurrence to this term.

        Args:
            occurrence: The occurrence to add.
        """
        self.occurrences.append(occurrence)
