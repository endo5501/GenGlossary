"""Tests for Terms API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection, transaction
from genglossary.db.project_repository import create_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.db.term_repository import create_term


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


def test_list_terms_returns_empty_list(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/terms returns empty list when no terms exist."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/terms")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_terms_returns_all_terms(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/terms returns all extracted terms."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Add some terms
    conn = get_connection(project_db_path)
    with transaction(conn):
        term1_id = create_term(conn, "量子コンピュータ", "技術")
        term2_id = create_term(conn, "量子ビット", "技術")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/terms")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == term1_id
    assert data[0]["term_text"] == "量子コンピュータ"
    assert data[0]["category"] == "技術"
    assert data[1]["id"] == term2_id
    assert data[1]["term_text"] == "量子ビット"


def test_get_term_by_id_returns_term(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/terms/{term_id} returns specific term."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        term_id = create_term(conn, "量子もつれ", "技術")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/terms/{term_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == term_id
    assert data["term_text"] == "量子もつれ"
    assert data["category"] == "技術"


def test_get_term_by_id_returns_404_for_missing_term(
    test_project_setup, client: TestClient
):
    """Test GET /api/projects/{id}/terms/{term_id} returns 404 for missing term."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/terms/999")

    assert response.status_code == 404


def test_create_term_adds_new_term(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/terms creates a new term."""
    project_id = test_project_setup["project_id"]

    payload = {"term_text": "重ね合わせ", "category": "技術"}

    response = client.post(f"/api/projects/{project_id}/terms", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["term_text"] == "重ね合わせ"
    assert data["category"] == "技術"


def test_update_term_modifies_existing_term(test_project_setup, client: TestClient):
    """Test PATCH /api/projects/{id}/terms/{term_id} updates term."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        term_id = create_term(conn, "旧用語", "旧カテゴリ")
    conn.close()

    payload = {"term_text": "新用語", "category": "新カテゴリ"}

    response = client.patch(
        f"/api/projects/{project_id}/terms/{term_id}", json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == term_id
    assert data["term_text"] == "新用語"
    assert data["category"] == "新カテゴリ"


def test_delete_term_removes_term(test_project_setup, client: TestClient):
    """Test DELETE /api/projects/{id}/terms/{term_id} removes term."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        term_id = create_term(conn, "削除対象", "技術")
    conn.close()

    response = client.delete(f"/api/projects/{project_id}/terms/{term_id}")

    assert response.status_code == 204

    # Verify deletion
    conn = get_connection(project_db_path)
    from genglossary.db.term_repository import get_term

    deleted_term = get_term(conn, term_id)
    assert deleted_term is None
    conn.close()


def test_list_terms_includes_user_notes(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/terms includes user_notes in response."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        create_term(conn, "GP", "abbreviation")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/terms")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_notes"] == ""


def test_get_term_includes_user_notes(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/terms/{term_id} includes user_notes."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        term_id = create_term(conn, "GP", "abbreviation")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/terms/{term_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["user_notes"] == ""


def test_update_term_user_notes(test_project_setup, client: TestClient):
    """Test PATCH /api/projects/{id}/terms/{term_id} updates user_notes."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        term_id = create_term(conn, "GP", "abbreviation")
    conn.close()

    payload = {
        "term_text": "GP",
        "category": "abbreviation",
        "user_notes": "General Practitioner（一般開業医）の略称",
    }

    response = client.patch(
        f"/api/projects/{project_id}/terms/{term_id}", json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_notes"] == "General Practitioner（一般開業医）の略称"


def test_get_terms_returns_404_for_missing_project(client: TestClient):
    """Test GET /api/projects/{id}/terms returns 404 for missing project."""
    response = client.get("/api/projects/999/terms")

    assert response.status_code == 404


def test_create_term_returns_409_for_duplicate_term(
    test_project_setup, client: TestClient
):
    """Test POST /api/projects/{id}/terms returns 409 for duplicate term."""
    project_id = test_project_setup["project_id"]

    # First creation should succeed
    payload = {"term_text": "重複用語", "category": "技術"}
    response = client.post(f"/api/projects/{project_id}/terms", json=payload)
    assert response.status_code == 201

    # Second creation should return 409 Conflict
    response = client.post(f"/api/projects/{project_id}/terms", json=payload)
    assert response.status_code == 409


def test_delete_term_returns_404_for_missing_term(
    test_project_setup, client: TestClient
):
    """Test DELETE /api/projects/{id}/terms/{term_id} returns 404 for missing term."""
    project_id = test_project_setup["project_id"]

    # Attempt to delete non-existent term
    response = client.delete(f"/api/projects/{project_id}/terms/999")

    assert response.status_code == 404
