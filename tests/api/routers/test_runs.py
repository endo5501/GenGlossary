"""Tests for Runs API endpoints."""

import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection, transaction
from genglossary.db.project_repository import create_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.db.runs_repository import create_run, update_run_status


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


class TestStartRun:
    """Tests for POST /api/projects/{id}/runs endpoint."""

    def test_start_run_creates_run_record(
        self, test_project_setup, client: TestClient
    ) -> None:
        """POST /api/projects/{id}/runs はRunレコードを作成する"""
        project_id = test_project_setup["project_id"]

        # Mock PipelineExecutor to prevent actual execution
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            response = client.post(
                f"/api/projects/{project_id}/runs",
                json={"scope": "full"}
            )

            assert response.status_code == 201
            data = response.json()
            assert data["scope"] == "full"
            assert data["status"] == "pending"
            assert data["id"] > 0

    def test_start_run_returns_409_when_already_running(
        self, test_project_setup, client: TestClient
    ) -> None:
        """既にRunが実行中の場合は409を返す"""
        project_id = test_project_setup["project_id"]

        # Mock PipelineExecutor to simulate long-running task
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            def slow_execute(*args, **kwargs):
                time.sleep(1.0)

            mock_executor.return_value.execute.side_effect = slow_execute

            # Start first run
            response1 = client.post(
                f"/api/projects/{project_id}/runs",
                json={"scope": "full"}
            )
            assert response1.status_code == 201

            # Wait for run to start
            time.sleep(0.1)

            # Try to start another run while first is running
            response2 = client.post(
                f"/api/projects/{project_id}/runs",
                json={"scope": "extract"}
            )
            assert response2.status_code == 409

    def test_start_run_with_different_scopes(
        self, test_project_setup, client: TestClient
    ) -> None:
        """異なるscopeでRunを開始できる"""
        project_id = test_project_setup["project_id"]

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            for scope in ["full", "extract", "generate", "review", "refine"]:
                response = client.post(
                    f"/api/projects/{project_id}/runs",
                    json={"scope": scope}
                )
                assert response.status_code == 201
                assert response.json()["scope"] == scope

                # Wait for run to complete
                time.sleep(0.1)


class TestCancelRun:
    """Tests for DELETE /api/projects/{id}/runs/{run_id} endpoint."""

    def test_cancel_run_updates_status(
        self, test_project_setup, client: TestClient
    ) -> None:
        """DELETE /api/projects/{id}/runs/{run_id} はRunをキャンセルする"""
        from genglossary.runs.executor import PipelineCancelledException

        project_id = test_project_setup["project_id"]

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            def cancellable_execute(conn, scope, context, doc_root=".", **kwargs):
                # Wait for cancellation, checking the event and raise PipelineCancelledException
                for _ in range(50):  # 5 seconds max
                    if context.cancel_event.is_set():
                        raise PipelineCancelledException()
                    time.sleep(0.1)

            mock_executor.return_value.execute.side_effect = cancellable_execute

            # Start run
            response = client.post(
                f"/api/projects/{project_id}/runs",
                json={"scope": "full"}
            )
            assert response.status_code == 201
            run_id = response.json()["id"]

            # Wait for run to start
            time.sleep(0.1)

            # Cancel run
            response = client.delete(f"/api/projects/{project_id}/runs/{run_id}")
            assert response.status_code == 200

            # Wait for cancellation to complete (thread needs to detect and update DB)
            time.sleep(0.5)

            # Verify run was cancelled
            response = client.get(f"/api/projects/{project_id}/runs/{run_id}")
            assert response.status_code == 200
            assert response.json()["status"] == "cancelled"

    def test_cancel_run_commits_immediately(
        self, test_project_setup, client: TestClient
    ) -> None:
        """キャンセルがDBに即座にコミットされる（別接続から確認）"""
        from datetime import datetime, timezone

        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create a running run directly in DB
        conn = get_connection(project_db_path)
        with transaction(conn):
            run_id = create_run(conn, scope="full")
            update_run_status(conn, run_id, "running", started_at=datetime.now(timezone.utc))
        conn.close()

        # Cancel via API (no background executor needed since run is already in DB)
        with patch("genglossary.runs.manager.RunManager.cancel_run"):
            response = client.delete(f"/api/projects/{project_id}/runs/{run_id}")
            assert response.status_code == 200

        # Verify from a separate connection that the cancel was committed
        reader = get_connection(project_db_path)
        row = reader.execute("SELECT status FROM runs WHERE id = ?", (run_id,)).fetchone()
        reader.close()
        assert row is not None
        assert row["status"] == "cancelled"

    def test_cancel_nonexistent_run_returns_404(
        self, test_project_setup, client: TestClient
    ) -> None:
        """存在しないRunをキャンセルしようとすると404を返す"""
        project_id = test_project_setup["project_id"]

        response = client.delete(f"/api/projects/{project_id}/runs/999")
        assert response.status_code == 404


