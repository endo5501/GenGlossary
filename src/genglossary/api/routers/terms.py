"""Terms API endpoints."""

import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.term_schemas import (
    TermCreateRequest,
    TermResponse,
    TermUpdateRequest,
)
from genglossary.db.term_repository import (
    create_term,
    delete_term,
    get_term,
    list_all_terms,
    update_term,
)

router = APIRouter(prefix="/api/projects/{project_id}/terms", tags=["terms"])


@router.get("", response_model=list[TermResponse])
async def list_terms(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[TermResponse]:
    """List all extracted terms for a project.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        list[TermResponse]: List of all terms.
    """
    rows = list_all_terms(project_db)
    return TermResponse.from_db_rows(rows)


@router.get("/{term_id}", response_model=TermResponse)
async def get_term_by_id(
    project_id: int = Path(..., description="Project ID"),
    term_id: int = Path(..., description="Term ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """Get a specific term by ID.

    Args:
        project_id: Project ID (path parameter).
        term_id: Term ID to retrieve.
        project_db: Project database connection.

    Returns:
        TermResponse: The requested term.

    Raises:
        HTTPException: 404 if term not found.
    """
    row = get_term(project_db, term_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    return TermResponse.from_db_row(row)


@router.post("", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
async def create_new_term(
    project_id: int = Path(..., description="Project ID"),
    request: TermCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """Create a new term.

    Args:
        project_id: Project ID (path parameter).
        request: Term creation request.
        project_db: Project database connection.

    Returns:
        TermResponse: The created term.
    """
    term_id = create_term(project_db, request.term_text, request.category)
    row = get_term(project_db, term_id)
    assert row is not None

    return TermResponse.from_db_row(row)


@router.patch("/{term_id}", response_model=TermResponse)
async def update_existing_term(
    project_id: int = Path(..., description="Project ID"),
    term_id: int = Path(..., description="Term ID"),
    request: TermUpdateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """Update an existing term.

    Args:
        project_id: Project ID (path parameter).
        term_id: Term ID to update.
        request: Term update request.
        project_db: Project database connection.

    Returns:
        TermResponse: The updated term.

    Raises:
        HTTPException: 404 if term not found.
    """
    try:
        update_term(project_db, term_id, request.term_text, request.category)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    row = get_term(project_db, term_id)
    assert row is not None

    return TermResponse.from_db_row(row)


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_term(
    project_id: int = Path(..., description="Project ID"),
    term_id: int = Path(..., description="Term ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """Delete a term.

    Args:
        project_id: Project ID (path parameter).
        term_id: Term ID to delete.
        project_db: Project database connection.
    """
    delete_term(project_db, term_id)
