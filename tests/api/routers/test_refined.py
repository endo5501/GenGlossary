"""Tests for Refined API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection, transaction
from genglossary.db.project_repository import create_project
from genglossary.db.refined_repository import create_refined_term
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.term import TermOccurrence


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
    with transaction(registry_conn):
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


def test_list_refined_returns_empty_list(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/refined returns empty list when no terms exist."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/refined")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_refined_returns_all_terms(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/refined returns all refined terms."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Add some refined terms
    conn = get_connection(project_db_path)
    occ1 = TermOccurrence(document_path="doc1.txt", line_number=1, context="context1")
    occ2 = TermOccurrence(document_path="doc2.txt", line_number=5, context="context2")

    with transaction(conn):
        term1_id = create_refined_term(
            conn, "量子コンピュータ", "量子力学を利用したコンピュータ", 0.95, [occ1]
        )
        term2_id = create_refined_term(
            conn, "量子ビット", "量子情報の基本単位", 0.92, [occ2]
        )
    conn.close()

    response = client.get(f"/api/projects/{project_id}/refined")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == term1_id
    assert data[0]["term_name"] == "量子コンピュータ"
    assert data[0]["definition"] == "量子力学を利用したコンピュータ"
    assert data[0]["confidence"] == 0.95
    assert len(data[0]["occurrences"]) == 1
    assert data[1]["id"] == term2_id


def test_get_refined_by_id_returns_term(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/refined/{term_id} returns specific term."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=3, context="context")
    with transaction(conn):
        term_id = create_refined_term(conn, "量子もつれ", "量子力学の現象", 0.98, [occ])
    conn.close()

    response = client.get(f"/api/projects/{project_id}/refined/{term_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == term_id
    assert data["term_name"] == "量子もつれ"
    assert data["definition"] == "量子力学の現象"
    assert data["confidence"] == 0.98


def test_get_refined_by_id_returns_404_for_missing_term(
    test_project_setup, client: TestClient
):
    """Test GET /api/projects/{id}/refined/{term_id} returns 404 for missing term."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/refined/999")

    assert response.status_code == 404


def test_export_markdown_returns_markdown_content(
    test_project_setup, client: TestClient
):
    """Test GET /api/projects/{id}/refined/export-md returns Markdown."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Add some refined terms
    conn = get_connection(project_db_path)
    occ1 = TermOccurrence(
        document_path="doc1.txt", line_number=1, context="量子コンピュータは..."
    )
    with transaction(conn):
        create_refined_term(conn, "量子コンピュータ", "量子力学を利用したコンピュータ", 0.95, [occ1])
    conn.close()

    response = client.get(f"/api/projects/{project_id}/refined/export-md")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    content = response.text
    assert "量子コンピュータ" in content
    assert "量子力学を利用したコンピュータ" in content
    assert "doc1.txt:1" in content


def test_export_markdown_returns_empty_for_no_terms(
    test_project_setup, client: TestClient
):
    """Test GET /api/projects/{id}/refined/export-md returns empty markdown when no terms."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/refined/export-md")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"


def test_get_refined_returns_404_for_missing_project(client: TestClient):
    """Test GET /api/projects/{id}/refined returns 404 for missing project."""
    response = client.get("/api/projects/999/refined")

    assert response.status_code == 404
