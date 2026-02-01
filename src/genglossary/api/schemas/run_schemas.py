"""Schemas for Runs API."""

from typing import Any

from pydantic import BaseModel, Field


class RunScope:
    """Run scope constants."""

    FULL = "full"
    EXTRACT = "extract"
    GENERATE = "generate"
    REVIEW = "review"
    REFINE = "refine"


class RunStartRequest(BaseModel):
    """Request schema for starting a new run."""

    scope: str = Field(
        ...,
        description="Run scope",
        pattern="^(full|extract|generate|review|refine)$",
    )


class RunResponse(BaseModel):
    """Response schema for a run."""

    id: int = Field(..., description="Run ID")
    scope: str = Field(..., description="Run scope")
    status: str = Field(..., description="Run status")
    started_at: str | None = Field(None, description="Started timestamp (ISO format)")
    finished_at: str | None = Field(None, description="Finished timestamp (ISO format)")
    triggered_by: str = Field(..., description="Source that triggered the run")
    error_message: str | None = Field(None, description="Error message if failed")
    progress_current: int = Field(0, description="Current progress value")
    progress_total: int = Field(0, description="Total progress value")
    current_step: str | None = Field(None, description="Current step name")
    created_at: str = Field(..., description="Created timestamp (ISO format)")

    @classmethod
    def from_db_row(cls, row: Any) -> "RunResponse":
        """Create from database row.

        Args:
            row: Database row (sqlite3.Row or dict-like).

        Returns:
            RunResponse: Response instance.
        """
        return cls(
            id=row["id"],
            scope=row["scope"],
            status=row["status"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            triggered_by=row["triggered_by"],
            error_message=row["error_message"],
            progress_current=row["progress_current"],
            progress_total=row["progress_total"],
            current_step=row["current_step"],
            created_at=row["created_at"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["RunResponse"]:
        """Create list from database rows.

        Args:
            rows: List of database rows (sqlite3.Row or dict-like).

        Returns:
            list[RunResponse]: List of response instances.
        """
        return [cls.from_db_row(row) for row in rows]
