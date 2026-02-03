"""Excluded Terms API endpoints."""

import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.excluded_term_schemas import (
    ExcludedTermCreateRequest,
    ExcludedTermListResponse,
    ExcludedTermResponse,
)
from genglossary.db.connection import transaction
from genglossary.db.excluded_term_repository import (
    add_excluded_term,
    delete_excluded_term,
    get_all_excluded_terms,
    get_excluded_term_by_id,
)

router = APIRouter(
    prefix="/api/projects/{project_id}/excluded-terms",
    tags=["excluded-terms"],
)


@router.get("", response_model=ExcludedTermListResponse)
async def list_excluded_terms(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ExcludedTermListResponse:
    """List all excluded terms for a project.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        ExcludedTermListResponse: List of excluded terms with total count.
    """
    terms = get_all_excluded_terms(project_db)
    items = ExcludedTermResponse.from_models(terms)
    return ExcludedTermListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=ExcludedTermResponse,
    responses={
        201: {"description": "Term created"},
        200: {"description": "Term already exists, returning existing"},
    },
)
async def create_excluded_term(
    project_id: int = Path(..., description="Project ID"),
    request: ExcludedTermCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
):
    """Add a term to the exclusion list.

    Manually adds a term to the exclusion list. If the term already exists,
    returns the existing term with 200 status instead of 201.

    Args:
        project_id: Project ID (path parameter).
        request: Term creation request.
        project_db: Project database connection.

    Returns:
        ExcludedTermResponse: The created or existing excluded term.
    """
    from fastapi.responses import JSONResponse

    # Add term atomically - returns (id, created) to avoid race condition
    with transaction(project_db):
        term_id, created = add_excluded_term(project_db, request.term_text, "manual")

    # Get the term by ID directly (O(1) instead of O(n))
    term = get_excluded_term_by_id(project_db, term_id)
    assert term is not None

    response_data = ExcludedTermResponse.from_model(term)

    if created:
        # Return 201 for new term
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data.model_dump(mode="json"),
        )
    else:
        # Return 200 for existing term
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(mode="json"),
        )


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_excluded_term_endpoint(
    project_id: int = Path(..., description="Project ID"),
    term_id: int = Path(..., description="Excluded term ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """Remove a term from the exclusion list.

    Args:
        project_id: Project ID (path parameter).
        term_id: Excluded term ID to delete.
        project_db: Project database connection.

    Raises:
        HTTPException: 404 if term not found.
    """
    with transaction(project_db):
        deleted = delete_excluded_term(project_db, term_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Excluded term {term_id} not found",
        )
