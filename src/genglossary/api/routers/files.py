"""Files API endpoints."""

import sqlite3
import unicodedata

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db, get_run_manager
from genglossary.db.connection import transaction
from genglossary.api.schemas.file_schemas import (
    FileCreateBulkRequest,
    FileCreateBulkResponse,
    FileCreateRequest,
    FileDetailResponse,
    FileResponse,
)
from genglossary.runs.manager import RunManager
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
MAX_SEGMENT_BYTES = 255
MAX_PATH_BYTES = 1024
MAX_CONTENT_BYTES = 3 * 1024 * 1024  # 3MB

# Unicode look-alike characters that could be used to bypass path validation
LOOKALIKE_SLASH = {"\u2215", "\uff0f", "\u2044", "\u29f8"}  # ∕ ／ ⁄ ⧸
LOOKALIKE_DOT = {"\u2024", "\uff0e", "\u00b7", "\u3002", "\uff61"}  # ․ ． · 。 ｡

# Control characters (C0: U+0000-U+001F, C1: U+007F-U+009F)
CONTROL_CHARS = set(chr(c) for c in range(0x00, 0x20)) | set(chr(c) for c in range(0x7F, 0xA0))

# Bidi override and zero-width characters (filename spoofing)
BIDI_AND_ZERO_WIDTH = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u200e",  # LEFT-TO-RIGHT MARK
    "\u200f",  # RIGHT-TO-LEFT MARK
    "\u202a",  # LEFT-TO-RIGHT EMBEDDING
    "\u202b",  # RIGHT-TO-LEFT EMBEDDING
    "\u202c",  # POP DIRECTIONAL FORMATTING
    "\u202d",  # LEFT-TO-RIGHT OVERRIDE
    "\u202e",  # RIGHT-TO-LEFT OVERRIDE
    "\u2066",  # LEFT-TO-RIGHT ISOLATE
    "\u2067",  # RIGHT-TO-LEFT ISOLATE
    "\u2068",  # FIRST STRONG ISOLATE
    "\u2069",  # POP DIRECTIONAL ISOLATE
    "\u061c",  # ARABIC LETTER MARK
    "\u2060",  # WORD JOINER
    "\ufeff",  # BYTE ORDER MARK / ZERO WIDTH NO-BREAK SPACE
}

# Windows/NTFS invalid characters (also blocks ADS via colon)
WINDOWS_INVALID_CHARS = {":", "<", ">", '"', "|", "?", "*"}

# Combined forbidden characters (single loop check)
FORBIDDEN_CHARS = CONTROL_CHARS | BIDI_AND_ZERO_WIDTH | LOOKALIKE_SLASH | LOOKALIKE_DOT | WINDOWS_INVALID_CHARS

# Trailing forbidden characters (space, dot, Unicode whitespace)
TRAILING_FORBIDDEN = (
    " ",  # Regular space
    ".",  # Dot
    "\u00a0",  # NO-BREAK SPACE
    "\u2000",  # EN QUAD
    "\u2001",  # EM QUAD
    "\u2002",  # EN SPACE
    "\u2003",  # EM SPACE
    "\u2009",  # THIN SPACE
    "\u200a",  # HAIR SPACE
    "\u3000",  # IDEOGRAPHIC SPACE
)

# Windows reserved device names
WINDOWS_RESERVED_NAMES = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def _validate_content_size(content: str) -> None:
    """Validate content size is within limit.

    Args:
        content: File content to validate.

    Raises:
        HTTPException: If content exceeds size limit.
    """
    content_bytes = len(content.encode("utf-8"))
    if content_bytes > MAX_CONTENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content too large ({content_bytes} bytes). Max: {MAX_CONTENT_BYTES} bytes (3MB)",
        )


