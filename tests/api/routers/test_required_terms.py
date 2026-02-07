"""Tests for Required Terms API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection, transaction
from genglossary.db.project_repository import create_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.db.required_term_repository import add_required_term


@pytest.fixture
def test_project_setup(tmp_path: Path, monkeypatch):
    """Setup test project with registry and project database."""
    registry_path = tmp_path / "registry.db"
    project_db_path = tmp_path / "project.db"
    doc_root = tmp_path / "docs"
    doc_root.mkdir()

    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(registry_path))

    registry_conn = get_connection(str(registry_path))
    initialize_registry(registry_conn)

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


class TestListRequiredTerms:
    """Test GET /api/projects/{project_id}/required-terms."""

    def test_returns_empty_list_when_no_terms(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns empty list when no required terms exist."""
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/required-terms")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_all_required_terms(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns all required terms."""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        with transaction(conn):
            add_required_term(conn, "必須用語1", "manual")
            add_required_term(conn, "必須用語2", "manual")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/required-terms")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        term_texts = [item["term_text"] for item in data["items"]]
        assert "必須用語1" in term_texts
        assert "必須用語2" in term_texts

    def test_returns_correct_fields(
        self, test_project_setup, client: TestClient
    ):
        """Test that returned items have correct fields."""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        with transaction(conn):
            add_required_term(conn, "テスト用語", "manual")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/required-terms")

        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]

        assert "id" in item
        assert item["term_text"] == "テスト用語"
        assert item["source"] == "manual"
        assert "created_at" in item

    def test_returns_404_for_missing_project(self, client: TestClient):
        """Test that endpoint returns 404 for non-existent project."""
        response = client.get("/api/projects/999/required-terms")

        assert response.status_code == 404


class TestCreateRequiredTerm:
    """Test POST /api/projects/{project_id}/required-terms."""

    def test_creates_new_required_term(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint creates a new required term."""
        project_id = test_project_setup["project_id"]

        payload = {"term_text": "必須にする用語"}

        response = client.post(
            f"/api/projects/{project_id}/required-terms",
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["term_text"] == "必須にする用語"
        assert data["source"] == "manual"
        assert "created_at" in data

    def test_returns_existing_term_if_duplicate(
        self, test_project_setup, client: TestClient
    ):
        """Test that creating duplicate term returns existing term."""
        project_id = test_project_setup["project_id"]

        payload = {"term_text": "重複用語"}

        response1 = client.post(
            f"/api/projects/{project_id}/required-terms",
            json=payload,
        )
        assert response1.status_code == 201
        id1 = response1.json()["id"]

        response2 = client.post(
            f"/api/projects/{project_id}/required-terms",
            json=payload,
        )
        assert response2.status_code == 200
        id2 = response2.json()["id"]

        assert id1 == id2

    def test_returns_422_for_empty_term_text(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns 422 for empty term_text."""
        project_id = test_project_setup["project_id"]

        payload = {"term_text": ""}

        response = client.post(
            f"/api/projects/{project_id}/required-terms",
            json=payload,
        )

        assert response.status_code == 422

    def test_returns_404_for_missing_project(self, client: TestClient):
        """Test that endpoint returns 404 for non-existent project."""
        payload = {"term_text": "用語"}

        response = client.post("/api/projects/999/required-terms", json=payload)

        assert response.status_code == 404


class TestDeleteRequiredTerm:
    """Test DELETE /api/projects/{project_id}/required-terms/{term_id}."""

    def test_deletes_existing_term(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint deletes an existing required term."""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        with transaction(conn):
            term_id, _ = add_required_term(conn, "削除対象", "manual")
        conn.close()

        response = client.delete(
            f"/api/projects/{project_id}/required-terms/{term_id}"
        )

        assert response.status_code == 204

        from genglossary.db.required_term_repository import term_exists_in_required

        conn = get_connection(project_db_path)
        exists = term_exists_in_required(conn, "削除対象")
        conn.close()

        assert exists is False

    def test_returns_404_for_missing_term(
        self, test_project_setup, client: TestClient
    ):
        """Test that endpoint returns 404 for non-existent term."""
        project_id = test_project_setup["project_id"]

        response = client.delete(
            f"/api/projects/{project_id}/required-terms/999"
        )

        assert response.status_code == 404

    def test_returns_404_for_missing_project(self, client: TestClient):
        """Test that endpoint returns 404 for non-existent project."""
        response = client.delete("/api/projects/999/required-terms/1")

        assert response.status_code == 404
