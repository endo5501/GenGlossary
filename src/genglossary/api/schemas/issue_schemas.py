"""Schemas for Issues API."""

from typing import Any

from pydantic import BaseModel, Field


class IssueResponse(BaseModel):
    """Response schema for a glossary issue."""

    id: int = Field(..., description="Issue ID")
    term_name: str = Field(..., description="Term name this issue relates to")
    issue_type: str = Field(..., description="Type of issue")
    description: str = Field(..., description="Description of the issue")

    @classmethod
    def from_db_row(cls, row: Any) -> "IssueResponse":
        """Create from database row.

        Args:
            row: Database row (sqlite3.Row or dict-like).

        Returns:
            IssueResponse: Response instance.
        """
        return cls(
            id=row["id"],
            term_name=row["term_name"],
            issue_type=row["issue_type"],
            description=row["description"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["IssueResponse"]:
        """Create list from database rows.

        Args:
            rows: List of database rows (sqlite3.Row or dict-like).

        Returns:
            list[IssueResponse]: List of response instances.
        """
        return [cls.from_db_row(row) for row in rows]
