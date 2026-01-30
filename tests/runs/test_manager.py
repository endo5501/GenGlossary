"""Tests for RunManager."""

import sqlite3
import time
from pathlib import Path
from threading import Event
from typing import Iterator
from unittest.mock import Mock, patch

import pytest

from genglossary.db.connection import get_connection
from genglossary.db.runs_repository import create_run, get_run
from genglossary.db.schema import initialize_db
from genglossary.runs.manager import RunManager


@pytest.fixture
def project_db_path(tmp_path: Path) -> str:
    """Create a test project database with runs table and return its path."""
    db_path = tmp_path / "test_project.db"
    connection = get_connection(str(db_path))
    initialize_db(connection)
    connection.close()
    return str(db_path)


@pytest.fixture
def project_db(project_db_path: str) -> Iterator[sqlite3.Connection]:
    """Get a connection to the test project database."""
    connection = get_connection(project_db_path)
    yield connection
    connection.close()


@pytest.fixture
def manager(project_db_path: str) -> RunManager:
    """Create a RunManager instance for testing."""
    mgr = RunManager(project_db_path)
    yield mgr
    # Ensure thread is stopped before fixture cleanup
    if mgr._thread and mgr._thread.is_alive():
        mgr._cancel_event.set()
        mgr._thread.join(timeout=2)


