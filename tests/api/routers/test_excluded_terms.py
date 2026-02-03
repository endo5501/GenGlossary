"""Tests for Excluded Terms API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection, transaction
from genglossary.db.excluded_term_repository import add_excluded_term
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


class TestListExcludedTerms:
    """Test GET /api/projects/{project_id}/excluded-terms."""

    def test_returns_empty_list_when_no_terms(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns empty list when no excluded terms exist."""
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/excluded-terms")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_all_excluded_terms(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns all excluded terms."""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Add some excluded terms
        conn = get_connection(project_db_path)
        with transaction(conn):
            add_excluded_term(conn, "一般名詞1", "auto")
            add_excluded_term(conn, "一般名詞2", "manual")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/excluded-terms")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        term_texts = [item["term_text"] for item in data["items"]]
        assert "一般名詞1" in term_texts
        assert "一般名詞2" in term_texts

    def test_returns_correct_fields(
        self, test_project_setup, client: TestClient
    ):
        """Test that returned items have correct fields."""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        with transaction(conn):
            add_excluded_term(conn, "テスト用語", "auto")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/excluded-terms")

        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]

        assert "id" in item
        assert item["term_text"] == "テスト用語"
        assert item["source"] == "auto"
        assert "created_at" in item

    def test_returns_404_for_missing_project(self, client: TestClient):
        """Test that endpoint returns 404 for non-existent project."""
        response = client.get("/api/projects/999/excluded-terms")

        assert response.status_code == 404


class TestCreateExcludedTerm:
    """Test POST /api/projects/{project_id}/excluded-terms."""

    def test_creates_new_excluded_term(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint creates a new excluded term."""
        project_id = test_project_setup["project_id"]

        payload = {"term_text": "除外する用語"}

        response = client.post(
            f"/api/projects/{project_id}/excluded-terms",
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["term_text"] == "除外する用語"
        assert data["source"] == "manual"  # Manual creation
        assert "created_at" in data

    def test_returns_existing_term_if_duplicate(
        self, test_project_setup, client: TestClient
    ):
        """Test that creating duplicate term returns existing term."""
        project_id = test_project_setup["project_id"]

        payload = {"term_text": "重複用語"}

        # First creation
        response1 = client.post(
            f"/api/projects/{project_id}/excluded-terms",
            json=payload,
        )
        assert response1.status_code == 201
        id1 = response1.json()["id"]

        # Second creation should return existing
        response2 = client.post(
            f"/api/projects/{project_id}/excluded-terms",
            json=payload,
        )
        assert response2.status_code == 200  # OK, not CREATED
        id2 = response2.json()["id"]

        assert id1 == id2

    def test_returns_400_for_empty_term_text(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns 400 for empty term_text."""
        project_id = test_project_setup["project_id"]

        payload = {"term_text": ""}

        response = client.post(
            f"/api/projects/{project_id}/excluded-terms",
            json=payload,
        )

        assert response.status_code == 422  # Validation error

    def test_returns_404_for_missing_project(self, client: TestClient):
        """Test that endpoint returns 404 for non-existent project."""
        payload = {"term_text": "用語"}

        response = client.post("/api/projects/999/excluded-terms", json=payload)

        assert response.status_code == 404


class TestDeleteExcludedTerm:
    """Test DELETE /api/projects/{project_id}/excluded-terms/{term_id}."""

    def test_deletes_existing_term(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint deletes an existing excluded term."""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Add a term to delete
        conn = get_connection(project_db_path)
        with transaction(conn):
            term_id = add_excluded_term(conn, "削除対象", "manual")
        conn.close()

        response = client.delete(
            f"/api/projects/{project_id}/excluded-terms/{term_id}"
        )

        assert response.status_code == 204

        # Verify deletion
        from genglossary.db.excluded_term_repository import term_exists_in_excluded

        conn = get_connection(project_db_path)
        exists = term_exists_in_excluded(conn, "削除対象")
        conn.close()

        assert exists is False

    def test_returns_404_for_missing_term(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns 404 for non-existent term."""
        project_id = test_project_setup["project_id"]

        response = client.delete(
            f"/api/projects/{project_id}/excluded-terms/999"
        )

        assert response.status_code == 404

    def test_returns_404_for_missing_project(self, client: TestClient):
        """Test that endpoint returns 404 for non-existent project."""
        response = client.delete("/api/projects/999/excluded-terms/1")

        assert response.status_code == 404
