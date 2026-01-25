"""API schemas."""

from genglossary.api.schemas.common import HealthResponse, VersionResponse
from genglossary.api.schemas.term_schemas import (
    TermCreateRequest,
    TermResponse,
    TermUpdateRequest,
)

__all__ = [
    "HealthResponse",
    "VersionResponse",
    "TermResponse",
    "TermCreateRequest",
    "TermUpdateRequest",
]
