"""Required Terms API endpoints."""

import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.required_term_schemas import (
    RequiredTermCreateRequest,
    RequiredTermListResponse,
    RequiredTermResponse,
)
from genglossary.db.connection import transaction
from genglossary.db.required_term_repository import (
    add_required_term,
    delete_required_term,
    get_all_required_terms,
    get_required_term_by_id,
)

router = APIRouter(
    prefix="/api/projects/{project_id}/required-terms",
    tags=["required-terms"],
)


@router.get("", response_model=RequiredTermListResponse)
async def list_required_terms(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> RequiredTermListResponse:
    """List all required terms for a project.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        RequiredTermListResponse: List of required terms with total count.
    """
    terms = get_all_required_terms(project_db)
    items = RequiredTermResponse.from_models(terms)
    return RequiredTermListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=RequiredTermResponse,
    responses={
        201: {"description": "Term created"},
        200: {"description": "Term already exists, returning existing"},
    },
)
async def create_required_term(
    project_id: int = Path(..., description="Project ID"),
    request: RequiredTermCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
):
    """Add a term to the required list.

    Manually adds a term to the required list. If the term already exists,
    returns the existing term with 200 status instead of 201.

    Args:
        project_id: Project ID (path parameter).
        request: Term creation request.
        project_db: Project database connection.

    Returns:
        RequiredTermResponse: The created or existing required term.
    """
    from fastapi.responses import JSONResponse

    with transaction(project_db):
        term_id, created = add_required_term(project_db, request.term_text, "manual")

    term = get_required_term_by_id(project_db, term_id)
    assert term is not None

    response_data = RequiredTermResponse.from_model(term)

    if created:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data.model_dump(mode="json"),
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(mode="json"),
        )


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_required_term_endpoint(
    project_id: int = Path(..., description="Project ID"),
    term_id: int = Path(..., description="Required term ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """Remove a term from the required list.

    Args:
        project_id: Project ID (path parameter).
        term_id: Required term ID to delete.
        project_db: Project database connection.

    Raises:
        HTTPException: 404 if term not found.
    """
    with transaction(project_db):
        deleted = delete_required_term(project_db, term_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Required term {term_id} not found",
        )