def _validate_file_name(file_name: str) -> str:
    """Validate and normalize file name (relative path).

    Accepts relative paths with forward slashes (e.g., 'chapter1/intro.md').
    Rejects absolute paths, path traversal attempts (..), and Windows backslashes.
    Normalizes paths by removing '.' segments and applying NFC normalization.

    Args:
        file_name: File name or relative path to validate.

    Returns:
        Normalized path string.

    Raises:
        HTTPException: If file name is invalid.
    """
    # Apply NFC normalization first
    file_name = unicodedata.normalize("NFC", file_name)

    # Reject forbidden characters (control, bidi, zero-width, look-alike)
    if any(char in FORBIDDEN_CHARS for char in file_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name contains disallowed Unicode characters",
        )

    # Reject absolute paths (Unix-style; Windows drive paths blocked by FORBIDDEN_CHARS)
    if file_name.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Absolute paths not allowed",
        )

    # Reject Windows backslashes (POSIX format only)
    if "\\" in file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name must use forward slashes",
        )

    # Split into segments for validation and normalization
    segments = file_name.split("/")

    # Reject path traversal attempts (check path segments, not substring)
    # This allows filenames like "notes..md" but rejects "../secret.txt"
    if ".." in segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot contain '..' path segments",
        )

    # Normalize: remove '.' and empty segments
    normalized_segments = [s for s in segments if s and s != "."]

    if not normalized_segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot be empty after normalization",
        )

    # Validate all segments in a single pass
    for segment in normalized_segments:
        # Check trailing space, dot, or Unicode whitespace (Windows compatibility)
        if segment.endswith(TRAILING_FORBIDDEN):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path segments cannot have trailing spaces or dots",
            )

        # Check segment length limit (255 bytes each)
        if len(segment.encode("utf-8")) > MAX_SEGMENT_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path segment too long (max {MAX_SEGMENT_BYTES} bytes)",
            )

    # Build normalized path
    normalized = "/".join(normalized_segments)

    # Check total path length limit (1024 bytes)
    if len(normalized.encode("utf-8")) > MAX_PATH_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path too long (max {MAX_PATH_BYTES} bytes)",
        )

    # Check extension on final segment (basename)
    basename = normalized_segments[-1]
    _, _, extension = basename.rpartition(".")

    if not extension or f".{extension.lower()}" not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check Windows reserved device names (case-insensitive, basename only)
    basename_without_ext = basename.rpartition(".")[0]
    if basename_without_ext.upper() in WINDOWS_RESERVED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is a reserved Windows device name",
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

    # Validate content size
    _validate_content_size(request.content)

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
    "/bulk", response_model=FileCreateBulkResponse, status_code=status.HTTP_201_CREATED
)
async def create_files_bulk(
    project_id: int = Path(..., description="Project ID"),
    request: FileCreateBulkRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
    manager: RunManager = Depends(get_run_manager),
) -> FileCreateBulkResponse:
    """Add multiple document files to the project and auto-trigger extract.

    This is an atomic operation - if any file fails validation or already exists,
    none of the files will be created. After successful creation, an extract run
    is automatically triggered.

    Args:
        project_id: Project ID (path parameter).
        request: Bulk file creation request with list of files.
        project_db: Project database connection.
        manager: Run manager for auto-triggering extract.

    Returns:
        FileCreateBulkResponse: Created documents with extract status.

    Raises:
        HTTPException: 400 if any file name or extension is invalid.
        HTTPException: 409 if any file already exists.
    """
    # Validate and normalize all file names first
    normalized_files: list[tuple[str, str]] = []  # (normalized_name, content)
    for file_req in request.files:
        normalized_name = _validate_file_name(file_req.file_name)
        _validate_content_size(file_req.content)
        normalized_files.append((normalized_name, file_req.content))

    # Check for duplicates in request (using normalized names)
    if len(normalized_files) != len(set(name for name, _ in normalized_files)):
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
    try:
        with transaction(project_db):
            for normalized_name, content in normalized_files:
                content_hash = compute_content_hash(content)
                doc_id = create_document(
                    project_db, normalized_name, content, content_hash
                )
                created_ids.append(doc_id)
    except sqlite3.IntegrityError as e:
        # Only map UNIQUE constraint violations to 409; re-raise others
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=409,
                detail="File already exists (concurrent creation)",
            )
        raise

    # Build file responses
    file_responses = []
    for doc_id in created_ids:
        row = get_document(project_db, doc_id)
        assert row is not None
        file_responses.append(FileResponse.from_db_row(row))

    # Auto-trigger extract run
    extract_started = False
    extract_skipped_reason: str | None = None
    try:
        manager.start_run(scope="extract", triggered_by="auto")
        extract_started = True
    except Exception as e:
        extract_skipped_reason = str(e)

    return FileCreateBulkResponse(
        files=file_responses,
        extract_started=extract_started,
        extract_skipped_reason=extract_skipped_reason,
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

    Raises:
        HTTPException: 404 if file not found.
    """
    # Check if file exists
    row = get_document(project_db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    with transaction(project_db):
        delete_document(project_db, file_id)
