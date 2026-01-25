"""Tests for Issues API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection
from genglossary.db.issue_repository import create_issue
from genglossary.db.project_repository import create_project
from genglossary.db.registry_schema import initialize_registry


@pytest.fixture
def test_project_setup(tmp_path: Path, monkeypatch):
    """Setup test project with registry and project database."""
    registry_path = tmp_path / "registry.db"
    project_db_path = tmp_path / "project.db"
    doc_root = tmp_path / "docs"
    doc_root.mkdir()

    # Set registry path for client fixture
    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(registry_path))

    # Initialize registry
    registry_conn = get_connection(str(registry_path))
    initialize_registry(registry_conn)

    # Create project
    project_id = create_project(
        registry_conn,
        name="Test Project",
        doc_root=str(doc_root),
        db_path=str(project_db_path),
    )

    registry_conn.close()

    return {
        "project_id": project_id,
        "registry_path": str(registry_path),
        "project_db_path": str(project_db_path),
    }


def test_list_issues_returns_empty_list(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/issues returns empty list when no issues exist."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/issues")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_issues_returns_all_issues(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/issues returns all issues."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Add some issues
    conn = get_connection(project_db_path)
    issue1_id = create_issue(conn, "量子コンピュータ", "unclear", "定義が不明確")
    issue2_id = create_issue(conn, "量子ビット", "contradiction", "矛盾がある")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/issues")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == issue1_id
    assert data[0]["term_name"] == "量子コンピュータ"
    assert data[0]["issue_type"] == "unclear"
    assert data[0]["description"] == "定義が不明確"
    assert data[1]["id"] == issue2_id


def test_list_issues_filters_by_issue_type(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/issues?issue_type=X filters by issue type."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Add issues with different types
    conn = get_connection(project_db_path)
    issue1_id = create_issue(conn, "用語1", "unclear", "説明1")
    create_issue(conn, "用語2", "contradiction", "説明2")
    issue3_id = create_issue(conn, "用語3", "unclear", "説明3")
    conn.close()

    response = client.get(
        f"/api/projects/{project_id}/issues", params={"issue_type": "unclear"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == issue1_id
    assert data[0]["issue_type"] == "unclear"
    assert data[1]["id"] == issue3_id
    assert data[1]["issue_type"] == "unclear"


def test_get_issue_by_id_returns_issue(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/issues/{issue_id} returns specific issue."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    issue_id = create_issue(conn, "用語", "missing", "説明")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/issues/{issue_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == issue_id
    assert data["term_name"] == "用語"
    assert data["issue_type"] == "missing"
    assert data["description"] == "説明"


def test_get_issue_by_id_returns_404_for_missing_issue(
    test_project_setup, client: TestClient
):
    """Test GET /api/projects/{id}/issues/{issue_id} returns 404 for missing issue."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/issues/999")

    assert response.status_code == 404


def test_get_issues_returns_404_for_missing_project(client: TestClient):
    """Test GET /api/projects/{id}/issues returns 404 for missing project."""
    response = client.get("/api/projects/999/issues")

    assert response.status_code == 404
