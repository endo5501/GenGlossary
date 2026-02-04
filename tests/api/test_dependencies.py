"""Tests for API dependency injection."""

import sqlite3
from pathlib import Path

import pytest

from genglossary.api.dependencies import (
    get_project_by_id,
    get_project_db,
    get_registry_db,
)
from genglossary.db.connection import get_connection, transaction
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

    with transaction(registry_conn):
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

    with transaction(registry_conn):
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


def test_run_manager_singleton_per_project(tmp_path: Path):
    """Test that get_run_manager returns the same instance for the same project."""
    from genglossary.api.dependencies import get_run_manager
    from genglossary.models.project import Project
    from genglossary.db.schema import initialize_db

    # Create test projects
    project1_db = tmp_path / "project1.db"
    project2_db = tmp_path / "project2.db"

    # Initialize databases
    for db_path in [project1_db, project2_db]:
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

    # Create project instances
    project1 = Project(
        id=1,
        name="Project 1",
        doc_root=str(tmp_path / "docs1"),
        db_path=str(project1_db),
        llm_provider="ollama",
        llm_model="llama2",
    )
    project2 = Project(
        id=2,
        name="Project 2",
        doc_root=str(tmp_path / "docs2"),
        db_path=str(project2_db),
        llm_provider="ollama",
        llm_model="llama3",
    )

    # Get RunManager instances
    manager1_first = get_run_manager(project1)
    manager1_second = get_run_manager(project1)
    manager2 = get_run_manager(project2)

    # Verify same instance for same project
    assert manager1_first is manager1_second, "Should return same instance for same project"

    # Verify different instance for different project
    assert manager1_first is not manager2, "Should return different instance for different project"

    # Verify instances have correct configuration
    assert manager1_first.db_path == str(project1_db)
    assert manager1_first.doc_root == str(tmp_path / "docs1")
    assert manager1_first.llm_provider == "ollama"
    assert manager1_first.llm_model == "llama2"

    assert manager2.db_path == str(project2_db)
    assert manager2.doc_root == str(tmp_path / "docs2")
    assert manager2.llm_provider == "ollama"
    assert manager2.llm_model == "llama3"


def test_run_manager_recreates_when_settings_change_and_no_active_run(tmp_path: Path):
    """設定変更時、実行中のRunがなければ新しいRunManagerを作成"""
    from genglossary.api.dependencies import get_run_manager, _run_manager_registry
    from genglossary.models.project import Project
    from genglossary.db.schema import initialize_db
    from unittest.mock import patch

    # Create test project database
    project_db = tmp_path / "project.db"
    conn = get_connection(str(project_db))
    initialize_db(conn)
    conn.close()

    # Create project with initial settings
    project = Project(
        id=1,
        name="Test Project",
        doc_root=str(tmp_path / "docs"),
        db_path=str(project_db),
        llm_provider="ollama",
        llm_model="llama3.2",
    )

    # Clear registry
    _run_manager_registry.clear()

    # Get initial manager
    manager1 = get_run_manager(project)
    assert manager1.doc_root == str(tmp_path / "docs")
    assert manager1.llm_provider == "ollama"
    assert manager1.llm_model == "llama3.2"

    # Mock get_active_run to return None (no active run)
    with patch.object(manager1, "get_active_run", return_value=None):
        # Update project settings
        project.doc_root = str(tmp_path / "new_docs")
        project.llm_provider = "openai"
        project.llm_model = "gpt-4"

        # Get manager again - should be recreated with new settings
        manager2 = get_run_manager(project)

        assert manager2.doc_root == str(tmp_path / "new_docs")
        assert manager2.llm_provider == "openai"
        assert manager2.llm_model == "gpt-4"


def test_run_manager_keeps_old_instance_when_settings_change_and_run_active(tmp_path: Path):
    """設定変更時、実行中のRunがあれば既存のRunManagerを返す"""
    from genglossary.api.dependencies import get_run_manager, _run_manager_registry
    from genglossary.models.project import Project
    from genglossary.db.schema import initialize_db
    from unittest.mock import MagicMock, patch

    # Create test project database
    project_db = tmp_path / "project.db"
    conn = get_connection(str(project_db))
    initialize_db(conn)
    conn.close()

    # Create project with initial settings
    project = Project(
        id=1,
        name="Test Project",
        doc_root=str(tmp_path / "docs"),
        db_path=str(project_db),
        llm_provider="ollama",
        llm_model="llama3.2",
    )

    # Clear registry
    _run_manager_registry.clear()

    # Get initial manager
    manager1 = get_run_manager(project)
    assert manager1.doc_root == str(tmp_path / "docs")

    # Mock get_active_run to return an active run
    mock_active_run = MagicMock()
    mock_active_run.__getitem__.side_effect = lambda key: {"id": 1, "status": "running"}[key]

    with patch.object(manager1, "get_active_run", return_value=mock_active_run):
        # Update project settings
        project.doc_root = str(tmp_path / "new_docs")
        project.llm_provider = "openai"

        # Get manager again - should be same instance (no recreation)
        manager2 = get_run_manager(project)

        assert manager2 is manager1
        assert manager2.doc_root == str(tmp_path / "docs")  # Old settings preserved


def test_run_manager_has_llm_base_url(tmp_path: Path):
    """RunManagerにllm_base_urlが設定されることを確認"""
    from genglossary.api.dependencies import get_run_manager, _run_manager_registry
    from genglossary.models.project import Project
    from genglossary.db.schema import initialize_db

    # Create test project database
    project_db = tmp_path / "project.db"
    conn = get_connection(str(project_db))
    initialize_db(conn)
    conn.close()

    # Create project with llm_base_url
    project = Project(
        id=1,
        name="Test Project",
        doc_root=str(tmp_path / "docs"),
        db_path=str(project_db),
        llm_provider="openai",
        llm_model="gpt-4",
        llm_base_url="http://127.0.0.1:8080/v1",
    )

    # Clear registry
    _run_manager_registry.clear()

    # Get manager
    manager = get_run_manager(project)

    # Verify llm_base_url is set
    assert manager.llm_base_url == "http://127.0.0.1:8080/v1"


def test_run_manager_recreates_when_llm_base_url_changes(tmp_path: Path):
    """llm_base_url変更時、実行中のRunがなければ新しいRunManagerを作成"""
    from genglossary.api.dependencies import get_run_manager, _run_manager_registry
    from genglossary.models.project import Project
    from genglossary.db.schema import initialize_db
    from unittest.mock import patch

    # Create test project database
    project_db = tmp_path / "project.db"
    conn = get_connection(str(project_db))
    initialize_db(conn)
    conn.close()

    # Create project with initial llm_base_url
    project = Project(
        id=1,
        name="Test Project",
        doc_root=str(tmp_path / "docs"),
        db_path=str(project_db),
        llm_provider="openai",
        llm_model="gpt-4",
        llm_base_url="http://localhost:8080/v1",
    )

    # Clear registry
    _run_manager_registry.clear()

    # Get initial manager
    manager1 = get_run_manager(project)
    assert manager1.llm_base_url == "http://localhost:8080/v1"

    # Mock get_active_run to return None (no active run)
    with patch.object(manager1, "get_active_run", return_value=None):
        # Update llm_base_url only
        project.llm_base_url = "http://192.168.1.100:8080/v1"

        # Get manager again - should be recreated with new llm_base_url
        manager2 = get_run_manager(project)

        assert manager2.llm_base_url == "http://192.168.1.100:8080/v1"
        assert manager2 is not manager1
