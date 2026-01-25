"""Schemas for Terms API."""

from typing import Any

from pydantic import BaseModel, Field


class TermResponse(BaseModel):
    """Response schema for a term."""

    id: int = Field(..., description="Term ID")
    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")

    @classmethod
    def from_db_row(cls, row: Any) -> "TermResponse":
        """Create from database row.

        Args:
            row: Database row (sqlite3.Row or dict-like).

        Returns:
            TermResponse: Response instance.
        """
        return cls(
            id=row["id"],
            term_text=row["term_text"],
            category=row["category"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["TermResponse"]:
        """Create list from database rows.

        Args:
            rows: List of database rows (sqlite3.Row or dict-like).

        Returns:
            list[TermResponse]: List of response instances.
        """
        return [cls.from_db_row(row) for row in rows]


class TermMutationRequest(BaseModel):
    """Request schema for creating or updating a term."""

    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")


# Aliases for clarity
TermCreateRequest = TermMutationRequest
TermUpdateRequest = TermMutationRequest
