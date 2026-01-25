"""Files API endpoints."""

import hashlib
import sqlite3
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_by_id, get_project_db
from genglossary.api.schemas.file_schemas import (
    DiffScanResponse,
    FileCreateRequest,
    FileResponse,
)
from genglossary.db.document_repository import (
    create_document,
    delete_document,
    get_document,
    get_document_by_path,
    list_all_documents,
)
from genglossary.models.project import Project

router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])


def _compute_file_hash(file_path: FilePath) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        str: Hexadecimal hash string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


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
    return [
        FileResponse(
            id=row["id"],
            file_path=row["file_path"],
            content_hash=row["content_hash"],
        )
        for row in rows
    ]


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

    return FileResponse(
        id=row["id"],
        file_path=row["file_path"],
        content_hash=row["content_hash"],
    )


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    project_id: int = Path(..., description="Project ID"),
    request: FileCreateRequest = ...,
    project: Project = Depends(get_project_by_id),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> FileResponse:
    """Add a new document file to the project.

    Args:
        project_id: Project ID (path parameter).
        request: File creation request.
        project: Project instance.
        project_db: Project database connection.

    Returns:
        FileResponse: The created document.

    Raises:
        HTTPException: 400 if file doesn't exist in doc_root.
    """
    # Resolve file path
    file_full_path = FilePath(project.doc_root) / request.file_path

    # Check if file exists
    if not file_full_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"File not found in doc_root: {request.file_path}",
        )

    # Compute hash
    content_hash = _compute_file_hash(file_full_path)

    # Create document
    doc_id = create_document(project_db, request.file_path, content_hash)

    # Return created document
    row = get_document(project_db, doc_id)
    assert row is not None

    return FileResponse(
        id=row["id"],
        file_path=row["file_path"],
        content_hash=row["content_hash"],
    )


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
    """
    delete_document(project_db, file_id)


@router.post("/diff-scan", response_model=DiffScanResponse)
async def diff_scan(
    project_id: int = Path(..., description="Project ID"),
    project: Project = Depends(get_project_by_id),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> DiffScanResponse:
    """Scan doc_root for file changes (added, modified, deleted).

    Args:
        project_id: Project ID (path parameter).
        project: Project instance.
        project_db: Project database connection.

    Returns:
        DiffScanResponse: Lists of added, modified, and deleted files.
    """
    doc_root = FilePath(project.doc_root)

    # Get all registered documents
    registered_docs = {row["file_path"]: row for row in list_all_documents(project_db)}

    # Scan filesystem for all files
    if not doc_root.exists():
        # If doc_root doesn't exist, all registered files are deleted
        return DiffScanResponse(
            added=[], modified=[], deleted=list(registered_docs.keys())
        )

    filesystem_files = {
        str(f.relative_to(doc_root))
        for f in doc_root.rglob("*")
        if f.is_file()
    }

    # Detect changes
    added = []
    modified = []
    deleted = []

    # Check for new and modified files
    for file_path in filesystem_files:
        if file_path not in registered_docs:
            added.append(file_path)
        else:
            # Check if file was modified (hash changed)
            full_path = doc_root / file_path
            current_hash = _compute_file_hash(full_path)
            if current_hash != registered_docs[file_path]["content_hash"]:
                modified.append(file_path)

    # Check for deleted files
    for file_path in registered_docs.keys():
        if file_path not in filesystem_files:
            deleted.append(file_path)

    return DiffScanResponse(added=added, modified=modified, deleted=deleted)
