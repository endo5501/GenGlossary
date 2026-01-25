"""Issues API endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.issue_schemas import IssueResponse
from genglossary.db.issue_repository import get_issue, list_all_issues

router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["issues"])


@router.get("", response_model=list[IssueResponse])
async def list_issues(
    project_id: int = Path(..., description="Project ID"),
    issue_type: str | None = Query(None, description="Filter by issue type"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[IssueResponse]:
    """List all issues for a project, optionally filtered by issue type.

    Args:
        project_id: Project ID (path parameter).
        issue_type: Optional issue type filter.
        project_db: Project database connection.

    Returns:
        list[IssueResponse]: List of issues.
    """
    rows = list_all_issues(project_db)

    # Filter by issue_type if provided
    if issue_type is not None:
        rows = [row for row in rows if row["issue_type"] == issue_type]

    return [
        IssueResponse(
            id=row["id"],
            term_name=row["term_name"],
            issue_type=row["issue_type"],
            description=row["description"],
        )
        for row in rows
    ]


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue_by_id(
    project_id: int = Path(..., description="Project ID"),
    issue_id: int = Path(..., description="Issue ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> IssueResponse:
    """Get a specific issue by ID.

    Args:
        project_id: Project ID (path parameter).
        issue_id: Issue ID to retrieve.
        project_db: Project database connection.

    Returns:
        IssueResponse: The requested issue.

    Raises:
        HTTPException: 404 if issue not found.
    """
    row = get_issue(project_db, issue_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")

    return IssueResponse(
        id=row["id"],
        term_name=row["term_name"],
        issue_type=row["issue_type"],
        description=row["description"],
    )