class TestListRuns:
    """Tests for GET /api/projects/{id}/runs endpoint."""

    def test_list_runs_returns_history(
        self, test_project_setup, client: TestClient
    ) -> None:
        """GET /api/projects/{id}/runs はRun履歴を返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create some runs directly in database
        conn = get_connection(project_db_path)
        with transaction(conn):
            run1_id = create_run(conn, scope="full")
            run2_id = create_run(conn, scope="extract")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/runs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Check both runs exist (order may vary)
        run_ids = [r["id"] for r in data]
        assert run1_id in run_ids
        assert run2_id in run_ids


class TestGetRun:
    """Tests for GET /api/projects/{id}/runs/{run_id} endpoint."""

    def test_get_run_returns_details(
        self, test_project_setup, client: TestClient
    ) -> None:
        """GET /api/projects/{id}/runs/{run_id} はRun詳細を返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        with transaction(conn):
            run_id = create_run(conn, scope="full")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/runs/{run_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["scope"] == "full"

    def test_get_run_returns_404_for_missing(
        self, test_project_setup, client: TestClient
    ) -> None:
        """存在しないRunに対しては404を返す"""
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/runs/999")
        assert response.status_code == 404


class TestGetCurrentRun:
    """Tests for GET /api/projects/{id}/runs/current endpoint."""

    def test_get_current_run_returns_active(
        self, test_project_setup, client: TestClient
    ) -> None:
        """GET /api/projects/{id}/runs/current はアクティブなRunを返す"""
        project_id = test_project_setup["project_id"]

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            def slow_execute(*args, **kwargs):
                time.sleep(1.0)

            mock_executor.return_value.execute.side_effect = slow_execute

            # Start run
            response = client.post(
                f"/api/projects/{project_id}/runs",
                json={"scope": "full"}
            )
            assert response.status_code == 201
            run_id = response.json()["id"]

            # Wait for run to start
            time.sleep(0.1)

            # Get current run
            response = client.get(f"/api/projects/{project_id}/runs/current")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == run_id
            assert data["status"] in ["pending", "running"]

    def test_get_current_run_returns_404_when_none(
        self, test_project_setup, client: TestClient
    ) -> None:
        """Runが存在しない場合は404を返す"""
        project_id = test_project_setup["project_id"]

        response = client.get(f"/api/projects/{project_id}/runs/current")
        assert response.status_code == 404

    def test_get_current_run_returns_completed_run(
        self, test_project_setup, client: TestClient
    ) -> None:
        """アクティブなRunがない場合は最新の完了Runを返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create a completed run directly in the database
        conn = get_connection(project_db_path)
        with transaction(conn):
            run_id = create_run(conn, scope="full")
            update_run_status(conn, run_id, "completed")
        conn.close()

        # Get current run - should return completed run
        response = client.get(f"/api/projects/{project_id}/runs/current")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["status"] == "completed"

    def test_get_current_run_returns_failed_run(
        self, test_project_setup, client: TestClient
    ) -> None:
        """アクティブなRunがない場合は最新の失敗Runを返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        # Create a failed run directly in the database
        conn = get_connection(project_db_path)
        with transaction(conn):
            run_id = create_run(conn, scope="full")
            update_run_status(conn, run_id, "failed", error_message="Test error")
        conn.close()

        # Get current run - should return failed run
        response = client.get(f"/api/projects/{project_id}/runs/current")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["status"] == "failed"


class TestRunLogs:
    """Tests for GET /api/projects/{id}/runs/{run_id}/logs endpoint."""

    def test_logs_complete_immediately_for_finished_run(
        self, test_project_setup, client: TestClient
    ) -> None:
        """完了済みRunは即完了イベントを返す"""
        project_id = test_project_setup["project_id"]
        project_db_path = test_project_setup["project_db_path"]

        conn = get_connection(project_db_path)
        with transaction(conn):
            run_id = create_run(conn, scope="full")
            update_run_status(conn, run_id, "completed")
        conn.close()

        response = client.get(f"/api/projects/{project_id}/runs/{run_id}/logs")
        assert response.status_code == 200
        assert "event: complete" in response.text
