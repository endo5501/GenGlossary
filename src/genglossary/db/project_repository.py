"""Repository for projects table operations."""

import sqlite3
from datetime import datetime
from pathlib import Path

from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.models.project import Project, ProjectStatus


def _row_to_project(row: sqlite3.Row) -> Project:
    """Convert a database row to a Project model.

    Args:
        row: SQLite row from projects table.

    Returns:
        Project: Project model instance.
    """
    return Project(
        id=row["id"],
        name=row["name"],
        doc_root=row["doc_root"],
        db_path=row["db_path"],
        llm_provider=row["llm_provider"],
        llm_model=row["llm_model"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        last_run_at=(
            datetime.fromisoformat(row["last_run_at"])
            if row["last_run_at"]
            else None
        ),
        status=ProjectStatus(row["status"]),
    )


def create_project(
    conn: sqlite3.Connection,
    name: str,
    doc_root: str,
    db_path: str,
    llm_provider: str = "ollama",
    llm_model: str = "",
    status: ProjectStatus = ProjectStatus.CREATED,
) -> int:
    """Create a new project.

    Args:
        conn: Registry database connection.
        name: Project name (must be unique).
        doc_root: Absolute path to document directory.
        db_path: Absolute path to project database file.
        llm_provider: LLM provider name (default: "ollama").
        llm_model: LLM model name (default: "").
        status: Initial project status (default: CREATED).

    Returns:
        int: The ID of the newly created project.

    Raises:
        sqlite3.IntegrityError: If name or db_path already exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO projects (
            name, doc_root, db_path, llm_provider, llm_model, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, doc_root, db_path, llm_provider, llm_model, status.value),
    )
    conn.commit()

    project_id = cursor.lastrowid
    assert project_id is not None

    # Initialize the project database
    project_conn = get_connection(db_path)
    initialize_db(project_conn)
    project_conn.close()

    return project_id


def get_project(conn: sqlite3.Connection, project_id: int) -> Project | None:
    """Get a project by ID.

    Args:
        conn: Registry database connection.
        project_id: Project ID.

    Returns:
        Project if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()

    if row is None:
        return None

    return _row_to_project(row)


def get_project_by_name(conn: sqlite3.Connection, name: str) -> Project | None:
    """Get a project by name.

    Args:
        conn: Registry database connection.
        name: Project name.

    Returns:
        Project if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row is None:
        return None

    return _row_to_project(row)


def list_projects(conn: sqlite3.Connection) -> list[Project]:
    """List all projects ordered by created_at descending.

    Args:
        conn: Registry database connection.

    Returns:
        List of Project instances, most recent first.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = cursor.fetchall()

    return [_row_to_project(row) for row in rows]


def update_project(
    conn: sqlite3.Connection,
    project_id: int,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    status: ProjectStatus | None = None,
    last_run_at: datetime | None = None,
) -> None:
    """Update project fields.

    Args:
        conn: Registry database connection.
        project_id: Project ID to update.
        llm_provider: New LLM provider (optional).
        llm_model: New LLM model (optional).
        status: New status (optional).
        last_run_at: New last run timestamp (optional).

    Raises:
        ValueError: If project with the given ID does not exist.
    """
    # Check if project exists
    project = get_project(conn, project_id)
    if project is None:
        raise ValueError(f"Project with id {project_id} not found")

    # Build update query dynamically based on provided fields
    updates = []
    values = []

    if llm_provider is not None:
        updates.append("llm_provider = ?")
        values.append(llm_provider)

    if llm_model is not None:
        updates.append("llm_model = ?")
        values.append(llm_model)

    if status is not None:
        updates.append("status = ?")
        values.append(status.value)

    if last_run_at is not None:
        updates.append("last_run_at = ?")
        values.append(last_run_at.isoformat())

    # Always update updated_at
    updates.append("updated_at = datetime('now')")

    query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
    values.append(project_id)

    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()


def delete_project(conn: sqlite3.Connection, project_id: int) -> None:
    """Delete a project.

    Note: This does NOT delete the project's database file.
    That should be handled separately if needed.

    Args:
        conn: Registry database connection.
        project_id: Project ID to delete.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()


def clone_project(
    conn: sqlite3.Connection,
    source_id: int,
    new_name: str,
    new_db_path: str,
) -> int:
    """Clone an existing project.

    Creates a copy of the project with a new name and db_path.
    Resets status to CREATED and last_run_at to None.

    Args:
        conn: Registry database connection.
        source_id: ID of the project to clone.
        new_name: Name for the cloned project.
        new_db_path: Database path for the cloned project.

    Returns:
        int: The ID of the newly cloned project.

    Raises:
        ValueError: If source project does not exist.
        sqlite3.IntegrityError: If new_name or new_db_path already exists.
    """
    # Get source project
    source = get_project(conn, source_id)
    if source is None:
        raise ValueError(f"Project with id {source_id} not found")

    # Create new project with copied settings
    new_id = create_project(
        conn,
        name=new_name,
        doc_root=source.doc_root,
        db_path=new_db_path,
        llm_provider=source.llm_provider,
        llm_model=source.llm_model,
        status=ProjectStatus.CREATED,  # Reset status
    )

    # Note: last_run_at is automatically None for new projects

    return new_id
