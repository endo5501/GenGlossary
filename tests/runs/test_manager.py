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
        # Cancel all running runs
        with mgr._cancel_events_lock:
            for cancel_event in mgr._cancel_events.values():
                cancel_event.set()
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
            # Mock executor that checks cancel event
            def cancellable_execute(conn, scope, context, doc_root="."):
                # Wait for cancellation, checking the event
                for _ in range(50):  # 5 seconds max
                    if context.cancel_event.is_set():
                        return
                    time.sleep(0.1)

            mock_executor.return_value.execute.side_effect = cancellable_execute

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)  # Allow thread to start

            manager.cancel_run(run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "cancelled"

    def test_cancel_run_signals_cancellation_event(
        self, manager: RunManager
    ) -> None:
        """cancel_runはキャンセルイベントをシグナルする"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            execution_barrier = Event()

            def mock_execute(conn, scope, context, doc_root="."):
                # Wait to keep run "active" until we cancel
                execution_barrier.wait(timeout=5)

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)

            # Cancel event should be set for this run
            manager.cancel_run(run_id)
            assert manager._cancel_events[run_id].is_set()

            # Cleanup
            execution_barrier.set()
            if manager._thread:
                manager._thread.join(timeout=2)

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


class TestRunManagerPerRunCancellation:
    """Tests for per-run cancellation functionality."""

    def test_each_run_gets_individual_cancel_event(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """各runが個別のキャンセルイベントを持つことを確認"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            captured_events = []

            def mock_execute(conn, scope, context, doc_root="."):
                captured_events.append(context.cancel_event)

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")
            if manager._thread:
                manager._thread.join(timeout=2)

            # Cancel event should be stored in _cancel_events dict
            assert hasattr(manager, "_cancel_events")
            assert len(captured_events) == 1

    def test_cancel_only_affects_specific_run(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """キャンセルが特定のrunのみに影響することを確認"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            captured_events: dict[int, Event] = {}
            execution_barrier = Event()

            def mock_execute(conn, scope, context, doc_root="."):
                captured_events[context.run_id] = context.cancel_event
                # Wait to keep first run "active" until we cancel
                if context.run_id == 1:
                    execution_barrier.wait(timeout=2)

            mock_executor.return_value.execute.side_effect = mock_execute

            # Start first run
            run_id1 = manager.start_run(scope="full")
            time.sleep(0.1)

            # Cancel run_id1
            manager.cancel_run(run_id1)

            # Release the barrier to let execution complete
            execution_barrier.set()

            if manager._thread:
                manager._thread.join(timeout=2)

            # Only the cancelled run's event should be set
            assert run_id1 in captured_events
            assert captured_events[run_id1].is_set()

    def test_cancel_nonexistent_run_is_safe(
        self, manager: RunManager
    ) -> None:
        """存在しないrunをキャンセルしても安全"""
        # Should not raise any exception
        manager.cancel_run(9999)

    def test_cancel_event_is_cleaned_up_after_run_completes(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """runが完了するとキャンセルイベントがクリーンアップされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")
            if manager._thread:
                manager._thread.join(timeout=2)

            # After completion, the cancel event should be cleaned up
            assert hasattr(manager, "_cancel_events")
            assert run_id not in manager._cancel_events

    def test_cancel_run_updates_specific_run_event(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """cancel_runが指定したrun_idのイベントのみをセットする"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            execution_barrier = Event()

            def mock_execute(conn, scope, context, doc_root="."):
                # Keep running until barrier is released
                execution_barrier.wait(timeout=5)

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)

            # Verify the event exists and is not set
            assert run_id in manager._cancel_events
            assert not manager._cancel_events[run_id].is_set()

            # Cancel the run
            manager.cancel_run(run_id)

            # Verify the specific run's event is now set
            assert manager._cancel_events[run_id].is_set()

            # Cleanup
            execution_barrier.set()
            if manager._thread:
                manager._thread.join(timeout=2)


class TestRunManagerErrorLogging:
    """Tests for error logging with traceback."""

    def test_error_log_includes_traceback(
        self, manager: RunManager
    ) -> None:
        """エラーログにトレースバックが含まれることを確認"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Raise an exception with a specific traceback
            def raise_error(*args, **kwargs):
                raise RuntimeError("Test error message")

            mock_executor.return_value.execute.side_effect = raise_error

            # Subscribe to logs before starting run
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Find the error log and check for traceback
            error_log = None
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and log.get("level") == "error":
                    error_log = log
                    break

            assert error_log is not None, "Error log should be broadcast"
            assert "Test error message" in error_log.get("message", "")
            assert "traceback" in error_log, "Error log should include traceback field"
            assert error_log["traceback"] is not None, "Traceback should not be None"
            assert "RuntimeError" in error_log["traceback"], (
                "Traceback should contain exception type"
            )
            assert "raise_error" in error_log["traceback"], (
                "Traceback should contain the function that raised the error"
            )


class TestRunManagerConnectionErrorHandling:
    """Tests for connection error handling in _execute_run."""

    def test_fallback_to_new_connection_when_conn_update_fails(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """connでのステータス更新が失敗した場合、新しい接続にフォールバックする"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # First call succeeds (status update to running)
            # Executor raises error
            mock_executor.return_value.execute.side_effect = RuntimeError("Test error")

            # Patch update_run_status to fail on first call in except block,
            # succeed on second call with fallback
            original_update_run_status = __import__(
                "genglossary.db.runs_repository", fromlist=["update_run_status"]
            ).update_run_status

            call_count = {"value": 0}

            def mock_update_run_status(conn, run_id, status, **kwargs):
                call_count["value"] += 1
                # First call is "running" status, let it pass
                if status == "running":
                    return original_update_run_status(conn, run_id, status, **kwargs)
                # For "failed" status: fail first, succeed second (fallback)
                if status == "failed":
                    if call_count["value"] == 2:
                        raise sqlite3.OperationalError("database is locked")
                    return original_update_run_status(conn, run_id, status, **kwargs)
                return original_update_run_status(conn, run_id, status, **kwargs)

            with patch(
                "genglossary.runs.manager.update_run_status",
                side_effect=mock_update_run_status,
            ):
                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Status should be updated via fallback connection
                run = get_run(project_db, run_id)
                assert run is not None
                assert run["status"] == "failed", (
                    f"Expected status 'failed' but got '{run['status']}'. "
                    "Fallback connection should have updated the status."
                )

    def test_error_log_broadcast_even_when_fallback_connection_fails(
        self, manager: RunManager
    ) -> None:
        """fallback接続が失敗しても、エラーログはブロードキャストされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = RuntimeError("Test error")

            # Make both primary and fallback connections fail for status update
            with patch(
                "genglossary.runs.manager.update_run_status"
            ) as mock_update_run_status:
                # First call succeeds (running status)
                # Second call fails (failed status with original conn)
                # Third call (fallback) also fails
                mock_update_run_status.side_effect = [
                    None,  # running status
                    sqlite3.OperationalError("database is locked"),  # first failed
                    sqlite3.OperationalError("database is locked"),  # fallback failed
                ]

                # Subscribe to logs before starting run
                queue = manager.register_subscriber(run_id=1)

                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Error log should still be broadcast
                error_log_found = False
                while not queue.empty():
                    log = queue.get_nowait()
                    if log is not None and log.get("level") == "error":
                        error_log_found = True
                        assert "Test error" in log.get("message", "")
                        break

                assert error_log_found, (
                    "Error log should be broadcast even when all status updates fail"
                )

    def test_warning_log_broadcast_when_status_update_fails(
        self, manager: RunManager
    ) -> None:
        """ステータス更新が失敗した場合、warningログがブロードキャストされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = RuntimeError("Test error")

            # Make primary connection fail, fallback succeeds
            with patch(
                "genglossary.runs.manager.update_run_status"
            ) as mock_update_run_status:
                mock_update_run_status.side_effect = [
                    None,  # running status
                    sqlite3.OperationalError("database is locked"),  # first failed
                    None,  # fallback succeeds
                ]

                # Subscribe to logs before starting run
                queue = manager.register_subscriber(run_id=1)

                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Warning log should be broadcast for failed status update
                warning_log_found = False
                while not queue.empty():
                    log = queue.get_nowait()
                    if log is not None and log.get("level") == "warning":
                        warning_log_found = True
                        assert "Failed to update run status" in log.get("message", "")
                        break

                assert warning_log_found, (
                    "Warning log should be broadcast when status update fails"
                )

    def test_completion_signal_sent_even_when_fallback_connection_fails(
        self, manager: RunManager
    ) -> None:
        """fallback接続が失敗しても、完了シグナルが送信される"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = RuntimeError("Test error")

            # Make fallback connection fail
            with patch(
                "genglossary.runs.manager.update_run_status"
            ) as mock_update_run_status:
                mock_update_run_status.side_effect = [
                    None,  # running status
                    sqlite3.OperationalError("database is locked"),  # first failed
                    sqlite3.OperationalError("database is locked"),  # fallback failed
                ]

                # Subscribe to logs before starting run
                queue = manager.register_subscriber(run_id=1)

                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Completion signal should still be sent
                completion_signal_found = False
                while not queue.empty():
                    log = queue.get_nowait()
                    if log is not None and log.get("complete"):
                        completion_signal_found = True
                        break

                assert completion_signal_found, (
                    "Completion signal should be sent even when all status updates fail"
                )

    def test_cancel_event_cleaned_up_when_get_connection_fails(
        self, manager: RunManager
    ) -> None:
        """get_connectionが失敗してもcancel_eventがクリーンアップされる"""
        with patch("genglossary.runs.manager.get_connection") as mock_get_connection:
            # Mock get_connection to raise an error
            mock_get_connection.side_effect = sqlite3.OperationalError(
                "Unable to connect to database"
            )

            run_id = manager.start_run(scope="full")

            # Wait for thread to complete (it should fail quickly)
            if manager._thread:
                manager._thread.join(timeout=2)

            # Cancel event should be cleaned up even though connection failed
            assert run_id not in manager._cancel_events, (
                "Cancel event should be cleaned up even when get_connection fails"
            )

    def test_completion_signal_sent_when_get_connection_fails(
        self, manager: RunManager
    ) -> None:
        """get_connectionが失敗しても完了シグナルが送信される"""
        with patch("genglossary.runs.manager.get_connection") as mock_get_connection:
            # Mock get_connection to raise an error
            mock_get_connection.side_effect = sqlite3.OperationalError(
                "Unable to connect to database"
            )

            # Subscribe to logs before starting run
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that completion signal was sent
            completion_signal_found = False
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and log.get("complete"):
                    completion_signal_found = True
                    break

            assert completion_signal_found, (
                "Completion signal should be sent even when get_connection fails"
            )

    def test_status_updated_to_failed_when_get_connection_fails(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """get_connectionが失敗した場合、ステータスがfailedに更新される"""
        with patch("genglossary.runs.manager.get_connection") as mock_get_connection:
            # Mock get_connection to raise an error
            mock_get_connection.side_effect = sqlite3.OperationalError(
                "Unable to connect to database"
            )

            run_id = manager.start_run(scope="full")

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that run status is failed
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "failed", (
                f"Expected status 'failed' but got '{run['status']}'"
            )
            assert "Unable to connect" in (run["error_message"] or "")


class TestRunManagerCancellationRaceCondition:
    """Tests for race condition between cancellation and completion."""

    def test_run_not_completed_when_cancelled_after_execution(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """実行完了後にキャンセルされた場合、ステータスはcancelledのまま"""
        from genglossary.db.connection import database_connection, transaction
        from genglossary.db.runs_repository import cancel_run as db_cancel_run

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor that simulates completion, then cancel happens
            # before status update
            cancel_after_execute = Event()

            def mock_execute(conn, scope, context, doc_root="."):
                # Simulate some work
                context.log_callback(
                    {"run_id": context.run_id, "level": "info", "message": "Done"}
                )
                # Signal that execution is complete, triggering cancellation
                cancel_after_execute.set()
                # Small delay to allow cancellation to happen before status update
                time.sleep(0.2)

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            cancel_after_execute.wait(timeout=5)

            # Cancel immediately after execute completes (race condition scenario)
            # This simulates the race: cancel happens between is_set() check
            # and status update
            with database_connection(manager.db_path) as conn:
                with transaction(conn):
                    db_cancel_run(conn, run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=3)

            # Status should be cancelled, not completed
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "cancelled", (
                f"Expected status 'cancelled' but got '{run['status']}'. "
                "Race condition: run was completed despite cancellation."
            )


class TestRunManagerSubscriberCleanup:
    """Tests for subscriber cleanup after run completion."""

    def test_subscribers_cleaned_up_after_run_completes(
        self, manager: RunManager
    ) -> None:
        """run完了後にsubscribersがクリーンアップされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            # Register subscriber before starting run
            # Note: We register for run_id=1 assuming it will be the first run
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # After completion, the subscribers should be cleaned up
            with manager._subscribers_lock:
                assert run_id not in manager._subscribers, (
                    "Subscribers should be cleaned up after run completion"
                )

    def test_subscribers_cleaned_up_after_run_fails(
        self, manager: RunManager
    ) -> None:
        """run失敗後にsubscribersがクリーンアップされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = RuntimeError("Test error")

            # Register subscriber before starting run
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # After failure, the subscribers should be cleaned up
            with manager._subscribers_lock:
                assert run_id not in manager._subscribers, (
                    "Subscribers should be cleaned up after run failure"
                )

    def test_subscribers_cleaned_up_after_run_cancelled(
        self, manager: RunManager
    ) -> None:
        """runキャンセル後にsubscribersがクリーンアップされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:

            def cancellable_execute(conn, scope, context, doc_root="."):
                # Wait for cancellation
                for _ in range(50):
                    if context.cancel_event.is_set():
                        return
                    time.sleep(0.1)

            mock_executor.return_value.execute.side_effect = cancellable_execute

            # Register subscriber before starting run
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")
            time.sleep(0.1)  # Allow thread to start

            manager.cancel_run(run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # After cancellation, the subscribers should be cleaned up
            with manager._subscribers_lock:
                assert run_id not in manager._subscribers, (
                    "Subscribers should be cleaned up after run cancellation"
                )

    def test_completion_signal_sent_before_subscriber_cleanup(
        self, manager: RunManager
    ) -> None:
        """subscriberクリーンアップ前に完了シグナルが送信される"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            # Register subscriber before starting run
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Completion signal should have been sent before cleanup
            completion_signal_found = False
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and log.get("complete"):
                    completion_signal_found = True
                    break

            assert completion_signal_found, (
                "Completion signal should be sent before subscriber cleanup"
            )