class TestRunManagerStart:
    """Tests for RunManager.start_run method."""

    def test_run_sets_failed_status_when_no_documents(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """ドキュメントがない場合はfailedステータスを設定する"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor to raise RuntimeError
            mock_executor.return_value.execute.side_effect = RuntimeError("No documents found in doc_root")

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that run status is "failed"
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "failed"
            assert "No documents found" in (run["error_message"] or "")

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
            # Mock executor to simulate long-running task
            def slow_execute(*args, **kwargs):
                time.sleep(0.5)

            mock_executor.return_value.execute.side_effect = slow_execute

            run_id = manager.start_run(scope="full")

            # Wait briefly for thread to start
            time.sleep(0.1)

            # Thread should be running
            assert manager._thread is not None
            assert manager._thread.is_alive()

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

            # Wait for thread to complete
            time.sleep(0.3)

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
            # Mock executor to simulate long-running task
            def slow_execute(*args, **kwargs):
                time.sleep(0.5)

            mock_executor.return_value.execute.side_effect = slow_execute

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)

            active_run = manager.get_active_run()
            assert active_run is not None
            assert active_run["id"] == run_id

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


class TestRunManagerSubscription:
    """Tests for RunManager subscription functionality."""

    def test_register_subscriber_creates_queue(self, manager: RunManager) -> None:
        """register_subscriberはQueueを作成して返す"""
        queue = manager.register_subscriber(run_id=1)
        assert queue is not None

    def test_multiple_subscribers_same_run_get_same_logs(self, manager: RunManager) -> None:
        """同じrunの複数subscriberが同じログを受信する"""
        queue1 = manager.register_subscriber(run_id=1)
        queue2 = manager.register_subscriber(run_id=1)

        manager._broadcast_log(1, {"level": "info", "message": "test"})

        log1 = queue1.get_nowait()
        log2 = queue2.get_nowait()
        assert log1 == log2

    def test_subscribers_only_receive_their_run_logs(self, manager: RunManager) -> None:
        """subscriberは自分のrunのログのみ受信する"""
        queue1 = manager.register_subscriber(run_id=1)
        queue2 = manager.register_subscriber(run_id=2)

        manager._broadcast_log(1, {"level": "info", "message": "run1"})

        log1 = queue1.get_nowait()
        assert log1["message"] == "run1"
        assert queue2.empty()

    def test_unregister_subscriber_stops_receiving(self, manager: RunManager) -> None:
        """unregister後はログを受信しない"""
        queue = manager.register_subscriber(run_id=1)
        manager.unregister_subscriber(run_id=1, queue=queue)

        manager._broadcast_log(1, {"level": "info", "message": "test"})

        assert queue.empty()

    def test_completion_signal_delivered_even_when_queue_full(self, manager: RunManager) -> None:
        """完了シグナルは満杯のキューでも配信される"""
        queue = manager.register_subscriber(run_id=1)

        for i in range(manager.MAX_LOG_QUEUE_SIZE):
            queue.put_nowait({"run_id": 1, "level": "info", "message": f"msg-{i}"})

        manager._broadcast_log(1, {"run_id": 1, "complete": True})

        completion_found = False
        while not queue.empty():
            msg = queue.get_nowait()
            if msg.get("complete"):
                completion_found = True
                break

        assert completion_found, "Completion signal should be delivered even when queue is full"


class TestRunManagerLogStreaming:
    """Tests for RunManager log streaming functionality."""

    def test_logs_are_captured_during_execution(
        self, manager: RunManager
    ) -> None:
        """実行中のログがキャプチャされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:

            def mock_execute(conn, scope, context, doc_root="."):
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Starting execution"})
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Completed"})

            mock_executor.return_value.execute.side_effect = mock_execute

            # Subscribe to logs
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")
            time.sleep(0.2)  # Allow execution to complete

            # Retrieve logs from queue (filter out completion signal)
            logs = []
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and not log.get("complete"):
                    logs.append(log)

            assert len(logs) >= 2
            assert any("Starting execution" in log.get("message", "") for log in logs)

    def test_cancel_run_stops_execution(self, manager: RunManager) -> None:
        """キャンセルが実行中スレッドに届いて処理を停止することを確認"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor that checks cancellation event
            cancel_detected = []

            def mock_execute(conn, scope, context, doc_root="."):
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Starting"})
                # Simulate some work, checking for cancellation
                for i in range(10):
                    if context.cancel_event.is_set():
                        cancel_detected.append(True)
                        context.log_callback({"run_id": context.run_id, "level": "info", "message": "Cancelled"})
                        return
                    time.sleep(0.1)
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Completed"})

            mock_executor.return_value.execute.side_effect = mock_execute

            # Subscribe to logs
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")
            time.sleep(0.2)  # Allow thread to start

            # Cancel the run
            manager.cancel_run(run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Verify cancellation was detected by the executor
            assert len(cancel_detected) > 0
            assert cancel_detected[0] is True

            # Check logs contain cancellation message (filter out completion signal)
            logs = []
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and not log.get("complete"):
                    logs.append(log)

            assert any("Cancelled" in log.get("message", "") for log in logs)

    def test_logs_include_run_id(self, manager: RunManager) -> None:
        """ログメッセージにrun_idが含まれることを確認"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:

            def mock_execute(conn, scope, context, doc_root="."):
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Starting"})
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Completed"})

            mock_executor.return_value.execute.side_effect = mock_execute

            # Subscribe to logs
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that logs include run_id
            logs = []
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and not log.get("complete"):
                    logs.append(log)

            assert len(logs) >= 2
            for log in logs:
                assert log.get("run_id") == run_id, f"Log should have run_id={run_id}, got {log.get('run_id')}"

    def test_completion_signal_includes_run_id(self, manager: RunManager) -> None:
        """完了シグナルにrun_idが含まれることを確認"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:

            def mock_execute(conn, scope, context, doc_root="."):
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Starting"})

            mock_executor.return_value.execute.side_effect = mock_execute

            # Subscribe to logs
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that completion signal has run_id
            completion_signal_found = False
            completion_run_id = None

            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and log.get("complete"):
                    completion_signal_found = True
                    completion_run_id = log.get("run_id")

            assert completion_signal_found, "Completion signal should be sent to log queue"
            assert completion_run_id == run_id, f"Completion signal should have run_id={run_id}"

    def test_sse_receives_completion_signal(self, manager: RunManager) -> None:
        """SSEストリームが完了シグナルを受け取ることを確認"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:

            def mock_execute(conn, scope, context, doc_root="."):
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Starting"})
                context.log_callback({"run_id": context.run_id, "level": "info", "message": "Completed"})
                # Completion signal should be sent by manager, not executor

            mock_executor.return_value.execute.side_effect = mock_execute

            # Subscribe to logs
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that completion signal was sent to queue
            logs = []
            completion_signal_found = False

            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and log.get("complete"):
                    completion_signal_found = True
                else:
                    logs.append(log)

            assert completion_signal_found, "Completion signal should be sent to log queue"
