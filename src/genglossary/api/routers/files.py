"""Files API endpoints."""

import re
import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db
from genglossary.db.connection import transaction
from genglossary.api.schemas.file_schemas import (
    FileCreateBulkRequest,
    FileCreateRequest,
    FileDetailResponse,
    FileResponse,
)
from genglossary.db.document_repository import (
    create_document,
    delete_document,
    get_document,
    get_document_by_name,
    list_all_documents,
)
from genglossary.utils.hash import compute_content_hash

router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])

ALLOWED_EXTENSIONS = {".txt", ".md"}


def _validate_file_name(file_name: str) -> str:
    """Validate and normalize file name (relative path).

    Accepts relative paths with forward slashes (e.g., 'chapter1/intro.md').
    Rejects absolute paths, path traversal attempts (..), and Windows backslashes.
    Normalizes paths by removing '.' segments.

    Args:
        file_name: File name or relative path to validate.

    Returns:
        Normalized path string.

    Raises:
        HTTPException: If file name is invalid.
    """
    # Reject absolute paths (Unix-style or Windows drive paths)
    if file_name.startswith("/") or re.match(r"^[A-Za-z]:", file_name):
        raise HTTPException(
            status_code=400,
            detail="Absolute paths not allowed",
        )

    # Reject Windows backslashes (POSIX format only)
    if "\\" in file_name:
        raise HTTPException(
            status_code=400,
            detail="File name must use forward slashes",
        )

    # Split into segments for validation and normalization
    segments = file_name.split("/")

    # Reject path traversal attempts (check path segments, not substring)
    # This allows filenames like "notes..md" but rejects "../secret.txt"
    if ".." in segments:
        raise HTTPException(
            status_code=400,
            detail="File name cannot contain '..' path segments",
        )

    # Normalize: remove '.' segments
    normalized_segments = [s for s in segments if s != "."]
    normalized = "/".join(normalized_segments)

    # Check extension on normalized path
    if "." not in normalized:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    ext = "." + normalized.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    return normalized


@router.get("", response_model=list[FileResponse])
async def list_files(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[FileResponse]:
    """List all registered documents for a project.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        list[FileResponse]: List of all documents.
    """
    rows = list_all_documents(project_db)
    return FileResponse.from_db_rows(rows)


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file_by_id(
    project_id: int = Path(..., description="Project ID"),
    file_id: int = Path(..., description="File ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> FileDetailResponse:
    """Get a specific document by ID with content.

    Args:
        project_id: Project ID (path parameter).
        file_id: File ID to retrieve.
        project_db: Project database connection.

    Returns:
        FileDetailResponse: The requested document with content.

    Raises:
        HTTPException: 404 if document not found.
    """
    row = get_document(project_db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    return FileDetailResponse.from_db_row(row)


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    project_id: int = Path(..., description="Project ID"),
    request: FileCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> FileResponse:
    """Add a new document file to the project.

    Args:
        project_id: Project ID (path parameter).
        request: File creation request with file_name and content.
        project_db: Project database connection.

    Returns:
        FileResponse: The created document.

    Raises:
        HTTPException: 400 if file name or extension is invalid.
        HTTPException: 409 if file already exists.
    """
    # Validate and normalize file name
    normalized_file_name = _validate_file_name(request.file_name)

    # Compute hash
    content_hash = compute_content_hash(request.content)

    # Create document with normalized name
    try:
        with transaction(project_db):
            doc_id = create_document(
                project_db, normalized_file_name, request.content, content_hash
            )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"File already exists: {normalized_file_name}"
        )

    # Return created document
    row = get_document(project_db, doc_id)
    assert row is not None

    return FileResponse.from_db_row(row)


@router.post(
    "/bulk", response_model=list[FileResponse], status_code=status.HTTP_201_CREATED
)
async def create_files_bulk(
    project_id: int = Path(..., description="Project ID"),
    request: FileCreateBulkRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[FileResponse]:
    """Add multiple document files to the project.

    This is an atomic operation - if any file fails validation or already exists,
    none of the files will be created.

    Args:
        project_id: Project ID (path parameter).
        request: Bulk file creation request with list of files.
        project_db: Project database connection.

    Returns:
        list[FileResponse]: List of created documents.

    Raises:
        HTTPException: 400 if any file name or extension is invalid.
        HTTPException: 409 if any file already exists.
    """
    # Validate and normalize all file names first
    normalized_files: list[tuple[str, str]] = []  # (normalized_name, content)
    for file_req in request.files:
        normalized_name = _validate_file_name(file_req.file_name)
        normalized_files.append((normalized_name, file_req.content))

    # Check for duplicates in request (using normalized names)
    normalized_names = [name for name, _ in normalized_files]
    if len(normalized_names) != len(set(normalized_names)):
        raise HTTPException(
            status_code=400, detail="Duplicate file names in request"
        )

    # Check for existing files (using normalized names)
    for normalized_name, _ in normalized_files:
        existing = get_document_by_name(project_db, normalized_name)
        if existing is not None:
            raise HTTPException(
                status_code=409, detail=f"File already exists: {normalized_name}"
            )

    # Create all documents with normalized names
    created_ids = []
    with transaction(project_db):
        for normalized_name, content in normalized_files:
            content_hash = compute_content_hash(content)
            doc_id = create_document(
                project_db, normalized_name, content, content_hash
            )
            created_ids.append(doc_id)

    # Return created documents
    responses = []
    for doc_id in created_ids:
        row = get_document(project_db, doc_id)
        assert row is not None
        responses.append(FileResponse.from_db_row(row))

    return responses


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    project_id: int = Path(..., description="Project ID"),
    file_id: int = Path(..., description="File ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """Delete a document file from the project.

    Args:
        project_id: Project ID (path parameter).
        file_id: File ID to delete.
        project_db: Project database connection.

    Raises:
        HTTPException: 404 if file not found.
    """
    # Check if file exists
    row = get_document(project_db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    with transaction(project_db):
        delete_document(project_db, file_id)
