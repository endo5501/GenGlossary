"""Tests for API dependency injection."""

import sqlite3
from pathlib import Path

import pytest

from genglossary.api.dependencies import (
    get_project_by_id,
    get_project_db,
    get_registry_db,
)
from genglossary.db.connection import get_connection
from genglossary.db.project_repository import create_project
from genglossary.db.registry_schema import initialize_registry


def test_get_registry_db_returns_connection(tmp_path: Path):
    """Test that get_registry_db returns a valid connection."""
    registry_path = tmp_path / "registry.db"
    conn = get_connection(str(registry_path))
    initialize_registry(conn)
    conn.close()

    # Test the generator
    gen = get_registry_db(str(registry_path))
    result = next(gen)

    assert isinstance(result, sqlite3.Connection)

    # Cleanup
    try:
        next(gen)
    except StopIteration:
        pass


def test_get_project_by_id_returns_project(tmp_path: Path):
    """Test that get_project_by_id returns a valid Project."""
    registry_path = tmp_path / "registry.db"
    project_db_path = tmp_path / "project.db"

    registry_conn = get_connection(str(registry_path))
    initialize_registry(registry_conn)

    project_id = create_project(
        registry_conn,
        name="Test Project",
        doc_root=str(tmp_path / "docs"),
        db_path=str(project_db_path),
    )

    project = get_project_by_id(project_id, registry_conn)

    assert project is not None
    assert project.id == project_id
    assert project.name == "Test Project"

    registry_conn.close()


def test_get_project_by_id_raises_404_for_missing_project(tmp_path: Path):
    """Test that get_project_by_id raises HTTPException for missing project."""
    from fastapi import HTTPException

    registry_path = tmp_path / "registry.db"
    registry_conn = get_connection(str(registry_path))
    initialize_registry(registry_conn)

    with pytest.raises(HTTPException) as exc_info:
        get_project_by_id(999, registry_conn)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()

    registry_conn.close()


def test_get_project_db_returns_connection(tmp_path: Path):
    """Test that get_project_db returns a valid connection."""
    registry_path = tmp_path / "registry.db"
    project_db_path = tmp_path / "project.db"

    registry_conn = get_connection(str(registry_path))
    initialize_registry(registry_conn)

    project_id = create_project(
        registry_conn,
        name="Test Project",
        doc_root=str(tmp_path / "docs"),
        db_path=str(project_db_path),
    )

    project = get_project_by_id(project_id, registry_conn)
    registry_conn.close()

    # Test the generator
    gen = get_project_db(project)
    result = next(gen)

    assert isinstance(result, sqlite3.Connection)

    # Cleanup
    try:
        next(gen)
    except StopIteration:
        pass
