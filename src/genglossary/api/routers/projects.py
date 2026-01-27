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
    ProjectUpdateRequest,
)
from genglossary.db.project_repository import (
    clone_project,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


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


@router.get("", response_model=list[ProjectResponse])
async def list_all_projects(
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> list[ProjectResponse]:
    """List all projects.

    Args:
        registry_conn: Registry database connection.

    Returns:
        list[ProjectResponse]: List of all projects, ordered by created_at desc.
    """
    projects = list_projects(registry_conn)
    return [ProjectResponse.from_project(p) for p in projects]


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
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return ProjectResponse.from_project(project)


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
    # Generate unique database path
    db_path = _generate_db_path(request.name)

    try:
        project_id = create_project(
            registry_conn,
            name=request.name,
            doc_root=request.doc_root,
            db_path=db_path,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"Project name already exists: {request.name}"
        )

    project = get_project(registry_conn, project_id)
    assert project is not None

    return ProjectResponse.from_project(project)


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
    # Generate unique database path for clone
    new_db_path = _generate_db_path(request.new_name)

    try:
        cloned_id = clone_project(
            registry_conn,
            source_id=project_id,
            new_name=request.new_name,
            new_db_path=new_db_path,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"Project name already exists: {request.new_name}"
        )

    project = get_project(registry_conn, cloned_id)
    assert project is not None

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
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

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
    """
    # Check if project exists
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Update fields
    update_project(
        registry_conn,
        project_id,
        llm_provider=request.llm_provider,
        llm_model=request.llm_model,
    )

    # Return updated project
    updated_project = get_project(registry_conn, project_id)
    assert updated_project is not None

    return ProjectResponse.from_project(updated_project)
