"""Provisional API endpoints."""

import sqlite3

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_by_id, get_project_db
from genglossary.api.schemas.provisional_schemas import (
    ProvisionalResponse,
    ProvisionalUpdateRequest,
)
from genglossary.db.provisional_repository import (
    get_provisional_term,
    list_all_provisional,
    update_provisional_term,
)
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.llm.factory import create_llm_client
from genglossary.models.project import Project

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
    return ProvisionalResponse.from_db_rows(rows)


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

    return ProvisionalResponse.from_db_row(row)


@router.patch("/{entry_id}", response_model=ProvisionalResponse)
async def update_provisional(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    request: ProvisionalUpdateRequest = Body(...),
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

    return ProvisionalResponse.from_db_row(updated_row)


@router.post("/{entry_id}/regenerate", response_model=ProvisionalResponse)
async def regenerate_provisional(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    project: Project = Depends(get_project_by_id),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ProvisionalResponse:
    """Regenerate definition for a provisional term using LLM.

    Args:
        project_id: Project ID (path parameter).
        entry_id: Term entry ID to regenerate.
        project: Project instance.
        project_db: Project database connection.

    Returns:
        ProvisionalResponse: The regenerated term.

    Raises:
        HTTPException: 404 if term not found.
        HTTPException: 503 if LLM service is unavailable or times out.
    """
    # Check if term exists
    row = get_provisional_term(project_db, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    try:
        # Create LLM client
        llm_client = create_llm_client(project.llm_provider, project.llm_model or None)

        # Load documents
        loader = DocumentLoader()
        documents = loader.load_directory(project.doc_root)

        # Regenerate definition using GlossaryGenerator
        generator = GlossaryGenerator(llm_client=llm_client)
        occurrences = generator._find_term_occurrences(row["term_name"], documents)
        if not occurrences:
            # Use existing occurrences if no new ones found
            occurrences = row["occurrences"]

        definition, confidence = generator._generate_definition(
            row["term_name"], occurrences
        )

        # Update database
        update_provisional_term(project_db, entry_id, definition, confidence)

        # Return updated term
        updated_row = get_provisional_term(project_db, entry_id)
        assert updated_row is not None

        return ProvisionalResponse.from_db_row(updated_row)

    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="LLM service timeout")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
