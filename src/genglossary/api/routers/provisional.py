"""Provisional API endpoints."""

import sqlite3

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_by_id, get_project_db
from genglossary.api.routers._synonym_helpers import build_aliases_map
from genglossary.db.connection import transaction
from genglossary.api.schemas.provisional_schemas import (
    ProvisionalResponse,
    ProvisionalUpdateRequest,
)
from genglossary.db.models import GlossaryTermRow
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


def _ensure_term_exists(conn: sqlite3.Connection, entry_id: int) -> GlossaryTermRow:
    """Ensure term exists and return it.

    Args:
        conn: Database connection.
        entry_id: Term entry ID.

    Returns:
        GlossaryTermRow: The term row.

    Raises:
        HTTPException: 404 if term not found.
    """
    row = get_provisional_term(conn, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
    return row


def _get_term_response(conn: sqlite3.Connection, entry_id: int) -> ProvisionalResponse:
    """Get term response after ensuring it exists.

    Args:
        conn: Database connection.
        entry_id: Term entry ID.

    Returns:
        ProvisionalResponse: The term response.

    Raises:
        RuntimeError: If term not found (should never happen after update).
    """
    row = get_provisional_term(conn, entry_id)
    if row is None:
        raise RuntimeError(f"Entry {entry_id} disappeared after update")
    aliases_map = build_aliases_map(conn)
    return ProvisionalResponse.from_db_row(row, aliases_map)


def _regenerate_definition(row: GlossaryTermRow, project: Project) -> tuple[str, float]:
    """Regenerate definition for a term using LLM.

    Args:
        row: Term row from database.
        project: Project instance.

    Returns:
        tuple[str, float]: Regenerated (definition, confidence).

    Raises:
        httpx.TimeoutException: If LLM service times out.
        httpx.HTTPError: If LLM service is unavailable.
    """
    llm_client = create_llm_client(project.llm_provider, project.llm_model)
    documents = DocumentLoader().load_directory(project.doc_root)
    generator = GlossaryGenerator(llm_client=llm_client)

    occurrences = generator._find_term_occurrences(row["term_name"], documents)
    occurrences = occurrences or row["occurrences"]

    return generator._generate_definition(row["term_name"], occurrences)


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
    aliases_map = build_aliases_map(project_db)
    return ProvisionalResponse.from_db_rows(rows, aliases_map)


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
    row = _ensure_term_exists(project_db, entry_id)
    aliases_map = build_aliases_map(project_db)
    return ProvisionalResponse.from_db_row(row, aliases_map)


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
    _ensure_term_exists(project_db, entry_id)
    with transaction(project_db):
        update_provisional_term(project_db, entry_id, request.definition, request.confidence)
    return _get_term_response(project_db, entry_id)


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
    row = _ensure_term_exists(project_db, entry_id)

    try:
        definition, confidence = _regenerate_definition(row, project)
        with transaction(project_db):
            update_provisional_term(project_db, entry_id, definition, confidence)
        return _get_term_response(project_db, entry_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid LLM provider: {e}")
    except (FileNotFoundError, NotADirectoryError) as e:
        raise HTTPException(status_code=400, detail=f"Document root not found: {e}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="LLM service timeout")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
