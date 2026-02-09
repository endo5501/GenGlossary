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


class TestRunManagerStartRunSynchronization:
    """Tests for start_run synchronization to prevent race conditions."""

    def test_concurrent_start_run_only_one_succeeds(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """並行してstart_runを呼び出した場合、1つだけが成功する"""
        import concurrent.futures

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor to simulate long-running task
            def slow_execute(*args, **kwargs):
                time.sleep(1)

            mock_executor.return_value.execute.side_effect = slow_execute

            results: list[int | Exception] = []
            errors: list[Exception] = []

            def try_start_run() -> int | None:
                try:
                    run_id = manager.start_run(scope="full")
                    return run_id
                except RuntimeError as e:
                    errors.append(e)
                    return None

            # Start multiple threads concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(try_start_run) for _ in range(5)]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result is not None:
                        results.append(result)

            # Only one should succeed
            assert len(results) == 1, (
                f"Expected only 1 successful start_run, but got {len(results)}. "
                "Race condition: multiple runs were created concurrently."
            )
            # Others should fail with RuntimeError
            assert len(errors) == 4, (
                f"Expected 4 failures, but got {len(errors)}. "
            )
            for error in errors:
                assert "already running" in str(error)

    def test_concurrent_start_run_no_duplicate_run_records(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """並行してstart_runを呼び出しても、重複したrunレコードが作成されない"""
        import concurrent.futures
        from genglossary.db.runs_repository import get_active_run

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor to simulate long-running task
            def slow_execute(*args, **kwargs):
                time.sleep(1)

            mock_executor.return_value.execute.side_effect = slow_execute

            def try_start_run() -> int | None:
                try:
                    return manager.start_run(scope="full")
                except RuntimeError:
                    return None

            # Start multiple threads concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(try_start_run) for _ in range(5)]
                concurrent.futures.wait(futures)

            # Check that only one active run exists
            active_run = get_active_run(project_db)
            assert active_run is not None

            # Count all runs with pending/running status
            cursor = project_db.execute(
                "SELECT COUNT(*) FROM runs WHERE status IN ('pending', 'running')"
            )
            count = cursor.fetchone()[0]
            assert count == 1, (
                f"Expected only 1 active run, but found {count}. "
                "Race condition: duplicate run records were created."
            )


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
                manager.start_run(scope="extract")

    def test_start_run_with_different_scopes(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """異なるscopeでRunを開始できる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="extract")

            run = get_run(project_db, run_id)
            assert run is not None
            assert run["scope"] == "extract"


class TestRunManagerCancel:
    """Tests for RunManager.cancel_run method."""

    def test_cancel_run_sets_status_to_cancelled(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """cancel_runはRunのステータスをcancelledに設定する"""
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor that checks cancel event and raises PipelineCancelledException
            def cancellable_execute(conn, scope, context, doc_root="."):
                # Wait for cancellation, checking the event
                for _ in range(50):  # 5 seconds max
                    if context.cancel_event.is_set():
                        raise PipelineCancelledException()
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

    def test_warning_log_broadcast_when_all_status_updates_fail(
        self, manager: RunManager
    ) -> None:
        """全てのステータス更新が失敗した場合、warningログがブロードキャストされる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = RuntimeError("Test error")

            # Make all update_run_status_if_active calls fail with exception
            # This causes both primary and fallback attempts to fail
            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=sqlite3.OperationalError("database is locked"),
            ):
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
                        if "Failed to update" in log.get("message", ""):
                            warning_log_found = True
                            break

                assert warning_log_found, (
                    "Warning log should be broadcast when all status updates fail"
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

    def test_late_cancel_preserves_completed_status(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """パイプライン完了後にキャンセルが来ても、ステータスはcompletedのまま

        This is the "late cancel" scenario: the pipeline has already completed,
        but a cancel request arrives just before the status update.
        The implementation prioritizes preserving results over respecting
        the cancel request.
        """
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor that simulates completion (returns False = not cancelled)
            # then cancel happens before status update
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
                return False  # Completed normally (not cancelled during execution)

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            cancel_after_execute.wait(timeout=5)

            # Cancel immediately after execute completes (late cancel scenario)
            # This simulates the race: user clicks cancel after pipeline is done
            # but before status update. cancel_run sets the event, but
            # since was_cancelled=False, the status should still be completed.
            manager.cancel_run(run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=3)

            # Status should be completed, because the pipeline finished before cancel
            # The cancel request was too late - results are preserved
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "completed", (
                f"Expected status 'completed' but got '{run['status']}'. "
                "Late cancel should not override completed status - results should be preserved."
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
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:

            def cancellable_execute(conn, scope, context, doc_root="."):
                # Wait for cancellation and raise PipelineCancelledException
                for _ in range(50):
                    if context.cancel_event.is_set():
                        raise PipelineCancelledException()
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


class TestRunManagerStatusUpdateFallbackLogic:
    """Tests for improved status update fallback logic.

    Issues addressed:
    1. _try_complete_status returns False for both no-op (not in expected state) and
       failure (exception), causing unnecessary fallback for no-op case.
    2. _try_status_with_fallback doesn't catch exceptions from updater,
       preventing fallback when updater throws.
    3. _try_cancel_status returns True even when cancel_run didn't update rows.
    """

    def test_complete_status_no_op_does_not_trigger_fallback(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """update_run_status_if_activeがNOT_IN_EXPECTED_STATEを返した場合（no-op）、
        フォールバックは試行されない"""
        from genglossary.db.runs_repository import RunUpdateResult

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            # Track how many times update_run_status_if_active is called
            call_count = {"value": 0}

            def counting_update(conn, run_id, status, error_message=None):
                call_count["value"] += 1
                # Return NOT_IN_EXPECTED_STATE to simulate no-op (already cancelled)
                return RunUpdateResult.NOT_IN_EXPECTED_STATE

            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=counting_update,
            ):
                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # update_run_status_if_active should be called only once
                # (no fallback retry for no-op case)
                assert call_count["value"] == 1, (
                    f"Expected 1 call to update_run_status_if_active (no fallback for no-op), "
                    f"but got {call_count['value']} calls"
                )

    def test_status_updater_exception_triggers_fallback(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """status_updaterが例外を投げた場合、フォールバックが試行される"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            # Track calls to update_run_status_if_active
            call_count = {"value": 0}

            original_update = __import__(
                "genglossary.db.runs_repository", fromlist=["update_run_status_if_active"]
            ).update_run_status_if_active

            def failing_then_succeeding_update(conn, run_id, status, error_message=None):
                call_count["value"] += 1
                if call_count["value"] == 1:
                    # Simulate updater throwing exception (not caught internally)
                    raise sqlite3.OperationalError("database is locked")
                return original_update(conn, run_id, status, error_message)

            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=failing_then_succeeding_update,
            ):
                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Should have been called twice: once failed, once fallback succeeded
                assert call_count["value"] == 2, (
                    f"Expected 2 calls (failure + fallback), got {call_count['value']}"
                )

                # Status should be completed via fallback
                run = get_run(project_db, run_id)
                assert run is not None
                assert run["status"] == "completed"

    def test_cancel_status_no_op_logged_and_no_fallback(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """update_run_status_if_activeがNOT_IN_EXPECTED_STATEを返した場合（no-op）、ログに記録されフォールバックは試行されない"""
        from genglossary.db.runs_repository import RunUpdateResult
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor that waits for cancellation and raises PipelineCancelledException
            def cancellable_execute(conn, scope, context, doc_root="."):
                for _ in range(50):
                    if context.cancel_event.is_set():
                        raise PipelineCancelledException()
                    time.sleep(0.1)

            mock_executor.return_value.execute.side_effect = cancellable_execute

            # Track how many times update_run_status_if_active is called for 'cancelled'
            call_count = {"value": 0}

            def counting_update(conn, run_id, status, error_message=None):
                if status == "cancelled":
                    call_count["value"] += 1
                    # Return NOT_IN_EXPECTED_STATE to simulate no-op (not in expected state)
                    return RunUpdateResult.NOT_IN_EXPECTED_STATE
                return RunUpdateResult.UPDATED  # For other status updates

            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=counting_update,
            ):
                # Subscribe to logs
                queue = manager.register_subscriber(run_id=1)

                run_id = manager.start_run(scope="full")
                time.sleep(0.1)  # Allow thread to start

                manager.cancel_run(run_id)

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Should only be called once for cancelled status (no fallback for no-op)
                assert call_count["value"] == 1, (
                    f"Expected 1 call (no fallback for no-op), got {call_count['value']}"
                )

                # Check that info log was broadcast about skipped cancel
                logs = []
                while not queue.empty():
                    log = queue.get_nowait()
                    if log is not None and not log.get("complete"):
                        logs.append(log)

                assert any(
                    "Cancelled skipped" in log.get("message", "") and log.get("level") == "info"
                    for log in logs
                ), "Info log about skipped cancel should be broadcast"


class TestRunManagerFailedStatusGuard:
    """Tests for _try_failed_status guarding against terminal states.

    Issue: _try_failed_status should not overwrite existing terminal states
    (cancelled, completed, failed) to maintain consistency with cancel_run
    and complete_run_if_not_cancelled semantics.
    """

    def test_failed_status_does_not_overwrite_cancelled(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """_try_failed_statusはcancelledを上書きしない"""
        from genglossary.db.connection import database_connection, transaction
        from genglossary.db.runs_repository import cancel_run as db_cancel_run

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            cancel_set = Event()

            def mock_execute(conn, scope, context, doc_root="."):
                # Signal that we are ready to be cancelled
                cancel_set.set()
                # Wait to allow cancel to happen
                time.sleep(0.2)
                # Simulate failure after cancel is set
                raise RuntimeError("Test error after cancel")

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")

            # Wait for execution to reach the point where it can be cancelled
            cancel_set.wait(timeout=5)

            # Cancel the run via database directly
            with database_connection(manager.db_path) as conn:
                with transaction(conn):
                    db_cancel_run(conn, run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=3)

            # Status should remain cancelled, not changed to failed
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "cancelled", (
                f"Expected status 'cancelled' but got '{run['status']}'. "
                "_try_failed_status should not overwrite cancelled status."
            )

    def test_failed_status_does_not_overwrite_completed(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """_try_failed_statusはcompletedを上書きしない"""
        from genglossary.db.connection import database_connection, transaction
        from genglossary.db.runs_repository import complete_run_if_not_cancelled

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            exec_done = Event()

            def mock_execute(conn, scope, context, doc_root="."):
                # Signal that execution is complete
                exec_done.set()
                # Wait a bit before returning
                time.sleep(0.2)
                # Simulate error after completion is set
                raise RuntimeError("Test error after complete")

            mock_executor.return_value.execute.side_effect = mock_execute

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            exec_done.wait(timeout=5)

            # Complete the run via database directly
            with database_connection(manager.db_path) as conn:
                with transaction(conn):
                    complete_run_if_not_cancelled(conn, run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=3)

            # Status should remain completed, not changed to failed
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "completed", (
                f"Expected status 'completed' but got '{run['status']}'. "
                "_try_failed_status should not overwrite completed status."
            )

    def test_failed_status_logs_when_skipped(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """_try_failed_statusがスキップされた場合、infoログが出力される"""
        from genglossary.db.connection import database_connection, transaction
        from genglossary.db.runs_repository import cancel_run as db_cancel_run

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            cancel_set = Event()

            def mock_execute(conn, scope, context, doc_root="."):
                cancel_set.set()
                time.sleep(0.2)
                raise RuntimeError("Test error after cancel")

            mock_executor.return_value.execute.side_effect = mock_execute

            # Subscribe to logs
            queue = manager.register_subscriber(run_id=1)

            run_id = manager.start_run(scope="full")

            # Wait for execution
            cancel_set.wait(timeout=5)

            # Cancel the run
            with database_connection(manager.db_path) as conn:
                with transaction(conn):
                    db_cancel_run(conn, run_id)

            # Wait for thread to complete
            if manager._thread:
                manager._thread.join(timeout=3)

            # Check that info log was broadcast about skipped failed status
            logs = []
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and not log.get("complete"):
                    logs.append(log)

            assert any(
                "Failed skipped" in log.get("message", "")
                and log.get("level") == "info"
                for log in logs
            ), "Info log about skipped failed status should be broadcast"


class TestRunManagerStateConsistency:
    """Tests for in-memory state consistency improvements.

    Issues addressed:
    1. _current_run_id was unused and should be removed.
    2. _cancel_events should be set within _start_run_lock.
    3. Thread start failure should cleanup _cancel_events and update DB status.
    """

    def test_current_run_id_attribute_does_not_exist(
        self, manager: RunManager
    ) -> None:
        """_current_run_id属性が存在しないことを確認（未使用のため削除済み）"""
        assert not hasattr(manager, "_current_run_id"), (
            "_current_run_id attribute should not exist (removed as unused)"
        )

    def test_thread_start_failure_cleans_up_cancel_event(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """Thread.start()が失敗した場合、_cancel_eventsからクリーンアップされる"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            # Mock Thread to raise on start()
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            with pytest.raises(RuntimeError, match="Failed to start thread"):
                manager.start_run(scope="full")

            # Cancel event should be cleaned up
            assert len(manager._cancel_events) == 0, (
                "Cancel event should be cleaned up when thread start fails"
            )

    def test_thread_start_failure_updates_db_status_to_failed(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """Thread.start()が失敗した場合、DBステータスがfailedに更新される"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            # Mock Thread to raise on start()
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            with pytest.raises(RuntimeError, match="Failed to start thread"):
                run_id = manager.start_run(scope="full")

            # Get the run_id from the database (since start_run raises, we need to find it)
            cursor = project_db.execute(
                "SELECT id, status, error_message FROM runs ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            assert row is not None

            assert row["status"] == "failed", (
                f"Expected status 'failed' but got '{row['status']}'"
            )
            error_message = row["error_message"] or ""
            assert "Failed to start execution thread" in error_message
            assert "Failed to start thread" in error_message, (
                "Original exception details should be included in error_message"
            )

    def test_thread_start_failure_reraises_exception(
        self, manager: RunManager
    ) -> None:
        """Thread.start()が失敗した場合、例外が再送出される"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            with pytest.raises(RuntimeError, match="Failed to start thread"):
                manager.start_run(scope="full")

    def test_thread_start_failure_sets_finished_at(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """Thread.start()が失敗した場合、finished_atが設定される"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            with pytest.raises(RuntimeError, match="Failed to start thread"):
                manager.start_run(scope="full")

            # Get the run from the database
            cursor = project_db.execute(
                "SELECT id, finished_at FROM runs ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            assert row is not None

            assert row["finished_at"] is not None, (
                "finished_at should be set when thread start fails"
            )

    def test_thread_start_failure_resets_thread_reference(
        self, manager: RunManager
    ) -> None:
        """Thread.start()が失敗した場合、self._threadがNoneにリセットされる"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            with pytest.raises(RuntimeError, match="Failed to start thread"):
                manager.start_run(scope="full")

            # _thread should be reset to None
            assert manager._thread is None, (
                "_thread should be None when thread start fails"
            )

    def test_thread_start_failure_sends_completion_signal(
        self, manager: RunManager
    ) -> None:
        """Thread.start()が失敗した場合、完了シグナルが送信される"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            # Register subscriber before starting run
            # We need to predict the run_id (will be 1 for first run)
            queue = manager.register_subscriber(run_id=1)

            with pytest.raises(RuntimeError, match="Failed to start thread"):
                manager.start_run(scope="full")

            # Check that completion signal was sent
            completion_signal_found = False
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and log.get("complete"):
                    completion_signal_found = True
                    break

            assert completion_signal_found, (
                "Completion signal should be sent when thread start fails"
            )

    def test_thread_start_failure_cleans_up_subscribers(
        self, manager: RunManager
    ) -> None:
        """Thread.start()が失敗した場合、subscribersがクリーンアップされる"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            # Register subscriber before starting run
            queue = manager.register_subscriber(run_id=1)

            with pytest.raises(RuntimeError, match="Failed to start thread"):
                manager.start_run(scope="full")

            # Subscribers should be cleaned up
            with manager._subscribers_lock:
                assert 1 not in manager._subscribers, (
                    "Subscribers should be cleaned up when thread start fails"
                )

    def test_thread_start_failure_does_not_mask_original_exception(
        self, manager: RunManager
    ) -> None:
        """Thread.start()が失敗し、DB更新も失敗した場合、元の例外がマスクされない"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            mock_thread = Mock()
            original_error = RuntimeError("Original thread start error")
            mock_thread.start.side_effect = original_error
            mock_thread_class.return_value = mock_thread

            # Make DB update also fail
            with patch(
                "genglossary.runs.manager.update_run_status",
                side_effect=sqlite3.OperationalError("database is locked"),
            ):
                with pytest.raises(RuntimeError) as exc_info:
                    manager.start_run(scope="full")

                # The original exception should be raised, not the DB error
                assert "Original thread start error" in str(exc_info.value), (
                    f"Original exception should be raised, got: {exc_info.value}"
                )

    def test_thread_start_failure_logs_warning_when_db_update_fails(
        self, manager: RunManager
    ) -> None:
        """Thread.start()が失敗し、DB更新も失敗した場合、warningログが送信される"""
        with patch("genglossary.runs.manager.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread.start.side_effect = RuntimeError("Failed to start thread")
            mock_thread_class.return_value = mock_thread

            # Register subscriber before starting run
            queue = manager.register_subscriber(run_id=1)

            # Make DB update fail
            with patch(
                "genglossary.runs.manager.update_run_status",
                side_effect=sqlite3.OperationalError("database is locked"),
            ):
                with pytest.raises(RuntimeError):
                    manager.start_run(scope="full")

            # Check that warning log was broadcast
            warning_log_found = False
            while not queue.empty():
                log = queue.get_nowait()
                if log is not None and log.get("level") == "warning":
                    if "Failed to update run status" in log.get("message", ""):
                        warning_log_found = True
                        break

            assert warning_log_found, (
                "Warning log should be broadcast when DB update fails during thread start failure"
            )


class TestRunManagerStatusMisclassification:
    """Tests for status misclassification bug fix.

    Issue: When pipeline succeeds but status update fails (e.g., DB locked),
    the run is incorrectly marked as 'failed' instead of 'completed'.
    Similarly, when cancellation status update fails, it's marked as 'failed'
    instead of 'cancelled'.
    """

    def test_pipeline_success_with_complete_run_db_failure_still_shows_completed(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """パイプラインが成功し、update_run_status_if_activeでDBエラーが発生しても、
        リトライによりステータスはcompletedになる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Pipeline executes successfully
            mock_executor.return_value.execute.return_value = None

            # update_run_status_if_active fails first time, succeeds on retry
            original_update = __import__(
                "genglossary.db.runs_repository", fromlist=["update_run_status_if_active"]
            ).update_run_status_if_active

            call_count = {"value": 0}

            def mock_update(conn, run_id, status, error_message=None):
                call_count["value"] += 1
                if call_count["value"] == 1:
                    raise sqlite3.OperationalError("database is locked")
                return original_update(conn, run_id, status, error_message)

            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=mock_update,
            ):
                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Status should be completed, not failed
                run = get_run(project_db, run_id)
                assert run is not None
                assert run["status"] == "completed", (
                    f"Expected status 'completed' but got '{run['status']}'. "
                    "Pipeline succeeded but DB update failure caused misclassification."
                )

    def test_cancel_with_db_update_failure_shows_cancelled_not_failed(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """キャンセルでDBステータス更新(update_run_status_if_active)が失敗しても、
        リトライによりステータスはcancelledになる"""
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor that waits for cancellation and raises PipelineCancelledException
            def cancellable_execute(conn, scope, context, doc_root="."):
                for _ in range(50):
                    if context.cancel_event.is_set():
                        raise PipelineCancelledException()
                    time.sleep(0.1)

            mock_executor.return_value.execute.side_effect = cancellable_execute

            # update_run_status_if_active for 'cancelled' fails first time, succeeds on retry
            original_update = __import__(
                "genglossary.db.runs_repository", fromlist=["update_run_status_if_active"]
            ).update_run_status_if_active

            call_count = {"value": 0}

            def mock_update(conn, run_id, status, error_message=None):
                if status == "cancelled":
                    call_count["value"] += 1
                    if call_count["value"] == 1:
                        raise sqlite3.OperationalError("database is locked")
                return original_update(conn, run_id, status, error_message)

            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=mock_update,
            ):
                run_id = manager.start_run(scope="full")
                time.sleep(0.1)  # Allow thread to start

                manager.cancel_run(run_id)

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Status should be cancelled, not failed
                run = get_run(project_db, run_id)
                assert run is not None
                assert run["status"] == "cancelled", (
                    f"Expected status 'cancelled' but got '{run['status']}'. "
                    "Cancellation status update failure caused misclassification."
                )

    def test_pipeline_success_prioritizes_completed_over_failed_on_all_db_failures(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """パイプラインが成功し、すべてのDBステータス更新が失敗しても、
        ステータスはfailedではなくcompletedのまま（または適切にログされる）"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Pipeline executes successfully
            mock_executor.return_value.execute.return_value = None

            # All update_run_status_if_active calls fail
            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=sqlite3.OperationalError("database is locked"),
            ):
                # Subscribe to logs before starting run
                queue = manager.register_subscriber(run_id=1)

                run_id = manager.start_run(scope="full")

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Even if all DB updates fail, the run should NOT be marked as
                # failed (which would be a misclassification). The status
                # should remain 'running' since the pipeline actually succeeded.
                run = get_run(project_db, run_id)
                assert run is not None
                # Status should NOT be 'failed' since pipeline succeeded
                assert run["status"] != "failed", (
                    f"Status should not be 'failed' when pipeline succeeded. "
                    f"Got '{run['status']}'."
                )

    def test_cancel_prioritizes_cancelled_over_failed_on_all_db_failures(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """キャンセルでDBステータス更新がすべて失敗しても、
        ステータスはfailedではない（キャンセルが優先される）"""
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor that waits for cancellation and raises PipelineCancelledException
            def cancellable_execute(conn, scope, context, doc_root="."):
                for _ in range(50):
                    if context.cancel_event.is_set():
                        raise PipelineCancelledException()
                    time.sleep(0.1)

            mock_executor.return_value.execute.side_effect = cancellable_execute

            # All update_run_status_if_active calls for 'cancelled' fail
            def failing_update(conn, run_id, status, error_message=None):
                from genglossary.db.runs_repository import RunUpdateResult

                if status == "cancelled":
                    raise sqlite3.OperationalError("database is locked")
                # Allow other status updates
                return RunUpdateResult.UPDATED

            with patch(
                "genglossary.runs.manager.update_run_status_if_active",
                side_effect=failing_update,
            ):
                # Subscribe to logs before starting run
                queue = manager.register_subscriber(run_id=1)

                run_id = manager.start_run(scope="full")
                time.sleep(0.1)  # Allow thread to start

                manager.cancel_run(run_id)

                # Wait for thread to complete
                if manager._thread:
                    manager._thread.join(timeout=2)

                # Status should NOT be 'failed' since cancellation was requested
                run = get_run(project_db, run_id)
                assert run is not None
                assert run["status"] != "failed", (
                    f"Status should not be 'failed' when cancellation was requested. "
                    f"Got '{run['status']}'."
                )


class TestPipelineCancelledExceptionHandling:
    """Tests for manager handling of PipelineCancelledException from executor."""

    def test_cancelled_exception_sets_status_to_cancelled(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """PipelineCancelledException が発生した場合、ステータスは cancelled になる"""
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor to raise PipelineCancelledException
            mock_executor.return_value.execute.side_effect = PipelineCancelledException()

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that run status is "cancelled"
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "cancelled", (
                f"Expected status 'cancelled' but got '{run['status']}'. "
                "PipelineCancelledException should result in cancelled status."
            )

    def test_regular_exception_sets_status_to_failed(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """通常の例外が発生した場合、ステータスは failed になる（回帰テスト）"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            # Mock executor to raise regular exception
            mock_executor.return_value.execute.side_effect = RuntimeError("Something went wrong")

            run_id = manager.start_run(scope="full")

            # Wait for execution to complete
            if manager._thread:
                manager._thread.join(timeout=2)

            # Check that run status is "failed"
            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "failed", (
                f"Expected status 'failed' but got '{run['status']}'. "
                "Regular exceptions should result in failed status."
            )
            assert "Something went wrong" in (run["error_message"] or "")

    def test_cancelled_exception_does_not_set_error_message(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """PipelineCancelledException の場合、error_message は設定されない"""
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = PipelineCancelledException()

            run_id = manager.start_run(scope="full")

            if manager._thread:
                manager._thread.join(timeout=2)

            run = get_run(project_db, run_id)
            assert run is not None
            # error_message should be None or empty for cancellation
            assert run["error_message"] is None or run["error_message"] == "", (
                f"error_message should be empty for cancellation, got '{run['error_message']}'"
            )


class TestRunManagerLlmBaseUrl:
    """Tests for llm_base_url parameter propagation to PipelineExecutor."""

    def test_manager_passes_llm_base_url_to_executor(
        self, project_db_path: str
    ) -> None:
        """RunManagerがllm_base_urlをPipelineExecutorに渡すことを確認"""
        custom_url = "http://192.168.1.100:11434"

        manager = RunManager(
            db_path=project_db_path,
            llm_provider="ollama",
            llm_model="test-model",
            llm_base_url=custom_url,
        )

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")

            # Wait for thread to start and create executor
            if manager._thread:
                manager._thread.join(timeout=2)

            mock_executor.assert_called_once()
            call_kwargs = mock_executor.call_args.kwargs
            assert call_kwargs.get("base_url") == custom_url

    def test_manager_passes_none_base_url_when_not_provided(
        self, project_db_path: str
    ) -> None:
        """RunManagerがllm_base_urlを指定しない場合、Noneが渡されることを確認"""
        manager = RunManager(
            db_path=project_db_path,
            llm_provider="ollama",
            llm_model="test-model",
        )

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            manager.start_run(scope="full")

            if manager._thread:
                manager._thread.join(timeout=2)

            mock_executor.assert_called_once()
            call_kwargs = mock_executor.call_args.kwargs
            # base_url should be None when llm_base_url is empty (fallback to config)
            assert call_kwargs.get("base_url") is None


class TestRunManagerCleanupRunResources:
    """Tests for _cleanup_run_resources method.

    This method consolidates the cleanup logic that was previously duplicated
    in start_run exception handler and _execute_run finally block.
    """

    def test_cleanup_run_resources_removes_cancel_event(
        self, manager: RunManager
    ) -> None:
        """_cleanup_run_resourcesがcancel_eventをクリーンアップする"""
        run_id = 1
        # Setup: add a cancel event
        cancel_event = Event()
        with manager._cancel_events_lock:
            manager._cancel_events[run_id] = cancel_event

        # Execute cleanup
        manager._cleanup_run_resources(run_id)

        # Verify cancel event was removed
        with manager._cancel_events_lock:
            assert run_id not in manager._cancel_events

    def test_cleanup_run_resources_broadcasts_completion_signal(
        self, manager: RunManager
    ) -> None:
        """_cleanup_run_resourcesが完了シグナルをブロードキャストする"""
        run_id = 1
        # Setup: register a subscriber
        queue = manager.register_subscriber(run_id)

        # Execute cleanup
        manager._cleanup_run_resources(run_id)

        # Verify completion signal was sent
        completion_signal_found = False
        while not queue.empty():
            msg = queue.get_nowait()
            if msg.get("complete") and msg.get("run_id") == run_id:
                completion_signal_found = True
                break

        assert completion_signal_found, (
            "Completion signal should be broadcast by _cleanup_run_resources"
        )

    def test_cleanup_run_resources_removes_subscribers(
        self, manager: RunManager
    ) -> None:
        """_cleanup_run_resourcesがsubscribersをクリーンアップする"""
        run_id = 1
        # Setup: register a subscriber
        queue = manager.register_subscriber(run_id)

        # Execute cleanup
        manager._cleanup_run_resources(run_id)

        # Verify subscribers were removed
        with manager._subscribers_lock:
            assert run_id not in manager._subscribers

    def test_cleanup_run_resources_is_idempotent(
        self, manager: RunManager
    ) -> None:
        """_cleanup_run_resourcesは冪等である（複数回呼び出しても安全）"""
        run_id = 1
        # Setup: add cancel event and subscriber
        cancel_event = Event()
        with manager._cancel_events_lock:
            manager._cancel_events[run_id] = cancel_event
        queue = manager.register_subscriber(run_id)

        # Execute cleanup twice
        manager._cleanup_run_resources(run_id)
        manager._cleanup_run_resources(run_id)  # Should not raise

        # Verify cleanup was done
        with manager._cancel_events_lock:
            assert run_id not in manager._cancel_events
        with manager._subscribers_lock:
            assert run_id not in manager._subscribers

    def test_cleanup_run_resources_handles_missing_resources(
        self, manager: RunManager
    ) -> None:
        """_cleanup_run_resourcesは存在しないリソースでも安全"""
        run_id = 999  # Non-existent run_id

        # Should not raise
        manager._cleanup_run_resources(run_id)


class TestRunManagerLogMessageDistinction:
    """Tests for distinguishing log messages between 'not found' and 'not in expected state'."""

    def test_try_update_status_logs_not_found_for_nonexistent_run(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """存在しないrunを更新しようとした場合、'not found'をログ出力する"""
        # Use non-existent run_id
        nonexistent_run_id = 99999
        log_messages: list[dict] = []

        def capture_log(run_id: int, message: dict) -> None:
            log_messages.append(message)

        manager._broadcast_log = capture_log  # type: ignore

        # Call _try_update_status directly with non-existent run
        result = manager._try_update_status(project_db, nonexistent_run_id, "cancelled")

        # Should return True (no fallback needed, even though run not found)
        assert result is True

        # Find the log message about skipped operation
        skipped_logs = [m for m in log_messages if "skipped" in m.get("message", "").lower()]
        assert len(skipped_logs) == 1
        assert "not found" in skipped_logs[0]["message"].lower()
        assert "terminal" not in skipped_logs[0]["message"].lower()

    def test_try_update_status_logs_not_in_expected_state_for_terminal_run(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """既にterminal状態のrunを更新しようとした場合、'not in expected state'をログ出力する"""
        from genglossary.db.runs_repository import update_run_status
        from datetime import datetime, timezone

        # Create a run and set it to completed (terminal state)
        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "completed",
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc)
        )

        log_messages: list[dict] = []

        def capture_log(run_id: int, message: dict) -> None:
            log_messages.append(message)

        manager._broadcast_log = capture_log  # type: ignore

        # Call _try_update_status directly with terminal run (not in expected state)
        result = manager._try_update_status(project_db, run_id, "cancelled")

        # Should return True (no fallback needed, not in expected state)
        assert result is True

        # Find the log message about skipped operation
        skipped_logs = [m for m in log_messages if "skipped" in m.get("message", "").lower()]
        assert len(skipped_logs) == 1
        assert "not in expected state" in skipped_logs[0]["message"].lower()
        assert "not found" not in skipped_logs[0]["message"].lower()


class TestTryUpdateStatusCommits:
    """Tests that _try_update_status commits after updating.

    Verified by checking that changes ARE visible from a separate connection
    (committed changes are visible across connections in SQLite).
    """

    def test_try_update_status_commits_after_update(
        self, manager: RunManager, project_db_path: str
    ) -> None:
        """_try_update_statusの更新後、別接続からデータが見える（commitされている）"""
        from datetime import datetime, timezone
        from genglossary.db.connection import get_connection
        from genglossary.db.runs_repository import update_run_status

        conn = get_connection(project_db_path)
        try:
            run_id = create_run(conn, scope="full")
            update_run_status(
                conn, run_id, "running",
                started_at=datetime.now(timezone.utc),
            )

            result = manager._try_update_status(conn, run_id, "completed")
            assert result is True

            # Verify from a separate connection that commit happened
            reader = get_connection(project_db_path)
            try:
                row = reader.execute(
                    "SELECT status FROM runs WHERE id = ?", (run_id,)
                ).fetchone()
                assert row["status"] == "completed"
            finally:
                reader.close()
        finally:
            conn.close()


class TestCleanupRunResourcesWithDbStatus:
    """Tests for _cleanup_run_resources with db_status parameter."""

    def test_cleanup_includes_db_status_in_completion_signal(
        self, manager: RunManager
    ) -> None:
        """完了シグナルにdb_statusが含まれる"""
        run_id = 1

        # Add a cancel event so cleanup has something to clean
        with manager._cancel_events_lock:
            manager._cancel_events[run_id] = Event()

        manager._cleanup_run_resources(run_id, db_status="completed")

        # Check stored completion signal
        assert run_id in manager._completed_runs
        completion_signal = manager._completed_runs[run_id]
        assert completion_signal.get("complete") is True
        assert completion_signal["db_status"] == "completed"

    def test_cleanup_includes_status_update_failed_flag(
        self, manager: RunManager
    ) -> None:
        """ステータス更新失敗時にstatus_update_failedフラグが含まれる"""
        run_id = 1

        with manager._cancel_events_lock:
            manager._cancel_events[run_id] = Event()

        manager._cleanup_run_resources(
            run_id, db_status="failed", status_update_failed=True
        )

        assert run_id in manager._completed_runs
        completion_signal = manager._completed_runs[run_id]
        assert completion_signal["db_status"] == "failed"
        assert completion_signal["status_update_failed"] is True

    def test_cleanup_without_db_status_omits_field(
        self, manager: RunManager
    ) -> None:
        """db_statusが指定されない場合はフィールドを含めない"""
        run_id = 1

        with manager._cancel_events_lock:
            manager._cancel_events[run_id] = Event()

        manager._cleanup_run_resources(run_id)

        assert run_id in manager._completed_runs
        completion_signal = manager._completed_runs[run_id]
        assert completion_signal.get("complete") is True
        assert "db_status" not in completion_signal
        assert "status_update_failed" not in completion_signal


class TestTryUpdateStatusFallback:
    """Tests for _try_update_status fallback behavior."""

    def test_returns_true_on_primary_success(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """プライマリ接続での更新成功時にTrueを返す"""
        run_id = create_run(project_db, scope="full")

        result = manager._try_update_status(project_db, run_id, "cancelled")
        assert result is True

    def test_falls_back_to_new_connection_on_primary_exception(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """プライマリ接続で例外が発生した場合、フォールバック接続で再試行する"""
        run_id = create_run(project_db, scope="full")
        project_db.commit()  # Commit so fallback connection can see the run

        call_count = {"value": 0}
        original_update = __import__(
            "genglossary.db.runs_repository", fromlist=["update_run_status_if_active"]
        ).update_run_status_if_active

        def failing_then_succeeding(conn, rid, status, error_message=None):
            call_count["value"] += 1
            if call_count["value"] == 1:
                raise sqlite3.OperationalError("database is locked")
            return original_update(conn, rid, status, error_message)

        with patch(
            "genglossary.runs.manager.update_run_status_if_active",
            side_effect=failing_then_succeeding,
        ):
            result = manager._try_update_status(project_db, run_id, "cancelled")

        assert result is True
        assert call_count["value"] == 2

    def test_conn_none_uses_fallback_directly(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """conn=Noneの場合、直接フォールバック接続を使用する"""
        run_id = create_run(project_db, scope="full")
        project_db.commit()  # Commit so fallback connection can see the run

        result = manager._try_update_status(None, run_id, "cancelled")
        assert result is True

        # Verify the status was actually updated
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "cancelled"

    def test_returns_false_when_both_connections_fail(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """両方の接続で失敗した場合にFalseを返す"""
        run_id = create_run(project_db, scope="full")

        manager._broadcast_log = Mock()  # type: ignore

        with patch(
            "genglossary.runs.manager.update_run_status_if_active",
            side_effect=sqlite3.OperationalError("database is locked"),
        ), patch(
            "genglossary.runs.manager.database_connection",
            side_effect=sqlite3.OperationalError("cannot open database"),
        ):
            result = manager._try_update_status(project_db, run_id, "cancelled")

        assert result is False


class TestFinalizeRunStatusReturnValue:
    """Tests for _finalize_run_status return value."""

    def test_returns_completed_status_on_success(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """パイプライン成功時に('completed', True)を返す"""
        run_id = create_run(project_db, scope="full")

        result = manager._finalize_run_status(
            project_db, run_id, pipeline_error=None
        )

        assert result == ("completed", True)

    def test_returns_cancelled_status_on_cancellation(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """キャンセル時に('cancelled', True)を返す"""
        from genglossary.runs.executor import PipelineCancelledException

        run_id = create_run(project_db, scope="full")

        result = manager._finalize_run_status(
            project_db, run_id, pipeline_error=PipelineCancelledException()
        )

        assert result == ("cancelled", True)

    def test_returns_failed_status_on_error(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """エラー時に('failed', True)を返す"""
        run_id = create_run(project_db, scope="full")

        # Suppress logging and broadcast
        manager._broadcast_log = Mock()  # type: ignore

        result = manager._finalize_run_status(
            project_db, run_id, pipeline_error=Exception("test error")
        )

        assert result == ("failed", True)

    def test_returns_false_when_update_fails(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """DB更新失敗時に(status, False)を返す"""
        run_id = create_run(project_db, scope="full")

        # Mock _try_update_status to always fail
        original_method = manager._try_update_status
        manager._try_update_status = Mock(return_value=False)  # type: ignore

        result = manager._finalize_run_status(
            project_db, run_id, pipeline_error=None
        )

        assert result[0] == "completed"
        assert result[1] is False

        # Restore original method
        manager._try_update_status = original_method  # type: ignore




class TestSubscriberCompletedRunRegistration:
    """Tests for subscriber registration on already completed runs."""

    def test_subscriber_registered_after_cleanup_receives_completion_immediately(
        self, manager: RunManager
    ) -> None:
        """既に完了したrunに登録したsubscriberは即座に完了シグナルを受け取る"""
        from queue import Empty

        run_id = 1

        # Set up cancel event
        with manager._cancel_events_lock:
            manager._cancel_events[run_id] = Event()

        # Complete the run
        manager._cleanup_run_resources(run_id, db_status="completed")

        # Register subscriber after run has completed
        queue = manager.register_subscriber(run_id)

        # Subscriber should immediately receive completion signal
        try:
            msg = queue.get(timeout=0.5)
        except Empty:
            msg = None

        assert msg is not None, (
            "Subscriber registered after run completion should receive "
            "completion signal immediately"
        )
        assert msg.get("complete") is True
        assert msg.get("db_status") == "completed"


class TestExecutorCloseOnCompletion:
    """Tests for executor.close() being called after pipeline execution."""

    def test_executor_closed_on_successful_completion(
        self, manager: RunManager
    ) -> None:
        """正常完了時にexecutor.close()が呼ばれる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="full")

            if manager._thread:
                manager._thread.join(timeout=2)

            mock_executor.return_value.close.assert_called()

    def test_executor_closed_on_pipeline_failure(
        self, manager: RunManager
    ) -> None:
        """パイプライン失敗時にexecutor.close()が呼ばれる"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = RuntimeError("Pipeline error")

            run_id = manager.start_run(scope="full")

            if manager._thread:
                manager._thread.join(timeout=2)

            mock_executor.return_value.close.assert_called()

    def test_executor_close_exception_does_not_mask_pipeline_error(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """executor.close()の例外がパイプラインエラーを上書きしない"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = RuntimeError("Pipeline error")
            mock_executor.return_value.close.side_effect = OSError("Close failed")

            run_id = manager.start_run(scope="full")

            if manager._thread:
                manager._thread.join(timeout=2)

            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "failed"
            assert "Pipeline error" in (run["error_message"] or "")

    def test_executor_close_exception_does_not_mask_completed_status(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """executor.close()の例外が正常完了ステータスを上書きしない"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None
            mock_executor.return_value.close.side_effect = OSError("Close failed")

            run_id = manager.start_run(scope="full")

            if manager._thread:
                manager._thread.join(timeout=2)

            run = get_run(project_db, run_id)
            assert run is not None
            assert run["status"] == "completed"

    def test_executor_closed_on_cancellation(
        self, manager: RunManager
    ) -> None:
        """キャンセル時にexecutor.close()が呼ばれる"""
        from genglossary.runs.executor import PipelineCancelledException

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.side_effect = PipelineCancelledException()

            run_id = manager.start_run(scope="full")

            if manager._thread:
                manager._thread.join(timeout=2)

            mock_executor.return_value.close.assert_called()


class TestRunManagerDocumentIds:
    """Tests for RunManager.start_run with document_ids parameter."""

    def test_start_run_passes_document_ids_to_executor(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """start_runのdocument_idsがexecutor.executeに渡される"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(
                scope="extract", triggered_by="auto", document_ids=[1, 2, 3]
            )

            if manager._thread:
                manager._thread.join(timeout=2)

            # Verify executor.execute was called with document_ids
            mock_executor.return_value.execute.assert_called_once()
            call_kwargs = mock_executor.return_value.execute.call_args
            assert call_kwargs.kwargs.get("document_ids") == [1, 2, 3]

    def test_start_run_without_document_ids_passes_none(
        self, manager: RunManager, project_db: sqlite3.Connection
    ) -> None:
        """document_ids未指定時はNoneが渡される"""
        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor:
            mock_executor.return_value.execute.return_value = None

            run_id = manager.start_run(scope="extract")

            if manager._thread:
                manager._thread.join(timeout=2)

            mock_executor.return_value.execute.assert_called_once()
            call_kwargs = mock_executor.return_value.execute.call_args
            assert call_kwargs.kwargs.get("document_ids") is None