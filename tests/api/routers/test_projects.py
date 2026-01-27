"""Tests for Projects API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection
from genglossary.db.document_repository import create_document
from genglossary.db.issue_repository import create_issue
from genglossary.db.project_repository import create_project
from genglossary.db.provisional_repository import create_provisional_term
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.term import TermOccurrence


@pytest.fixture
def test_registry_setup(tmp_path: Path, monkeypatch):
    """Setup test registry database."""
    registry_path = tmp_path / "registry.db"
    doc_root = tmp_path / "docs"
    doc_root.mkdir()

    # Set registry path for client fixture
    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(registry_path))

    # Initialize registry
    registry_conn = get_connection(str(registry_path))
    initialize_registry(registry_conn)
    registry_conn.close()

    return {
        "registry_path": str(registry_path),
        "doc_root": str(doc_root),
        "tmp_path": tmp_path,
    }


@pytest.fixture
def test_project_in_registry(test_registry_setup, tmp_path: Path):
    """Create a test project in the registry."""
    registry_path = test_registry_setup["registry_path"]
    doc_root = test_registry_setup["doc_root"]
    project_db_path = tmp_path / "projects" / "test_project.db"
    project_db_path.parent.mkdir(parents=True, exist_ok=True)

    registry_conn = get_connection(registry_path)
    project_id = create_project(
        registry_conn,
        name="Test Project",
        doc_root=doc_root,
        db_path=str(project_db_path),
        llm_provider="ollama",
        llm_model="llama3.2",
    )
    registry_conn.close()

    return {
        **test_registry_setup,
        "project_id": project_id,
        "project_db_path": str(project_db_path),
    }


class TestListProjects:
    """Tests for GET /api/projects."""

    def test_returns_empty_list_when_no_projects(
        self, test_registry_setup, client: TestClient
    ):
        """Test returns empty list when no projects exist."""
        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_returns_all_projects(self, test_project_in_registry, client: TestClient):
        """Test returns all projects."""
        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_project_in_registry["project_id"]
        assert data[0]["name"] == "Test Project"
        assert data[0]["llm_provider"] == "ollama"
        assert data[0]["llm_model"] == "llama3.2"
        assert data[0]["status"] == "created"

    def test_returns_projects_with_statistics(
        self, test_project_in_registry, client: TestClient
    ):
        """Test returns projects with document_count, term_count, issue_count."""
        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        project = data[0]
        # Verify statistics fields are present
        assert "document_count" in project
        assert "term_count" in project
        assert "issue_count" in project
        # Verify default values for empty project
        assert project["document_count"] == 0
        assert project["term_count"] == 0
        assert project["issue_count"] == 0

    def test_returns_projects_with_correct_statistics_counts(
        self, test_project_in_registry, client: TestClient
    ):
        """Test returns correct counts for documents, terms, and issues."""
        project_db_path = test_project_in_registry["project_db_path"]

        # Add data to project database
        project_conn = get_connection(project_db_path)
        # Add 2 documents
        create_document(project_conn, "/path/to/doc1.md", "hash1")
        create_document(project_conn, "/path/to/doc2.md", "hash2")
        # Add 3 provisional terms
        occurrence = TermOccurrence(
            document_path="/path/to/doc1.md",
            line_number=1,
            context="Test context",
        )
        create_provisional_term(project_conn, "term1", "def1", 0.9, [occurrence])
        create_provisional_term(project_conn, "term2", "def2", 0.8, [occurrence])
        create_provisional_term(project_conn, "term3", "def3", 0.7, [occurrence])
        # Add 1 issue
        create_issue(project_conn, "term1", "unclear", "Test issue description")
        project_conn.close()

        # Verify statistics
        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        project = data[0]
        assert project["document_count"] == 2
        assert project["term_count"] == 3
        assert project["issue_count"] == 1

    def test_returns_multiple_projects(
        self, test_registry_setup, client: TestClient, tmp_path: Path
    ):
        """Test returns multiple projects with correct data."""
        registry_path = test_registry_setup["registry_path"]
        doc_root = test_registry_setup["doc_root"]

        registry_conn = get_connection(registry_path)

        # Create multiple projects
        db_path1 = tmp_path / "projects" / "project1.db"
        db_path1.parent.mkdir(parents=True, exist_ok=True)
        create_project(
            registry_conn,
            name="First Project",
            doc_root=doc_root,
            db_path=str(db_path1),
        )

        db_path2 = tmp_path / "projects" / "project2.db"
        create_project(
            registry_conn,
            name="Second Project",
            doc_root=doc_root,
            db_path=str(db_path2),
        )
        registry_conn.close()

        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Verify both projects are returned with correct data
        names = {p["name"] for p in data}
        assert names == {"First Project", "Second Project"}
        # Verify all required fields are present
        for project in data:
            assert "id" in project
            assert "name" in project
            assert "doc_root" in project
            assert "created_at" in project
            assert "status" in project


class TestGetProject:
    """Tests for GET /api/projects/{id}."""

    def test_returns_project_by_id(self, test_project_in_registry, client: TestClient):
        """Test returns specific project by ID."""
        project_id = test_project_in_registry["project_id"]

        response = client.get(f"/api/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Test Project"
        assert data["llm_provider"] == "ollama"
        assert data["llm_model"] == "llama3.2"
        assert data["status"] == "created"
        assert "created_at" in data
        assert "updated_at" in data

    def test_returns_404_for_missing_project(
        self, test_registry_setup, client: TestClient
    ):
        """Test returns 404 for non-existent project."""
        response = client.get("/api/projects/999")

        assert response.status_code == 404


class TestCreateProject:
    """Tests for POST /api/projects."""

    def test_creates_new_project(
        self, test_registry_setup, client: TestClient, tmp_path: Path
    ):
        """Test creates a new project."""
        doc_root = test_registry_setup["doc_root"]

        payload = {
            "name": "New Project",
            "doc_root": doc_root,
            "llm_provider": "ollama",
            "llm_model": "llama3.2",
        }

        response = client.post("/api/projects", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "New Project"
        assert data["doc_root"] == doc_root
        assert data["llm_provider"] == "ollama"
        assert data["llm_model"] == "llama3.2"
        assert data["status"] == "created"

    def test_creates_project_with_defaults(
        self, test_registry_setup, client: TestClient
    ):
        """Test creates project with default values."""
        doc_root = test_registry_setup["doc_root"]

        payload = {
            "name": "Minimal Project",
            "doc_root": doc_root,
        }

        response = client.post("/api/projects", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["llm_provider"] == "ollama"
        assert data["llm_model"] == ""

    def test_returns_409_for_duplicate_name(
        self, test_project_in_registry, client: TestClient
    ):
        """Test returns 409 for duplicate project name."""
        doc_root = test_project_in_registry["doc_root"]

        payload = {
            "name": "Test Project",  # Same name as existing
            "doc_root": doc_root,
        }

        response = client.post("/api/projects", json=payload)

        assert response.status_code == 409

    def test_returns_400_for_empty_name(
        self, test_registry_setup, client: TestClient
    ):
        """Test returns 400 for empty project name."""
        doc_root = test_registry_setup["doc_root"]

        payload = {
            "name": "",
            "doc_root": doc_root,
        }

        response = client.post("/api/projects", json=payload)

        assert response.status_code == 422  # Pydantic validation error


class TestCloneProject:
    """Tests for POST /api/projects/{id}/clone."""

    def test_clones_project(self, test_project_in_registry, client: TestClient):
        """Test clones an existing project."""
        project_id = test_project_in_registry["project_id"]

        payload = {"new_name": "Cloned Project"}

        response = client.post(f"/api/projects/{project_id}/clone", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"] != project_id
        assert data["name"] == "Cloned Project"
        assert data["doc_root"] == test_project_in_registry["doc_root"]
        assert data["status"] == "created"  # Reset to created

    def test_returns_404_for_missing_source(
        self, test_registry_setup, client: TestClient
    ):
        """Test returns 404 when source project doesn't exist."""
        payload = {"new_name": "Cloned Project"}

        response = client.post("/api/projects/999/clone", json=payload)

        assert response.status_code == 404

    def test_returns_409_for_duplicate_name(
        self, test_project_in_registry, client: TestClient
    ):
        """Test returns 409 when cloned name already exists."""
        project_id = test_project_in_registry["project_id"]

        payload = {"new_name": "Test Project"}  # Same name as source

        response = client.post(f"/api/projects/{project_id}/clone", json=payload)

        assert response.status_code == 409


