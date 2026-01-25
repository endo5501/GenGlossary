"""Tests for RunManager."""

import sqlite3
import time
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

import pytest

from genglossary.db.connection import get_connection
from genglossary.db.runs_repository import create_run, get_run
from genglossary.db.schema import initialize_db
from genglossary.runs.manager import RunManager


@pytest.fixture
def project_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a test project database with runs table."""
    db_path = tmp_path / "test_project.db"
    connection = get_connection(str(db_path))
    initialize_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def manager(project_db: sqlite3.Connection) -> RunManager:
    """Create a RunManager instance for testing."""
    return RunManager(project_db)


class TestRunManagerStart:
    """Tests for RunManager.start_run method."""

    def test_start_run_creates_run_record(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """start_runはRunレコードを作成する"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")

            assert run_id > 0
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["scope"] == "full"

    def test_start_run_launches_background_thread(
        self, manager: RunManager
    ) -> None:
        """start_runはバックグラウンドスレッドを起動する"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")

            # Wait briefly for thread to start
            time.sleep(0.1)

            # Thread should be running
            assert manager._thread is not None
            assert manager._thread.is_alive()

            # Cleanup
            manager.cancel_run(run_id)
            manager._thread.join(timeout=1)

    def test_start_run_rejects_when_already_running(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """既にRunが実行中の場合は新しいRunを開始できない"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor to simulate long-running task
            mock_executor.return_value.execute.side_effect = lambda *args, **kwargs: time.sleep(
                0.5
            )

            run_id1 = manager.start_run(scope="full")

            # Attempt to start another run while first is running
            with pytest.raises(RuntimeError, match="already running"):
                manager.start_run(scope="from_terms")

            # Cleanup
            manager.cancel_run(run_id1)
            if manager._thread:
                manager._thread.join(timeout=1)

    def test_start_run_with_different_scopes(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """異なるscopeでRunを開始できる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="from_terms")

            run = get_run(project_db, run_id)
            assert run is not None
            assert run["scope"] == "from_terms"

            # Cleanup
            if manager._thread:
                manager._thread.join(timeout=1)


class TestRunManagerCancel:
    """Tests for RunManager.cancel_run method."""

    def test_cancel_run_sets_status_to_cancelled(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """cancel_runはRunのステータスをcancelledに設定する"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock long-running executor
            def slow_execute(*args, **kwargs):
                time.sleep(0.5)

            mock_executor.return_value.execute.side_effect = slow_execute

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)  # Allow thread to start

            manager.cancel_run(run_id)

            # Wait for cancellation to complete
            if manager._thread:
                manager._thread.join(timeout=1)

            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "cancelled"

    def test_cancel_run_signals_cancellation_event(
        self, manager: RunManager
    ) -> None:
        """cancel_runはキャンセルイベントをシグナルする"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)

            manager.cancel_run(run_id)

            # Cancellation event should be set
            assert manager._cancel_event.is_set()

            # Cleanup
            if manager._thread:
                manager._thread.join(timeout=1)

    def test_cancel_nonexistent_run_does_not_fail(
        self, manager: RunManager
    ) -> None:
        """存在しないRunをキャンセルしようとしても失敗しない"""
        manager.cancel_run(999)  # Should not raise


class TestRunManagerGetActiveRun:
    """Tests for RunManager.get_active_run method."""

    def test_get_active_run_returns_current_run(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """get_active_runは現在アクティブなRunを返す"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)

            active_run = manager.get_active_run()
            assert active_run is not None
            assert active_run["id"] == run_id

            # Cleanup
            manager.cancel_run(run_id)
            if manager._thread:
                manager._thread.join(timeout=1)

    def test_get_active_run_returns_none_when_no_active(
        self, manager: RunManager
    ) -> None:
        """アクティブなRunがない場合はNoneを返す"""
        active_run = manager.get_active_run()
        assert active_run is None


class TestRunManagerGetRun:
    """Tests for RunManager.get_run method."""

    def test_get_run_returns_run_details(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """get_runはRun詳細を返す"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")

            run = manager.get_run(run_id)
            assert run is not None
            assert run["id"] == run_id
            assert run["scope"] == "full"

            # Cleanup
            if manager._thread:
                manager._thread.join(timeout=1)

    def test_get_run_returns_none_for_nonexistent(
        self, manager: RunManager
    ) -> None:
        """存在しないRunに対してはNoneを返す"""
        run = manager.get_run(999)
        assert run is None


class TestRunManagerLogStreaming:
    """Tests for RunManager log streaming functionality."""

    def test_get_log_queue_returns_queue(self, manager: RunManager) -> None:
        """get_log_queueはログキューを返す"""
        queue = manager.get_log_queue()
        assert queue is not None

    def test_logs_are_captured_during_execution(
        self, manager: RunManager
    ) -> None:
        """実行中のログがキャプチャされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:

            def mock_execute(conn, scope, cancel_event, log_queue):
                log_queue.put({"level": "info", "message": "Starting execution"})
                log_queue.put({"level": "info", "message": "Completed"})

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")
            time.sleep(0.2)  # Allow execution to complete

            # Retrieve logs from queue
            log_queue = manager.get_log_queue()
            logs = []
            while not log_queue.empty():
                logs.append(log_queue.get_nowait())

            assert len(logs) >= 2
            assert any("Starting execution" in log["message"] for log in logs)

            # Cleanup
            if manager._thread:
                manager._thread.join(timeout=1)
