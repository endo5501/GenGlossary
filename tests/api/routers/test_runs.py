"""Tests for Runs API endpoints."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection
from genglossary.db.project_repository import create_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.db.runs_repository import create_run, get_run, update_run_status


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


class TestStartRun:
    """Tests for POST /api/projects/{id}/runs endpoint."""

    def test_start_run_returns_201(self, test_project_setup, client: TestClient):
        """POST /api/projects/{id}/runs は新しいRunを作成し201を返す"""
        project_id = test_project_setup["project_id"]

        with patch("genglossary.api.routers.runs.RunManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.start_run.return_value = 1

            payload = {"scope": "full"}
            response = client.post(
                f"/api/projects/{project_id}/runs", json=payload
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["scope"] == "full"
            assert data["status"] == "pending"

    def test_start_run_with_different_scopes(
        self, test_project_setup, client: TestClient
    ):
        """異なるscopeでRunを開始できる"""
        project_id = test_project_setup["project_id"]

        with patch("genglossary.api.routers.runs.RunManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.start_run.return_value = 1

            for scope in ["full", "from_terms", "provisional_to_refined"]:
                payload = {"scope": scope}
                response = client.post(
                    f"/api/projects/{project_id}/runs", json=payload
                )

                assert response.status_code == 201
                data = response.json()
                assert data["scope"] == scope

    def test_start_run_rejects_when_already_running(
        self, test_project_setup, client: TestClient
    ):
        """既にRunが実行中の場合は409を返す"""
        project_id = test_project_setup["project_id"]

        with patch("genglossary.api.routers.runs.RunManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.start_run.side_effect = RuntimeError("Run already running")

            payload = {"scope": "full"}
            response = client.post(
                f"/api/projects/{project_id}/runs", json=payload
            )

            assert response.status_code == 409

    def test_start_run_rejects_invalid_scope(
        self, test_project_setup, client: TestClient
    ):
        """無効なscopeは422を返す"""
        project_id = test_project_setup["project_id"]

        payload = {"scope": "invalid_scope"}
        response = client.post(
            f"/api/projects/{project_id}/runs", json=payload
        )

        assert response.status_code == 422


class TestCancelRun:
    """Tests for DELETE /api/projects/{id}/runs/{run_id} endpoint."""

    def test_cancel_run_returns_200(self, test_project_setup, client: TestClient):
        """DELETE /api/projects/{id}/runs/{run_id} はRunをキャンセルし200を返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create a run
        conn = get_connection(project_db_path)
        run_id = create_run(conn, scope="full")
        update_run_status(conn, run_id, "running")
        conn.close()

        with patch("genglossary.api.routers.runs.RunManager") as mock_manager_class:
            mock_manager = mock_manager_class.return_value

            response = client.delete(
                f"/api/projects/{project_id}/runs/{run_id}"
            )

            assert response.status_code == 200
            mock_manager.cancel_run.assert_called_once_with(run_id)

    def test_cancel_nonexistent_run_returns_404(
        self, test_project_setup, client: TestClient
    ):
        """存在しないRunをキャンセルしようとすると404を返す"""
        project_id = test_project_setup["project_id"]

        response = client.delete(
            f"/api/projects/{project_id}/runs/999"
        )

        assert response.status_code == 404


class TestListRuns:
    """Tests for GET /api/projects/{id}/runs endpoint."""

    def test_list_runs_returns_empty_list(
        self, test_project_setup, client: TestClient
    ):
        """Run履歴がない場合は空リストを返す"""
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/runs")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_runs_returns_all_runs(
        self, test_project_setup, client: TestClient
    ):
        """すべてのRun履歴を返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create some runs
        conn = get_connection(project_db_path)
        run_id1 = create_run(conn, scope="full")
        run_id2 = create_run(conn, scope="from_terms")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/runs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["id"] == run_id2
        assert data[1]["id"] == run_id1


class TestGetCurrentRun:
    """Tests for GET /api/projects/{id}/runs/current endpoint."""

    def test_get_current_run_returns_active_run(
        self, test_project_setup, client: TestClient
    ):
        """現在アクティブなRunを返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create a running run
        conn = get_connection(project_db_path)
        run_id = create_run(conn, scope="full")
        update_run_status(conn, run_id, "running")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/runs/current")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["status"] == "running"

    def test_get_current_run_returns_404_when_no_active(
        self, test_project_setup, client: TestClient
    ):
        """アクティブなRunがない場合は404を返す"""
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/runs/current")

        assert response.status_code == 404


class TestGetRun:
    """Tests for GET /api/projects/{id}/runs/{run_id} endpoint."""

    def test_get_run_returns_run_details(
        self, test_project_setup, client: TestClient
    ):
        """Run詳細を返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create a run
        conn = get_connection(project_db_path)
        run_id = create_run(conn, scope="full")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/runs/{run_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["scope"] == "full"
        assert data["status"] == "pending"

    def test_get_run_returns_404_for_nonexistent(
        self, test_project_setup, client: TestClient
    ):
        """存在しないRunは404を返す"""
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/runs/999")

        assert response.status_code == 404


class TestGetRunLogs:
    """Tests for GET /api/projects/{id}/runs/{run_id}/logs endpoint."""

    def test_get_run_logs_streams_sse(
        self, test_project_setup, client: TestClient
    ):
        """SSE形式でログをストリーミングする"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create a run
        conn = get_connection(project_db_path)
        run_id = create_run(conn, scope="full")
        conn.close()

        with patch("genglossary.api.routers.runs.RunManager") as mock_manager_class:
            from queue import Queue

            mock_manager = mock_manager_class.return_value
            mock_queue = Queue()
            mock_queue.put({"level": "info", "message": "Starting"})
            mock_queue.put({"level": "info", "message": "Completed"})
            mock_queue.put(None)  # Sentinel

            mock_manager.get_log_queue.return_value = mock_queue

            response = client.get(
                f"/api/projects/{project_id}/runs/{run_id}/logs",
                headers={"Accept": "text/event-stream"},
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

    def test_get_run_logs_returns_404_for_nonexistent(
        self, test_project_setup, client: TestClient
    ):
        """存在しないRunのログは404を返す"""
        project_id = test_project_setup["project_id"]

        response = client.get(
            f"/api/projects/{project_id}/runs/999/logs"
        )

        assert response.status_code == 404
