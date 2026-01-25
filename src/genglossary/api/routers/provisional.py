"""Provisional API endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.provisional_schemas import (
    ProvisionalResponse,
    ProvisionalUpdateRequest,
)
from genglossary.db.provisional_repository import (
    get_provisional_term,
    list_all_provisional,
    update_provisional_term,
)

router = APIRouter(prefix="/api/projects/{project_id}/provisional", tags=["provisional"])


@router.get("", response_model=list[ProvisionalResponse])
async def list_provisional(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[ProvisionalResponse]:
    """List all provisional glossary terms for a project.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        list[ProvisionalResponse]: List of all provisional terms.
    """
    rows = list_all_provisional(project_db)
    return [
        ProvisionalResponse(
            id=row["id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=row["occurrences"],
        )
        for row in rows
    ]


@router.get("/{entry_id}", response_model=ProvisionalResponse)
async def get_provisional_by_id(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ProvisionalResponse:
    """Get a specific provisional term by ID.

    Args:
        project_id: Project ID (path parameter).
        entry_id: Term entry ID to retrieve.
        project_db: Project database connection.

    Returns:
        ProvisionalResponse: The requested term.

    Raises:
        HTTPException: 404 if term not found.
    """
    row = get_provisional_term(project_db, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    return ProvisionalResponse(
        id=row["id"],
        term_name=row["term_name"],
        definition=row["definition"],
        confidence=row["confidence"],
        occurrences=row["occurrences"],
    )


@router.patch("/{entry_id}", response_model=ProvisionalResponse)
async def update_provisional(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    request: ProvisionalUpdateRequest = ...,
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ProvisionalResponse:
    """Update a provisional term's definition and confidence.

    Args:
        project_id: Project ID (path parameter).
        entry_id: Term entry ID to update.
        request: Update request.
        project_db: Project database connection.

    Returns:
        ProvisionalResponse: The updated term.

    Raises:
        HTTPException: 404 if term not found.
    """
    # Check if term exists
    row = get_provisional_term(project_db, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    # Update term
    update_provisional_term(project_db, entry_id, request.definition, request.confidence)

    # Return updated term
    updated_row = get_provisional_term(project_db, entry_id)
    assert updated_row is not None

    return ProvisionalResponse(
        id=updated_row["id"],
        term_name=updated_row["term_name"],
        definition=updated_row["definition"],
        confidence=updated_row["confidence"],
        occurrences=updated_row["occurrences"],
    )


@router.post("/{entry_id}/regenerate", response_model=ProvisionalResponse)
async def regenerate_provisional(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ProvisionalResponse:
    """Regenerate definition for a provisional term using LLM.

    Args:
        project_id: Project ID (path parameter).
        entry_id: Term entry ID to regenerate.
        project_db: Project database connection.

    Returns:
        ProvisionalResponse: The regenerated term.

    Raises:
        HTTPException: 404 if term not found.
    """
    # Check if term exists
    row = get_provisional_term(project_db, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    # TODO: Implement LLM-based regeneration
    # For now, just return the existing term
    # This will be implemented in a future enhancement
    return ProvisionalResponse(
        id=row["id"],
        term_name=row["term_name"],
        definition=row["definition"],
        confidence=row["confidence"],
        occurrences=row["occurrences"],
    )
