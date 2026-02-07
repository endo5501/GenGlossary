"""Tests for Files API endpoints."""

from pathlib import Path
from unittest.mock import MagicMock, patch

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


def test_get_file_by_id_returns_document_with_content(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/files/{file_id} returns document with content."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    with transaction(conn):
        doc_id = create_document(conn, "test.txt", "Test content for viewer", "test_hash")
    conn.close()

    response = client.get(f"/api/projects/{project_id}/files/{doc_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["file_name"] == "test.txt"
    assert data["content_hash"] == "test_hash"
    assert data["content"] == "Test content for viewer"


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


def test_create_file_allows_double_dots_in_filename(test_project_setup, client: TestClient):
    """Test POST /api/projects/{id}/files allows .. in filename (not path segment)."""
    project_id = test_project_setup["project_id"]

    # Double dots in filename (not a path segment) should be allowed
    payload = {"file_name": "notes..md", "content": "content"}
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 201
    assert response.json()["file_name"] == "notes..md"


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
    assert len(data["files"]) == 2
    assert data["files"][0]["file_name"] == "file1.txt"
    assert data["files"][1]["file_name"] == "file2.md"


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


class TestWindowsDrivePathRejection:
    """Tests for Windows drive path rejection (e.g., C:/path/to/file.md)."""

    def test_create_file_rejects_windows_drive_path(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files rejects Windows drive paths."""
        project_id = test_project_setup["project_id"]

        # Windows drive path should be rejected (colon is now a forbidden char)
        payload = {"file_name": "C:/Windows/system32/file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_lowercase_drive_letter(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files rejects lowercase drive letters."""
        project_id = test_project_setup["project_id"]

        # Lowercase drive letter should also be rejected (colon is now a forbidden char)
        payload = {"file_name": "d:/path/to/file.txt", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_colon_anywhere(
        self, test_project_setup, client: TestClient
    ):
        """Test that colons are rejected in any position (Windows-invalid)."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "notes/2025-01-01: Meeting.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_files_bulk_rejects_windows_drive_path(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files/bulk rejects Windows drive paths."""
        project_id = test_project_setup["project_id"]

        # Colon in drive path is now caught by forbidden chars check
        payload = {
            "files": [
                {"file_name": "valid.md", "content": "content"},
                {"file_name": "E:/data/file.txt", "content": "bad"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400


class TestEmptySegmentNormalization:
    """Tests for empty segment normalization in file paths."""

    def test_create_file_normalizes_empty_segments(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files normalizes empty segments."""
        project_id = test_project_setup["project_id"]

        # Path with empty segments should be normalized
        payload = {"file_name": "a//b.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201
        assert response.json()["file_name"] == "a/b.md"

    def test_create_file_normalizes_multiple_empty_segments(
        self, test_project_setup, client: TestClient
    ):
        """Test normalization of multiple consecutive empty segments."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "a///b////c.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201
        assert response.json()["file_name"] == "a/b/c.md"

    def test_create_file_detects_duplicate_via_empty_segment_normalization(
        self, test_project_setup, client: TestClient
    ):
        """Test that normalized paths detect duplicates with empty segments."""
        project_id = test_project_setup["project_id"]

        # Create a file
        payload1 = {"file_name": "dir/file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload1)
        assert response.status_code == 201

        # Try to create same file with empty segments - should be duplicate
        payload2 = {"file_name": "dir//file.md", "content": "other"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload2)
        assert response.status_code == 409

    def test_create_files_bulk_normalizes_empty_segments(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files/bulk normalizes empty segments."""
        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "a//b.md", "content": "content1"},
                {"file_name": "x///y.txt", "content": "content2"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["files"][0]["file_name"] == "a/b.md"
        assert data["files"][1]["file_name"] == "x/y.txt"


class TestPathLengthLimits:
    """Tests for path length limits."""

    def test_create_file_rejects_segment_too_long(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files rejects segments over 255 bytes."""
        project_id = test_project_setup["project_id"]

        # Create a segment longer than 255 bytes
        long_segment = "a" * 256
        payload = {"file_name": f"{long_segment}.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "255" in response.json()["detail"] or "segment" in response.json()["detail"].lower()

    def test_create_file_rejects_path_too_long(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files rejects paths over 1024 bytes."""
        project_id = test_project_setup["project_id"]

        # Create a path longer than 1024 bytes (using multiple segments)
        segments = ["dir" + str(i) for i in range(200)]  # Each ~4-5 chars
        long_path = "/".join(segments) + "/file.md"
        assert len(long_path.encode("utf-8")) > 1024

        payload = {"file_name": long_path, "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "1024" in response.json()["detail"] or "path" in response.json()["detail"].lower()

    def test_create_file_accepts_max_segment_length(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files accepts exactly 255 byte segments."""
        project_id = test_project_setup["project_id"]

        # Create a segment of exactly 255 bytes (252 chars + ".md")
        segment = "a" * 252
        payload = {"file_name": f"{segment}.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201

    def test_create_file_rejects_unicode_segment_too_long(
        self, test_project_setup, client: TestClient
    ):
        """Test that segment length is measured in bytes, not characters."""
        project_id = test_project_setup["project_id"]

        # Japanese characters are 3 bytes each in UTF-8
        # 86 Japanese chars = 258 bytes > 255
        long_segment = "あ" * 86
        payload = {"file_name": f"{long_segment}.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_files_bulk_rejects_segment_too_long(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files/bulk rejects segments over 255 bytes."""
        project_id = test_project_setup["project_id"]

        long_segment = "a" * 256
        payload = {
            "files": [
                {"file_name": "valid.md", "content": "content"},
                {"file_name": f"{long_segment}.md", "content": "content"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400


class TestExtensionValidationEdgeCases:
    """Tests for extension validation edge cases."""

    def test_create_file_validates_extension_from_basename(
        self, test_project_setup, client: TestClient
    ):
        """Test that extension is validated from basename, not full path."""
        project_id = test_project_setup["project_id"]

        # Directory with dot should not affect extension validation
        payload = {"file_name": "dir.with.dot/readme.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201
        assert response.json()["file_name"] == "dir.with.dot/readme.md"

    def test_create_file_rejects_file_without_extension_in_dotted_dir(
        self, test_project_setup, client: TestClient
    ):
        """Test that file without extension is rejected even in dotted directory."""
        project_id = test_project_setup["project_id"]

        # File without extension in directory with dots
        payload = {"file_name": "dir.with.dot/readme", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "extension" in response.json()["detail"].lower()


class TestUnicodeNormalization:
    """Tests for Unicode normalization and look-alike character rejection."""

    def test_create_file_applies_nfc_normalization(
        self, test_project_setup, client: TestClient
    ):
        """Test that NFC normalization is applied to file names."""
        project_id = test_project_setup["project_id"]

        # NFD form: e + combining acute accent (é as two codepoints)
        nfd_name = "caf\u0065\u0301.md"  # "café.md" in NFD
        # NFC form: precomposed é (single codepoint)
        nfc_name = "caf\u00e9.md"  # "café.md" in NFC

        payload = {"file_name": nfd_name, "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201
        # Should be stored in NFC form
        assert response.json()["file_name"] == nfc_name

    def test_create_file_rejects_lookalike_slash_division(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+2215 DIVISION SLASH is rejected."""
        project_id = test_project_setup["project_id"]

        # U+2215 DIVISION SLASH (∕) looks like forward slash
        payload = {"file_name": "path\u2215file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "unicode" in response.json()["detail"].lower() or "character" in response.json()["detail"].lower()

    def test_create_file_rejects_lookalike_fullwidth_slash(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+FF0F FULLWIDTH SOLIDUS is rejected."""
        project_id = test_project_setup["project_id"]

        # U+FF0F FULLWIDTH SOLIDUS (／)
        payload = {"file_name": "path\uff0ffile.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_lookalike_fraction_slash(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+2044 FRACTION SLASH is rejected."""
        project_id = test_project_setup["project_id"]

        # U+2044 FRACTION SLASH (⁄)
        payload = {"file_name": "path\u2044file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_lookalike_big_solidus(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+29F8 BIG SOLIDUS is rejected."""
        project_id = test_project_setup["project_id"]

        # U+29F8 BIG SOLIDUS (⧸)
        payload = {"file_name": "path\u29f8file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_lookalike_one_dot_leader(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+2024 ONE DOT LEADER is rejected."""
        project_id = test_project_setup["project_id"]

        # U+2024 ONE DOT LEADER (․) looks like period
        payload = {"file_name": "file\u2024md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_lookalike_fullwidth_dot(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+FF0E FULLWIDTH FULL STOP is rejected."""
        project_id = test_project_setup["project_id"]

        # U+FF0E FULLWIDTH FULL STOP (．)
        payload = {"file_name": "file\uff0emd", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_lookalike_middle_dot(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+00B7 MIDDLE DOT is rejected."""
        project_id = test_project_setup["project_id"]

        # U+00B7 MIDDLE DOT (·)
        payload = {"file_name": "file\u00b7md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_trailing_space_in_segment(
        self, test_project_setup, client: TestClient
    ):
        """Test that trailing space in path segment is rejected."""
        project_id = test_project_setup["project_id"]

        # Trailing space in directory name
        payload = {"file_name": "dir /file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "trailing" in response.json()["detail"].lower() or "space" in response.json()["detail"].lower()

    def test_create_file_rejects_trailing_dot_in_segment(
        self, test_project_setup, client: TestClient
    ):
        """Test that trailing dot in path segment (not extension) is rejected."""
        project_id = test_project_setup["project_id"]

        # Trailing dot in directory name (Windows issue)
        payload = {"file_name": "dir./file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_file_rejects_trailing_space_in_basename(
        self, test_project_setup, client: TestClient
    ):
        """Test that trailing space in basename (after extension) is rejected."""
        project_id = test_project_setup["project_id"]

        # Filename ending with space (invalid on Windows)
        # Note: "file .md" is valid because space is not at the end
        payload = {"file_name": "file.md ", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_create_files_bulk_applies_nfc_normalization(
        self, test_project_setup, client: TestClient
    ):
        """Test that bulk create applies NFC normalization."""
        project_id = test_project_setup["project_id"]

        nfd_name = "caf\u0065\u0301.md"
        nfc_name = "caf\u00e9.md"

        payload = {"files": [{"file_name": nfd_name, "content": "content"}]}
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 201
        assert response.json()["files"][0]["file_name"] == nfc_name

    def test_create_files_bulk_rejects_lookalike_characters(
        self, test_project_setup, client: TestClient
    ):
        """Test that bulk create rejects look-alike characters."""
        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "valid.md", "content": "content"},
                {"file_name": "path\u2215file.md", "content": "content"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400

    def test_create_files_bulk_rejects_trailing_space(
        self, test_project_setup, client: TestClient
    ):
        """Test that bulk create rejects trailing space in segments."""
        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "valid.md", "content": "content"},
                {"file_name": "dir /file.md", "content": "content"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400


class TestBulkCreateIntegrityError:
    """Tests for bulk create IntegrityError handling."""

    def test_create_files_bulk_returns_409_on_integrity_error(
        self, test_project_setup, client: TestClient, monkeypatch
    ):
        """Test POST /api/projects/{id}/files/bulk returns 409 on IntegrityError."""
        import sqlite3
        from genglossary.api.routers import files as files_router
        from genglossary.db.document_repository import create_document as original_create

        project_id = test_project_setup["project_id"]

        # Mock create_document to raise IntegrityError (simulating race condition)
        call_count = 0

        def mock_create(conn, name, content, hash):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Fail on second file
                raise sqlite3.IntegrityError("UNIQUE constraint failed")
            return original_create(conn, name, content, hash)

        monkeypatch.setattr(files_router, "create_document", mock_create)

        payload = {
            "files": [
                {"file_name": "file1.md", "content": "content1"},
                {"file_name": "file2.md", "content": "content2"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 409


class TestPathValidationEnhancement:
    """Tests for absolute path rejection and path normalization."""

    def test_create_file_rejects_absolute_path(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files rejects absolute paths."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "/etc/passwd.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "absolute" in response.json()["detail"].lower()

    def test_create_file_normalizes_dot_segments(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files normalizes . segments in path."""
        project_id = test_project_setup["project_id"]

        # Path with . segments should be normalized
        payload = {"file_name": "./chapter1/./intro.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201
        # The stored file_name should be normalized
        assert response.json()["file_name"] == "chapter1/intro.md"

    def test_create_file_detects_duplicate_via_normalization(
        self, test_project_setup, client: TestClient
    ):
        """Test that normalized paths are used for duplicate detection."""
        project_id = test_project_setup["project_id"]

        # Create a file
        payload1 = {"file_name": "chapter1/intro.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload1)
        assert response.status_code == 201

        # Try to create same file with . segments - should be detected as duplicate
        payload2 = {"file_name": "./chapter1/./intro.md", "content": "other content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload2)
        assert response.status_code == 409

    def test_create_files_bulk_rejects_absolute_path(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files/bulk rejects absolute paths."""
        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "valid.md", "content": "content"},
                {"file_name": "/etc/passwd.md", "content": "bad"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400
        assert "absolute" in response.json()["detail"].lower()

    def test_create_files_bulk_normalizes_paths(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files/bulk normalizes paths."""
        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "./file1.md", "content": "content1"},
                {"file_name": "dir/./file2.md", "content": "content2"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["files"][0]["file_name"] == "file1.md"
        assert data["files"][1]["file_name"] == "dir/file2.md"

    def test_create_files_bulk_detects_duplicate_via_normalization(
        self, test_project_setup, client: TestClient
    ):
        """Test that bulk create detects duplicates after normalization."""
        project_id = test_project_setup["project_id"]

        # These are the same file after normalization
        payload = {
            "files": [
                {"file_name": "chapter/intro.md", "content": "content1"},
                {"file_name": "./chapter/./intro.md", "content": "content2"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower()


class TestContentSizeLimit:
    """Tests for content size limit (3MB)."""

    def test_create_file_rejects_content_too_large(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files rejects content over 3MB."""
        project_id = test_project_setup["project_id"]

        # Create content larger than 3MB (3 * 1024 * 1024 = 3145728 bytes)
        large_content = "a" * (3 * 1024 * 1024 + 1)
        payload = {"file_name": "large.txt", "content": large_content}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_create_file_accepts_content_at_limit(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files accepts content exactly at 3MB."""
        project_id = test_project_setup["project_id"]

        # Create content of exactly 3MB
        content_at_limit = "a" * (3 * 1024 * 1024)
        payload = {"file_name": "at_limit.txt", "content": content_at_limit}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201

    def test_create_file_measures_size_in_bytes(
        self, test_project_setup, client: TestClient
    ):
        """Test that content size is measured in bytes, not characters."""
        project_id = test_project_setup["project_id"]

        # Japanese characters are 3 bytes each in UTF-8
        # 1048577 Japanese chars = 3145731 bytes > 3MB
        large_unicode_content = "あ" * 1048577
        payload = {"file_name": "unicode_large.txt", "content": large_unicode_content}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_create_files_bulk_rejects_content_too_large(
        self, test_project_setup, client: TestClient
    ):
        """Test POST /api/projects/{id}/files/bulk rejects content over 3MB."""
        project_id = test_project_setup["project_id"]

        large_content = "a" * (3 * 1024 * 1024 + 1)
        payload = {
            "files": [
                {"file_name": "small.txt", "content": "small content"},
                {"file_name": "large.txt", "content": large_content},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_create_file_error_message_includes_size_info(
        self, test_project_setup, client: TestClient
    ):
        """Test that error message includes actual and max size."""
        project_id = test_project_setup["project_id"]

        large_content = "a" * (3 * 1024 * 1024 + 100)
        payload = {"file_name": "large.txt", "content": large_content}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400
        detail = response.json()["detail"]
        # Should include the actual size and max size
        assert "3145828" in detail  # actual size
        assert "3145728" in detail or "3MB" in detail  # max size


class TestSecurityCharacterValidation:
    """Tests for control characters, bidi overrides, and security validation."""

    # Control character tests
    def test_rejects_null_character(self, test_project_setup, client: TestClient):
        """Test that NUL character (U+0000) is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\x00name.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_newline_in_filename(self, test_project_setup, client: TestClient):
        """Test that newline character is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\nname.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_c1_control_character(self, test_project_setup, client: TestClient):
        """Test that C1 control characters (U+0080-U+009F) are rejected."""
        project_id = test_project_setup["project_id"]

        # U+0085 NEXT LINE (NEL)
        payload = {"file_name": "file\x85name.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    # Bidi and zero-width character tests
    def test_rejects_rtl_override(self, test_project_setup, client: TestClient):
        """Test that U+202E RIGHT-TO-LEFT OVERRIDE is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u202ename.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_zero_width_space(self, test_project_setup, client: TestClient):
        """Test that U+200B ZERO WIDTH SPACE is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u200bname.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_zero_width_joiner(self, test_project_setup, client: TestClient):
        """Test that U+200D ZERO WIDTH JOINER is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u200dname.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    # Look-alike character extension tests
    def test_rejects_cjk_fullstop(self, test_project_setup, client: TestClient):
        """Test that U+3002 IDEOGRAPHIC FULL STOP is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u3002md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_halfwidth_fullstop(self, test_project_setup, client: TestClient):
        """Test that U+FF61 HALFWIDTH IDEOGRAPHIC FULL STOP is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\uff61md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    # Unicode whitespace trailing tests
    def test_rejects_trailing_nbsp(self, test_project_setup, client: TestClient):
        """Test that trailing U+00A0 NO-BREAK SPACE is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "dir\u00a0/file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_trailing_ideographic_space(
        self, test_project_setup, client: TestClient
    ):
        """Test that trailing U+3000 IDEOGRAPHIC SPACE is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "dir\u3000/file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    # Windows reserved name tests
    def test_rejects_con_device_name(self, test_project_setup, client: TestClient):
        """Test that CON device name is rejected as filename."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "CON.txt", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_com1_device_name(self, test_project_setup, client: TestClient):
        """Test that COM1 device name is rejected as filename."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "com1.txt", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_allows_con_in_directory(self, test_project_setup, client: TestClient):
        """Test that CON is allowed as directory name."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "CON/file.txt", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201

    def test_allows_con_as_substring(self, test_project_setup, client: TestClient):
        """Test that CON as substring in filename is allowed."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "CONTEXT.txt", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 201

    # Additional Bidi isolate and format character tests
    def test_rejects_left_to_right_isolate(self, test_project_setup, client: TestClient):
        """Test that U+2066 LEFT-TO-RIGHT ISOLATE is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u2066name.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_pop_directional_isolate(
        self, test_project_setup, client: TestClient
    ):
        """Test that U+2069 POP DIRECTIONAL ISOLATE is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u2069name.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_arabic_letter_mark(self, test_project_setup, client: TestClient):
        """Test that U+061C ARABIC LETTER MARK is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u061cname.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_rejects_word_joiner(self, test_project_setup, client: TestClient):
        """Test that U+2060 WORD JOINER is rejected."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": "file\u2060name.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400


class TestWindowsInvalidCharacters:
    """Tests for Windows-invalid character blocking (:, <, >, \", |, ?, *)."""

    @pytest.mark.parametrize(
        "char,desc",
        [
            ("<", "less-than"),
            (">", "greater-than"),
            ('"', "double-quote"),
            ("|", "pipe"),
            ("?", "question-mark"),
            ("*", "asterisk"),
            (":", "colon"),
        ],
    )
    def test_rejects_windows_invalid_char_in_filename(
        self, test_project_setup, client: TestClient, char: str, desc: str
    ):
        """Test that Windows-invalid characters are rejected in filenames."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": f"file{char}name.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400, f"Expected 400 for {desc} ({char!r})"

    @pytest.mark.parametrize(
        "char,desc",
        [
            ("<", "less-than"),
            (">", "greater-than"),
            ('"', "double-quote"),
            ("|", "pipe"),
            ("?", "question-mark"),
            ("*", "asterisk"),
            (":", "colon"),
        ],
    )
    def test_rejects_windows_invalid_char_in_directory(
        self, test_project_setup, client: TestClient, char: str, desc: str
    ):
        """Test that Windows-invalid characters are rejected in directory names."""
        project_id = test_project_setup["project_id"]

        payload = {"file_name": f"dir{char}name/file.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400, f"Expected 400 for {desc} ({char!r})"

    def test_rejects_ads_pattern(self, test_project_setup, client: TestClient):
        """Test that NTFS Alternate Data Stream pattern is rejected."""
        project_id = test_project_setup["project_id"]

        # ADS pattern: file.txt:stream - blocked because colon is forbidden
        payload = {"file_name": "file.txt:hidden.md", "content": "content"}
        response = client.post(f"/api/projects/{project_id}/files", json=payload)

        assert response.status_code == 400

    def test_bulk_rejects_windows_invalid_chars(
        self, test_project_setup, client: TestClient
    ):
        """Test that bulk create rejects Windows-invalid characters."""
        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "valid.md", "content": "content"},
                {"file_name": "file<name.md", "content": "content"},
            ]
        }
        response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)

        assert response.status_code == 400


class TestCreateFilesBulkAutoExtract:
    """Tests for auto-extract trigger on bulk file creation."""

    def test_create_files_bulk_triggers_extract(
        self, test_project_setup, client: TestClient
    ):
        """ファイル追加成功後にExtractが自動的に開始される"""
        from genglossary.api.dependencies import get_run_manager

        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "file1.txt", "content": "Content 1"},
            ]
        }

        mock_manager = MagicMock()
        mock_manager.start_run.return_value = 42  # run_id

        client.app.dependency_overrides[get_run_manager] = lambda: mock_manager
        try:
            response = client.post(
                f"/api/projects/{project_id}/files/bulk", json=payload
            )
        finally:
            client.app.dependency_overrides.pop(get_run_manager, None)

        assert response.status_code == 201
        data = response.json()

        # Response should include extract_started flag
        assert data["extract_started"] is True
        assert data["extract_skipped_reason"] is None

        # Files should be in the response
        assert len(data["files"]) == 1
        assert data["files"][0]["file_name"] == "file1.txt"

        # RunManager.start_run should have been called with extract scope
        mock_manager.start_run.assert_called_once_with(
            scope="extract", triggered_by="auto"
        )

    def test_create_files_bulk_skips_extract_when_run_active(
        self, test_project_setup, client: TestClient
    ):
        """既にRunが実行中の場合、ファイル保存は成功しExtractはスキップされる"""
        from genglossary.api.dependencies import get_run_manager

        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "file1.txt", "content": "Content 1"},
            ]
        }

        mock_manager = MagicMock()
        mock_manager.start_run.side_effect = RuntimeError(
            "Run already running: 10"
        )

        client.app.dependency_overrides[get_run_manager] = lambda: mock_manager
        try:
            response = client.post(
                f"/api/projects/{project_id}/files/bulk", json=payload
            )
        finally:
            client.app.dependency_overrides.pop(get_run_manager, None)

        assert response.status_code == 201
        data = response.json()

        # Extract should be skipped but files saved
        assert data["extract_started"] is False
        # Sanitized message: no raw exception details exposed
        assert data["extract_skipped_reason"] is not None
        assert "Run already running: 10" not in data["extract_skipped_reason"]

        # Files should still be created
        assert len(data["files"]) == 1
        assert data["files"][0]["file_name"] == "file1.txt"

    def test_create_files_bulk_handles_unexpected_extract_error(
        self, test_project_setup, client: TestClient
    ):
        """start_runが予期しない例外を投げてもファイル保存は成功しextract_startedはfalseになる"""
        from genglossary.api.dependencies import get_run_manager

        project_id = test_project_setup["project_id"]

        payload = {
            "files": [
                {"file_name": "file1.txt", "content": "Content 1"},
            ]
        }

        mock_manager = MagicMock()
        mock_manager.start_run.side_effect = Exception(
            "Unexpected DB connection failure"
        )

        client.app.dependency_overrides[get_run_manager] = lambda: mock_manager
        try:
            response = client.post(
                f"/api/projects/{project_id}/files/bulk", json=payload
            )
        finally:
            client.app.dependency_overrides.pop(get_run_manager, None)

        assert response.status_code == 201
        data = response.json()

        # Extract should be skipped with sanitized message
        assert data["extract_started"] is False
        assert data["extract_skipped_reason"] is not None
        # Raw exception message must not leak to client
        assert "Unexpected DB connection failure" not in data["extract_skipped_reason"]

        # Files should still be created
        assert len(data["files"]) == 1
        assert data["files"][0]["file_name"] == "file1.txt"
