"""Projects API endpoints."""

import os
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Path as PathParam, status

from genglossary.api.dependencies import get_registry_db
from genglossary.api.schemas.project_schemas import (
    ProjectCloneRequest,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectStatistics,
    ProjectUpdateRequest,
)
from genglossary.db.connection import get_connection
from genglossary.db.project_repository import (
    clone_project,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from genglossary.db.stats_repository import (
    count_documents,
    count_issues,
    count_provisional_terms,
)
from genglossary.models.project import Project

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_project_or_404(
    registry_conn: sqlite3.Connection,
    project_id: int,
) -> Project:
    """Get project or raise 404.

    Args:
        registry_conn: Registry database connection.
        project_id: Project ID.

    Returns:
        Project: The requested project.

    Raises:
        HTTPException: 404 if project not found.
    """
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def _cleanup_db_file(db_path: str) -> None:
    """Cleanup orphaned database file.

    Args:
        db_path: Path to the database file.
    """
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass


def _get_projects_dir() -> Path:
    """Get the projects directory path.

    Returns:
        Path: Path to projects directory.
    """
    base_dir = Path(
        os.getenv("GENGLOSSARY_DATA_DIR", str(Path.home() / ".genglossary"))
    )
    projects_dir = base_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


def _generate_db_path(name: str) -> str:
    """Generate a unique database path for a project.

    Args:
        name: Project name (used as part of filename).

    Returns:
        str: Absolute path to the project database file.
    """
    projects_dir = _get_projects_dir()
    # Sanitize name for filesystem
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    unique_id = uuid4().hex[:8]
    db_path = projects_dir / f"{safe_name}_{unique_id}.db"
    return str(db_path)


def _generate_doc_root(name: str) -> str:
    """Generate document root path for a project.

    Args:
        name: Project name.

    Returns:
        str: Absolute path to the project document directory.
    """
    projects_dir = _get_projects_dir()
    doc_root = projects_dir / name
    doc_root.mkdir(parents=True, exist_ok=True)
    return str(doc_root)


def _get_project_statistics(db_path: str) -> ProjectStatistics:
    """Get statistics for a project from its database.

    Args:
        db_path: Path to the project database file.

    Returns:
        ProjectStatistics: Statistics for the project.
    """
    try:
        project_conn = get_connection(db_path)
        stats = ProjectStatistics(
            document_count=count_documents(project_conn),
            term_count=count_provisional_terms(project_conn),
            issue_count=count_issues(project_conn),
        )
        project_conn.close()
        return stats
    except Exception:
        return ProjectStatistics()


@router.get("", response_model=list[ProjectResponse])
async def list_all_projects(
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> list[ProjectResponse]:
    """List all projects with statistics.

    Args:
        registry_conn: Registry database connection.

    Returns:
        list[ProjectResponse]: List of all projects with statistics.
    """
    projects = list_projects(registry_conn)
    result = []
    for p in projects:
        stats = _get_project_statistics(p.db_path)
        result.append(ProjectResponse.from_project(p, stats))
    return result


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: int = PathParam(..., description="Project ID"),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """Get a project by ID.

    Args:
        project_id: Project ID.
        registry_conn: Registry database connection.

    Returns:
        ProjectResponse: The requested project.

    Raises:
        HTTPException: 404 if project not found.
    """
    project = _get_project_or_404(registry_conn, project_id)
    return ProjectResponse.from_project(project)


def _create_project_with_cleanup(
    registry_conn: sqlite3.Connection,
    request: ProjectCreateRequest,
    db_path: str,
    doc_root: str,
) -> int:
    """Create project and cleanup on failure.

    Args:
        registry_conn: Registry database connection.
        request: Project creation request.
        db_path: Database file path.
        doc_root: Document root path.

    Returns:
        int: Created project ID.

    Raises:
        HTTPException: 409 if project name already exists.
    """
    try:
        return create_project(
            registry_conn,
            name=request.name,
            doc_root=doc_root,
            db_path=db_path,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            llm_base_url=request.llm_base_url,
        )
    except sqlite3.IntegrityError:
        _cleanup_db_file(db_path)
        raise HTTPException(
            status_code=409, detail=f"Project name already exists: {request.name}"
        )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    request: ProjectCreateRequest = Body(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """Create a new project.

    Args:
        request: Project creation request.
        registry_conn: Registry database connection.

    Returns:
        ProjectResponse: The created project.

    Raises:
        HTTPException: 409 if project name already exists.
    """
    db_path = _generate_db_path(request.name)
    # Auto-generate doc_root if not provided
    doc_root = request.doc_root if request.doc_root else _generate_doc_root(request.name)
    project_id = _create_project_with_cleanup(registry_conn, request, db_path, doc_root)
    project = _get_project_or_404(registry_conn, project_id)
    return ProjectResponse.from_project(project)


def _clone_project_with_cleanup(
    registry_conn: sqlite3.Connection,
    project_id: int,
    new_name: str,
    new_db_path: str,
) -> int:
    """Clone project and cleanup on failure.

    Args:
        registry_conn: Registry database connection.
        project_id: Source project ID.
        new_name: Name for cloned project.
        new_db_path: Database file path for clone.

    Returns:
        int: Cloned project ID.

    Raises:
        HTTPException: 404 if source project not found, 409 if name exists.
    """
    try:
        return clone_project(
            registry_conn,
            source_id=project_id,
            new_name=new_name,
            new_db_path=new_db_path,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    except sqlite3.IntegrityError:
        _cleanup_db_file(new_db_path)
        raise HTTPException(
            status_code=409, detail=f"Project name already exists: {new_name}"
        )


@router.post(
    "/{project_id}/clone",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_existing_project(
    project_id: int = PathParam(..., description="Project ID to clone"),
    request: ProjectCloneRequest = Body(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """Clone an existing project.

    Args:
        project_id: ID of the project to clone.
        request: Clone request with new name.
        registry_conn: Registry database connection.

    Returns:
        ProjectResponse: The cloned project.

    Raises:
        HTTPException: 404 if source project not found.
        HTTPException: 409 if new name already exists.
    """
    new_db_path = _generate_db_path(request.new_name)
    cloned_id = _clone_project_with_cleanup(registry_conn, project_id, request.new_name, new_db_path)
    project = _get_project_or_404(registry_conn, cloned_id)
    return ProjectResponse.from_project(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_project(
    project_id: int = PathParam(..., description="Project ID to delete"),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> None:
    """Delete a project.

    Note: This deletes the project from the registry but does NOT delete
    the project's database file on disk.

    Args:
        project_id: ID of the project to delete.
        registry_conn: Registry database connection.

    Raises:
        HTTPException: 404 if project not found.
    """
    _get_project_or_404(registry_conn, project_id)
    delete_project(registry_conn, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_existing_project(
    project_id: int = PathParam(..., description="Project ID to update"),
    request: ProjectUpdateRequest = Body(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """Update a project's settings.

    Args:
        project_id: ID of the project to update.
        request: Update request with fields to change.
        registry_conn: Registry database connection.

    Returns:
        ProjectResponse: The updated project.

    Raises:
        HTTPException: 404 if project not found.
        HTTPException: 409 if name already exists.
    """
    _get_project_or_404(registry_conn, project_id)

    try:
        update_project(
            registry_conn,
            project_id,
            name=request.name,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            llm_base_url=request.llm_base_url,
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"Project name already exists: {request.name}"
        )

    updated_project = _get_project_or_404(registry_conn, project_id)
    return ProjectResponse.from_project(updated_project)
