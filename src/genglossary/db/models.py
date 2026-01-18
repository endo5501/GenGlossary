"""Database model serialization and deserialization.

Handles conversion between Pydantic models and JSON strings for database storage.
"""

import json
from typing import TypeVar, TypedDict

from pydantic import BaseModel, TypeAdapter

from genglossary.models.term import TermOccurrence

T = TypeVar("T", bound=BaseModel)


class GlossaryTermRow(TypedDict):
    """Typed dict for glossary term row with deserialized occurrences.

    Used by both provisional and refined term repositories.
    """

    id: int
    run_id: int
    term_name: str
    definition: str
    confidence: float
    occurrences: list[TermOccurrence]


def serialize_occurrences(occurrences: list[TermOccurrence]) -> str:
    """Serialize a list of TermOccurrence objects to JSON string.

    Args:
        occurrences: List of TermOccurrence objects to serialize.

    Returns:
        str: JSON string representation of the occurrences.
    """
    # Convert Pydantic models to dicts
    data = [occ.model_dump() for occ in occurrences]
    # Serialize to JSON with ensure_ascii=False to preserve Unicode
    return json.dumps(data, ensure_ascii=False)


def deserialize_occurrences(json_str: str) -> list[TermOccurrence]:
    """Deserialize JSON string to a list of TermOccurrence objects.

    Args:
        json_str: JSON string to deserialize.

    Returns:
        list[TermOccurrence]: List of TermOccurrence objects.

    Raises:
        ValidationError: If the JSON data doesn't match TermOccurrence schema.
    """
    # Parse JSON
    data = json.loads(json_str)

    # Use TypeAdapter for list validation
    adapter = TypeAdapter(list[TermOccurrence])
    return adapter.validate_python(data)