class TestDeleteProject:
    """Tests for DELETE /api/projects/{id}."""

    def test_deletes_project(self, test_project_in_registry, client: TestClient):
        """Test deletes a project."""
        project_id = test_project_in_registry["project_id"]

        response = client.delete(f"/api/projects/{project_id}")

        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 404

    def test_returns_404_for_missing_project(
        self, test_registry_setup, client: TestClient
    ):
        """Test returns 404 for non-existent project."""
        response = client.delete("/api/projects/999")

        assert response.status_code == 404


class TestUpdateProject:
    """Tests for PATCH /api/projects/{id}."""

    def test_updates_llm_provider(self, test_project_in_registry, client: TestClient):
        """Test updates LLM provider."""
        project_id = test_project_in_registry["project_id"]

        payload = {"llm_provider": "openai"}

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["llm_provider"] == "openai"
        assert data["llm_model"] == "llama3.2"  # Unchanged

    def test_updates_llm_model(self, test_project_in_registry, client: TestClient):
        """Test updates LLM model."""
        project_id = test_project_in_registry["project_id"]

        payload = {"llm_model": "gpt-4"}

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["llm_model"] == "gpt-4"
        assert data["llm_provider"] == "ollama"  # Unchanged

    def test_updates_multiple_fields(
        self, test_project_in_registry, client: TestClient
    ):
        """Test updates multiple fields at once."""
        project_id = test_project_in_registry["project_id"]

        payload = {
            "llm_provider": "openai",
            "llm_model": "gpt-4",
        }

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["llm_provider"] == "openai"
        assert data["llm_model"] == "gpt-4"

    def test_returns_404_for_missing_project(
        self, test_registry_setup, client: TestClient
    ):
        """Test returns 404 for non-existent project."""
        payload = {"llm_model": "gpt-4"}

        response = client.patch("/api/projects/999", json=payload)

        assert response.status_code == 404

    def test_updates_name(self, test_project_in_registry, client: TestClient):
        """Test updates project name."""
        project_id = test_project_in_registry["project_id"]

        payload = {"name": "Updated Name"}

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_returns_409_for_duplicate_name_on_update(
        self, test_project_in_registry, client: TestClient, tmp_path: Path
    ):
        """Test returns 409 when updating to an existing name."""
        registry_path = test_project_in_registry["registry_path"]
        doc_root = test_project_in_registry["doc_root"]
        project_id = test_project_in_registry["project_id"]

        # Create another project with a different name
        db_path2 = tmp_path / "projects" / "project2.db"
        db_path2.parent.mkdir(parents=True, exist_ok=True)
        registry_conn = get_connection(registry_path)
        create_project(
            registry_conn,
            name="Other Project",
            doc_root=doc_root,
            db_path=str(db_path2),
        )
        registry_conn.close()

        # Try to update to the other project's name
        payload = {"name": "Other Project"}

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 409

    def test_returns_422_for_empty_name_on_update(
        self, test_project_in_registry, client: TestClient
    ):
        """Test returns 422 for empty name validation error."""
        project_id = test_project_in_registry["project_id"]

        payload = {"name": ""}

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 422

    def test_updates_llm_base_url(self, test_project_in_registry, client: TestClient):
        """Test updates LLM base URL."""
        project_id = test_project_in_registry["project_id"]

        payload = {"llm_base_url": "https://api.openai.com/v1"}

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["llm_base_url"] == "https://api.openai.com/v1"

    def test_returns_422_for_invalid_base_url(
        self, test_project_in_registry, client: TestClient
    ):
        """Test returns 422 for invalid base URL format."""
        project_id = test_project_in_registry["project_id"]

        payload = {"llm_base_url": "not-a-valid-url"}

        response = client.patch(f"/api/projects/{project_id}", json=payload)

        assert response.status_code == 422
