"""Files API endpoints."""

import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db
from genglossary.db.connection import transaction
from genglossary.api.schemas.file_schemas import (
    FileCreateBulkRequest,
    FileCreateRequest,
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


def _validate_file_name(file_name: str) -> None:
    """Validate file name.

    Args:
        file_name: File name to validate.

    Raises:
        HTTPException: If file name is invalid.
    """
    # Check for path separators
    if "/" in file_name or "\\" in file_name:
        raise HTTPException(
            status_code=400,
            detail="File name cannot contain path separators",
        )

    # Check extension
    if "." not in file_name:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    ext = "." + file_name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )


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


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_by_id(
    project_id: int = Path(..., description="Project ID"),
    file_id: int = Path(..., description="File ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> FileResponse:
    """Get a specific document by ID.

    Args:
        project_id: Project ID (path parameter).
        file_id: File ID to retrieve.
        project_db: Project database connection.

    Returns:
        FileResponse: The requested document.

    Raises:
        HTTPException: 404 if document not found.
    """
    row = get_document(project_db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    return FileResponse.from_db_row(row)


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
    # Validate file name
    _validate_file_name(request.file_name)

    # Compute hash
    content_hash = compute_content_hash(request.content)

    # Create document
    try:
        with transaction(project_db):
            doc_id = create_document(
                project_db, request.file_name, request.content, content_hash
            )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"File already exists: {request.file_name}"
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
    # Validate all file names first
    for file_req in request.files:
        _validate_file_name(file_req.file_name)

    # Check for duplicates in request
    file_names = [f.file_name for f in request.files]
    if len(file_names) != len(set(file_names)):
        raise HTTPException(
            status_code=400, detail="Duplicate file names in request"
        )

    # Check for existing files
    for file_req in request.files:
        existing = get_document_by_name(project_db, file_req.file_name)
        if existing is not None:
            raise HTTPException(
                status_code=409, detail=f"File already exists: {file_req.file_name}"
            )

    # Create all documents
    created_ids = []
    with transaction(project_db):
        for file_req in request.files:
            content_hash = compute_content_hash(file_req.content)
            doc_id = create_document(
                project_db, file_req.file_name, file_req.content, content_hash
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
