"""Dependency injection for API."""

import os
import sqlite3
from pathlib import Path
from typing import Generator

from fastapi import Depends, HTTPException

from genglossary.config import Config
from genglossary.db.connection import get_connection
from genglossary.db.project_repository import get_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.project import Project


def get_config() -> Config:
    """Get application configuration.

    Returns:
        Config: Application configuration instance
    """
    return Config()


def get_registry_db(
    registry_path: str | None = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Get registry database connection.

    Args:
        registry_path: Optional path to registry database.
            If None, uses GENGLOSSARY_REGISTRY_PATH env var or default.

    Yields:
        sqlite3.Connection: Registry database connection.
    """
    if registry_path is None:
        registry_path = os.getenv(
            "GENGLOSSARY_REGISTRY_PATH",
            str(Path.home() / ".genglossary" / "registry.db"),
        )

    conn = get_connection(registry_path)
    initialize_registry(conn)

    try:
        yield conn
    finally:
        conn.close()


def get_project_by_id(
    project_id: int,
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> Project:
    """Get project by ID or raise 404.

    Args:
        project_id: Project ID to retrieve.
        registry_conn: Registry database connection.

    Returns:
        Project: The requested project.

    Raises:
        HTTPException: 404 if project not found.
    """
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def get_project_db(
    project: Project = Depends(get_project_by_id),
) -> Generator[sqlite3.Connection, None, None]:
    """Get project-specific database connection.

    Args:
        project: Project instance from get_project_by_id.

    Yields:
        sqlite3.Connection: Project database connection.
    """
    conn = get_connection(project.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_db_connection():
    """Get database connection (placeholder).

    This will be implemented in a future ticket when
    database integration is added.

    Returns:
        None: Placeholder for database connection
    """
    # TODO: Implement database connection
    return None
