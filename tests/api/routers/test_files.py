"""Tests for Files API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection, transaction
from genglossary.db.document_repository import create_document
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
        "doc_root": str(doc_root),
    }


def test_list_files_returns_empty_list(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/files returns empty list when no files exist."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/files")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_files_returns_all_documents(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/files returns all documents."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Add some documents
    conn = get_connection(project_db_path)
    with transaction(conn):
        doc1_id = create_document(conn, "doc1.txt", "Content 1", "hash1")
        doc2_id = create_document(conn, "doc2.md", "Content 2", "hash2")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/files")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == doc1_id
    assert data[0]["file_name"] == "doc1.txt"
    assert data[0]["content_hash"] == "hash1"
    assert data[1]["id"] == doc2_id
    assert data[1]["file_name"] == "doc2.md"


def test_get_file_by_id_returns_document(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/files/{file_id} returns specific document."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        doc_id = create_document(conn, "test.txt", "Test content", "test_hash")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/files/{doc_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["file_name"] == "test.txt"
    assert data["content_hash"] == "test_hash"


def test_get_file_by_id_returns_404_for_missing_file(
    test_project_setup, client: TestClient
):
    """Test GET /api/projects/{id}/files/{file_id} returns 404 for missing file."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/files/999")

    assert response.status_code == 404


def test_create_file_adds_new_document_with_content(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files creates a new document with content."""
    project_id = test_project_setup["project_id"]

    payload = {"file_name": "new_doc.txt", "content": "This is test content."}

    response = client.post(f"/api/projects/{project_id}/files", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["file_name"] == "new_doc.txt"
    assert "content_hash" in data


def test_create_file_rejects_invalid_extension(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files rejects non txt/md files."""
    project_id = test_project_setup["project_id"]

    payload = {"file_name": "script.py", "content": "print('hello')"}

    response = client.post(f"/api/projects/{project_id}/files", json=payload)

    assert response.status_code == 400
    assert "extension" in response.json()["detail"].lower()


def test_create_file_accepts_relative_path(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files accepts relative paths with forward slashes."""
    project_id = test_project_setup["project_id"]

    # Relative path with forward slashes should be accepted
    payload = {"file_name": "chapter1/intro.txt", "content": "content"}
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 201
    assert response.json()["file_name"] == "chapter1/intro.txt"


def test_create_file_rejects_path_traversal(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files rejects path traversal attempts."""
    project_id = test_project_setup["project_id"]

    # Path traversal with .. should be rejected
    payload = {"file_name": "../secret.txt", "content": "content"}
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 400
    assert ".." in response.json()["detail"]

    # Path traversal in middle of path
    payload = {"file_name": "chapter1/../../../etc/passwd.txt", "content": "content"}
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 400


def test_create_file_rejects_backslash(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files rejects Windows-style backslashes."""
    project_id = test_project_setup["project_id"]

    # Backslash should be rejected (POSIX format only)
    payload = {"file_name": "path\\to\\file.txt", "content": "content"}
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 400
    assert "forward" in response.json()["detail"].lower() or "slash" in response.json()["detail"].lower()


def test_create_file_returns_409_for_duplicate_file(
    test_project_setup, client: TestClient
):
    """Test POST /api/projects/{id}/files returns 409 for duplicate file."""
    project_id = test_project_setup["project_id"]

    payload = {"file_name": "duplicate.txt", "content": "Content 1"}

    # First creation should succeed
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 201

    # Second creation should return 409 Conflict
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 409


def test_create_files_bulk_adds_multiple_documents(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files/bulk creates multiple documents."""
    project_id = test_project_setup["project_id"]

    payload = {
        "files": [
            {"file_name": "file1.txt", "content": "Content 1"},
            {"file_name": "file2.md", "content": "# Markdown content"},
        ]
    }

    response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["file_name"] == "file1.txt"
    assert data[1]["file_name"] == "file2.md"


def test_create_files_bulk_returns_400_for_invalid_extension(
    test_project_setup, client: TestClient
):
    """Test POST /api/projects/{id}/files/bulk rejects invalid extensions."""
    project_id = test_project_setup["project_id"]

    payload = {
        "files": [
            {"file_name": "valid.txt", "content": "Content"},
            {"file_name": "invalid.py", "content": "print('x')"},
        ]
    }

    response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

    assert response.status_code == 400


def test_create_files_bulk_rolls_back_on_duplicate(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files/bulk rolls back all on duplicate."""
    project_id = test_project_setup["project_id"]

    # First create one file
    payload1 = {"file_name": "existing.txt", "content": "Existing"}
    response = client.post(f"/api/projects/{project_id}/files", json=payload1)
    assert response.status_code == 201

    # Now try bulk with duplicate
    payload2 = {
        "files": [
            {"file_name": "new.txt", "content": "New"},
            {"file_name": "existing.txt", "content": "Duplicate"},
        ]
    }
    response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload2)

    assert response.status_code == 409

    # Verify new.txt was not created (rolled back)
    response = client.get(f"/api/projects/{project_id}/files")
    files = response.json()
    assert len(files) == 1  # Only existing.txt should exist


def test_delete_file_removes_document(test_project_setup, client: TestClient):
    """Test DELETE /api/projects/{id}/files/{file_id} removes document."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        doc_id = create_document(conn, "delete_me.txt", "To be deleted", "hash")
    conn.close()

    response = client.delete(f"/api/projects/{project_id}/files/{doc_id}")

    assert response.status_code == 204

    # Verify deletion
    conn = get_connection(project_db_path)
    from genglossary.db.document_repository import get_document

    deleted_doc = get_document(conn, doc_id)
    assert deleted_doc is None
    conn.close()


def test_delete_file_returns_404_for_missing_file(
    test_project_setup, client: TestClient
):
    """Test DELETE /api/projects/{id}/files/{file_id} returns 404 for missing file."""
    project_id = test_project_setup["project_id"]

    response = client.delete(f"/api/projects/{project_id}/files/999")

    assert response.status_code == 404


def test_get_files_returns_404_for_missing_project(client: TestClient):
    """Test GET /api/projects/{id}/files returns 404 for missing project."""
    response = client.get("/api/projects/999/files")

    assert response.status_code == 404
