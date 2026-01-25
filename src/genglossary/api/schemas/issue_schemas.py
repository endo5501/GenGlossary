"""Schemas for Issues API."""

from pydantic import BaseModel, Field


class IssueResponse(BaseModel):
    """Response schema for a glossary issue."""

    id: int = Field(..., description="Issue ID")
    term_name: str = Field(..., description="Term name this issue relates to")
    issue_type: str = Field(..., description="Type of issue")
    description: str = Field(..., description="Description of the issue")
