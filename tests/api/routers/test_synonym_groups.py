"""Tests for Synonym Groups API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection, transaction
from genglossary.db.project_repository import create_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.db.schema import initialize_db
from genglossary.db.synonym_repository import create_group


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


class TestListSynonymGroups:
    """Test GET /api/projects/{project_id}/synonym-groups."""

    def test_returns_empty_list_when_no_groups(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/synonym-groups")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_all_groups_with_members(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            create_group(conn, "田中太郎", ["田中太郎", "田中", "田中部長"])
        conn.close()

        response = client.get(f"/api/projects/{project_id}/synonym-groups")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        group = data["items"][0]
        assert group["primary_term_text"] == "田中太郎"
        assert len(group["members"]) == 3


class TestCreateSynonymGroup:
    """Test POST /api/projects/{project_id}/synonym-groups."""

    def test_creates_new_group(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]

        payload = {
            "primary_term_text": "サーバー",
            "member_texts": ["サーバー", "サーバ"],
        }

        response = client.post(
            f"/api/projects/{project_id}/synonym-groups",
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["primary_term_text"] == "サーバー"
        assert len(data["members"]) == 2

    def test_returns_409_for_duplicate_member(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            create_group(conn, "田中太郎", ["田中太郎", "田中"])
        conn.close()

        payload = {
            "primary_term_text": "鈴木",
            "member_texts": ["鈴木", "田中"],
        }

        response = client.post(
            f"/api/projects/{project_id}/synonym-groups",
            json=payload,
        )

        assert response.status_code == 409


class TestDeleteSynonymGroup:
    """Test DELETE /api/projects/{project_id}/synonym-groups/{group_id}."""

    def test_deletes_existing_group(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            group_id = create_group(conn, "田中太郎", ["田中太郎", "田中"])
        conn.close()

        response = client.delete(
            f"/api/projects/{project_id}/synonym-groups/{group_id}"
        )

        assert response.status_code == 204

    def test_returns_404_for_missing_group(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]

        response = client.delete(
            f"/api/projects/{project_id}/synonym-groups/999"
        )

        assert response.status_code == 404


class TestUpdateSynonymGroup:
    """Test PATCH /api/projects/{project_id}/synonym-groups/{group_id}."""

    def test_updates_primary_term(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            group_id = create_group(conn, "田中太郎", ["田中太郎", "田中"])
        conn.close()

        response = client.patch(
            f"/api/projects/{project_id}/synonym-groups/{group_id}",
            json={"primary_term_text": "田中"},
        )

        assert response.status_code == 200
        assert response.json()["primary_term_text"] == "田中"

    def test_returns_404_for_missing_group(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]

        response = client.patch(
            f"/api/projects/{project_id}/synonym-groups/999",
            json={"primary_term_text": "田中"},
        )

        assert response.status_code == 404


class TestAddMember:
    """Test POST /api/projects/{project_id}/synonym-groups/{group_id}/members."""

    def test_adds_member_to_group(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            group_id = create_group(conn, "田中太郎", ["田中太郎"])
        conn.close()

        response = client.post(
            f"/api/projects/{project_id}/synonym-groups/{group_id}/members",
            json={"term_text": "田中"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["term_text"] == "田中"
        assert data["group_id"] == group_id

    def test_returns_409_for_duplicate_member(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            group_id = create_group(conn, "田中太郎", ["田中太郎"])
        conn.close()

        response = client.post(
            f"/api/projects/{project_id}/synonym-groups/{group_id}/members",
            json={"term_text": "田中太郎"},
        )

        assert response.status_code == 409


class TestRemoveMember:
    """Test DELETE /api/projects/{project_id}/synonym-groups/{group_id}/members/{member_id}."""

    def test_removes_member_from_group(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            group_id = create_group(conn, "田中太郎", ["田中太郎", "田中"])
        conn.close()

        # Get member_id for "田中"
        conn = get_connection(project_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM term_synonym_members WHERE term_text = ?",
            ("田中",),
        )
        member_id = cursor.fetchone()[0]
        conn.close()

        response = client.delete(
            f"/api/projects/{project_id}/synonym-groups/{group_id}/members/{member_id}"
        )

        assert response.status_code == 204

    def test_returns_404_for_missing_member(
        self, test_project_setup, client: TestClient
    ):
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        initialize_db(conn)
        with transaction(conn):
            group_id = create_group(conn, "田中太郎", ["田中太郎"])
        conn.close()

        response = client.delete(
            f"/api/projects/{project_id}/synonym-groups/{group_id}/members/999"
        )

        assert response.status_code == 404
