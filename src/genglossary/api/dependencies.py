"""Dependency injection for API."""

import os
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Generator

from fastapi import Depends, HTTPException

from genglossary.config import Config
from genglossary.db.connection import get_connection
from genglossary.db.project_repository import get_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.db.schema import initialize_db
from genglossary.models.project import Project
from genglossary.runs.manager import RunManager

# RunManager registry: one instance per project (keyed by db_path)
_run_manager_registry: dict[str, RunManager] = {}
_registry_lock = Lock()


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

    Ensures the project database schema is up-to-date by running
    initialize_db, which applies any missing schema migrations.

    Args:
        project: Project instance from get_project_by_id.

    Yields:
        sqlite3.Connection: Project database connection.
    """
    conn = get_connection(project.db_path)
    initialize_db(conn)
    try:
        yield conn
    finally:
        conn.close()


def get_project_db_path(project: Project = Depends(get_project_by_id)) -> str:
    """Get project database path.

    Args:
        project: Project instance from get_project_by_id.

    Returns:
        str: Path to project database.
    """
    return project.db_path


def _settings_match(manager: RunManager, project: Project) -> bool:
    """Check if manager settings match project settings.

    Args:
        manager: RunManager instance to check.
        project: Project instance to compare against.

    Returns:
        bool: True if settings match.
    """
    return (
        manager.doc_root == project.doc_root
        and manager.llm_provider == project.llm_provider
        and manager.llm_model == project.llm_model
        and manager.llm_base_url == project.llm_base_url
    )


def _create_and_register_manager(project: Project) -> RunManager:
    """Create and register a new RunManager.

    Args:
        project: Project instance to create manager for.

    Returns:
        RunManager: Newly created manager instance.
    """
    manager = RunManager(
        db_path=project.db_path,
        doc_root=project.doc_root,
        llm_provider=project.llm_provider,
        llm_model=project.llm_model,
        llm_base_url=project.llm_base_url,
    )
    _run_manager_registry[project.db_path] = manager
    return manager


def get_run_manager(project: Project = Depends(get_project_by_id)) -> RunManager:
    """Get or create RunManager instance for the project (singleton per project).

    If project settings have changed, recreates the RunManager only if no run
    is currently active. If a run is active, returns the existing instance to
    avoid interrupting the running job.

    Args:
        project: Project instance from get_project_by_id.

    Returns:
        RunManager: RunManager instance for the project.
    """
    with _registry_lock:
        existing = _run_manager_registry.get(project.db_path)

        if existing is None:
            return _create_and_register_manager(project)

        if existing.get_active_run() is not None:
            return existing

        if _settings_match(existing, project):
            return existing

        return _create_and_register_manager(project)
