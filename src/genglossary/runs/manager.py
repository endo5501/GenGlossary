"""Run manager for background pipeline execution."""

import sqlite3
import traceback
from collections.abc import Callable
from datetime import datetime
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread

from genglossary.db.connection import database_connection, get_connection, transaction
from genglossary.db.runs_repository import (
    cancel_run,
    complete_run_if_not_cancelled,
    create_run,
    fail_run_if_not_terminal,
    get_active_run,
    get_run,
    update_run_status,
)
from genglossary.runs.executor import ExecutionContext, PipelineExecutor


class RunManager:
    """Manages background execution of glossary generation pipeline.

    Ensures only one active run per project and provides log streaming.
    """

    # Maximum log queue size to prevent unbounded memory growth
    MAX_LOG_QUEUE_SIZE = 1000

    def __init__(
        self,
        db_path: str,
        doc_root: str = ".",
        llm_provider: str = "ollama",
        llm_model: str = "",
    ):
        """Initialize the RunManager.

        Args:
            db_path: Path to project database.
            doc_root: Root directory for documents (default: ".").
            llm_provider: LLM provider name (default: "ollama").
            llm_model: LLM model name (default: "").
        """
        self.db_path = db_path
        self.doc_root = doc_root
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self._thread: Thread | None = None
        self._cancel_events: dict[int, Event] = {}
        self._cancel_events_lock = Lock()
        self._start_run_lock = Lock()  # Synchronize start_run to prevent race conditions
        self._current_run_id: int | None = None
        # Subscriber管理
        self._subscribers: dict[int, set[Queue]] = {}
        self._subscribers_lock = Lock()

    def start_run(self, scope: str, triggered_by: str = "api") -> int:
        """Start a new run in the background.

        Args:
            scope: Run scope ('full', 'from_terms', 'provisional_to_refined').
            triggered_by: Source that triggered the run (default: 'api').

        Returns:
            int: The ID of the newly created run.

        Raises:
            RuntimeError: If a run is already running.
        """
        # Synchronize to prevent race conditions between concurrent start_run calls
        with self._start_run_lock:
            # Check if a run is already active and create run record atomically
            with database_connection(self.db_path) as conn:
                active_run = get_active_run(conn)
                if active_run is not None:
                    raise RuntimeError(f"Run already running: {active_run['id']}")

                # Create run record atomically within the same lock
                with transaction(conn):
                    run_id = create_run(conn, scope=scope, triggered_by=triggered_by)

        self._current_run_id = run_id

        # Create cancel event for this run
        cancel_event = Event()
        with self._cancel_events_lock:
            self._cancel_events[run_id] = cancel_event

        # Start background thread
        self._thread = Thread(target=self._execute_run, args=(run_id, scope))
        self._thread.daemon = True
        self._thread.start()

        return run_id

    def _execute_run(self, run_id: int, scope: str) -> None:
        """Execute run in background thread.

        Args:
            run_id: Run ID.
            scope: Run scope.
        """
        conn = None
        pipeline_error: Exception | None = None
        pipeline_traceback: str | None = None

        try:
            # Create a new connection for this thread
            conn = get_connection(self.db_path)
            # Update status to running
            with transaction(conn):
                update_run_status(
                    conn, run_id, "running", started_at=datetime.now()
                )

            # ログコールバックを作成
            def log_callback(msg: dict) -> None:
                self._broadcast_log(run_id, msg)

            # Get cancel event (guaranteed to exist, created in start_run)
            with self._cancel_events_lock:
                cancel_event = self._cancel_events[run_id]

            # Create execution context
            context = ExecutionContext(
                run_id=run_id,
                log_callback=log_callback,
                cancel_event=cancel_event,
            )

            # Execute pipeline with project settings
            executor = PipelineExecutor(
                provider=self.llm_provider,
                model=self.llm_model,
            )

            # Separate try/except for pipeline execution
            try:
                executor.execute(
                    conn,
                    scope,
                    context,
                    doc_root=self.doc_root,
                )
            except Exception as e:
                pipeline_error = e
                pipeline_traceback = traceback.format_exc()

            # Finalize run status (separate from pipeline execution)
            self._finalize_run_status(
                conn, run_id, cancel_event, pipeline_error, pipeline_traceback
            )

        except Exception as e:
            # Connection errors or other errors outside pipeline execution
            error_message = str(e)
            error_traceback = traceback.format_exc()
            self._update_failed_status(conn, run_id, error_message)
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "error",
                    "message": f"Run failed: {error_message}",
                    "traceback": error_traceback,
                },
            )
        finally:
            # Cleanup cancel event for this run
            with self._cancel_events_lock:
                self._cancel_events.pop(run_id, None)
            # Send completion signal to close SSE stream
            self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
            # Clear subscribers for this run to prevent memory leak
            with self._subscribers_lock:
                self._subscribers.pop(run_id, None)
            # Close the connection when thread completes
            if conn is not None:
                conn.close()

    def cancel_run(self, run_id: int) -> None:
        """Cancel a running run by setting its cancellation event.

        Note: The database status will be updated by the execution thread
        when it detects the cancellation.

        Args:
            run_id: Run ID to cancel.
        """
        with self._cancel_events_lock:
            cancel_event = self._cancel_events.get(run_id)
            if cancel_event is not None:
                cancel_event.set()

    def get_active_run(self) -> sqlite3.Row | None:
        """Get the currently active run.

        Returns:
            sqlite3.Row if found, None otherwise.
        """
        with database_connection(self.db_path) as conn:
            return get_active_run(conn)

    def get_run(self, run_id: int) -> sqlite3.Row | None:
        """Get run details by ID.

        Args:
            run_id: Run ID.

        Returns:
            sqlite3.Row if found, None otherwise.
        """
        with database_connection(self.db_path) as conn:
            return get_run(conn, run_id)

    def register_subscriber(self, run_id: int) -> Queue:
        """SSEクライアント用のQueueを作成し登録する.

        Args:
            run_id: Run ID.

        Returns:
            Queue: ログメッセージを受信するためのQueue.
        """
        queue: Queue = Queue(maxsize=self.MAX_LOG_QUEUE_SIZE)
        with self._subscribers_lock:
            if run_id not in self._subscribers:
                self._subscribers[run_id] = set()
            self._subscribers[run_id].add(queue)
        return queue

    def unregister_subscriber(self, run_id: int, queue: Queue) -> None:
        """SSEクライアントの登録を解除する.

        Args:
            run_id: Run ID.
            queue: 登録解除するQueue.
        """
        with self._subscribers_lock:
            if run_id in self._subscribers:
                self._subscribers[run_id].discard(queue)
                if not self._subscribers[run_id]:
                    del self._subscribers[run_id]

    def _put_to_queue(self, queue: Queue, message: dict) -> None:
        """Put message to queue, ensuring completion signals are delivered.

        Args:
            queue: Queue to put message to.
            message: Message to put.
        """
        if message.get("complete"):
            # For completion signals, make space if needed
            while queue.full():
                try:
                    queue.get_nowait()
                except Empty:
                    break
        try:
            queue.put_nowait(message)
        except Full:
            pass  # Only regular messages are dropped when full

    def _broadcast_log(self, run_id: int, message: dict) -> None:
        """全subscriberにログをブロードキャストする.

        Args:
            run_id: Run ID.
            message: ログメッセージ.
        """
        with self._subscribers_lock:
            if run_id in self._subscribers:
                for queue in self._subscribers[run_id]:
                    self._put_to_queue(queue, message)

    def _try_status_with_fallback(
        self,
        conn: sqlite3.Connection | None,
        run_id: int,
        status_updater: Callable[[sqlite3.Connection, int], bool],
        operation_name: str,
    ) -> None:
        """Try status update with fallback to new connection.

        Args:
            conn: Primary database connection (may be None or unusable).
            run_id: Run ID to update.
            status_updater: Function that takes (conn, run_id) and returns bool.
            operation_name: Name of the operation for error messages.
        """
        # Try primary connection
        if conn is not None and status_updater(conn, run_id):
            return

        # Fallback to new connection
        try:
            with database_connection(self.db_path) as fallback_conn:
                status_updater(fallback_conn, run_id)
        except Exception as e:
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to update {operation_name} status: {e}",
                },
            )

    def _finalize_run_status(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        cancel_event: Event,
        pipeline_error: Exception | None,
        pipeline_traceback: str | None = None,
    ) -> None:
        """Finalize run status after pipeline execution.

        Handles the status update logic separately from pipeline execution
        to prevent misclassification when status update fails.

        Priority:
        1. If pipeline had an error -> failed
        2. If cancelled -> cancelled
        3. Otherwise -> completed

        Args:
            conn: Database connection.
            run_id: Run ID.
            cancel_event: Cancellation event for this run.
            pipeline_error: Exception from pipeline execution, or None if successful.
            pipeline_traceback: Traceback from pipeline error, or None if successful.
        """
        if pipeline_error is not None:
            # Pipeline failed - update to failed status
            error_message = str(pipeline_error)
            error_traceback = pipeline_traceback or traceback.format_exc()
            self._update_failed_status(conn, run_id, error_message)
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "error",
                    "message": f"Run failed: {error_message}",
                    "traceback": error_traceback,
                },
            )
            return

        # Pipeline succeeded - determine final status
        if cancel_event.is_set():
            # Cancelled - try to update status with fallback
            self._try_status_with_fallback(
                conn, run_id, self._try_cancel_status, "cancelled"
            )
        else:
            # Completed - try atomic completion with fallback
            self._try_status_with_fallback(
                conn, run_id, self._try_complete_status, "completed"
            )

    def _try_cancel_status(
        self,
        conn: sqlite3.Connection,
        run_id: int,
    ) -> bool:
        """Try to update run status to cancelled.

        Returns:
            True if cancelled or already in terminal state (no fallback needed).
            False if failed with exception (fallback needed).
        """
        try:
            with transaction(conn):
                rows_updated = cancel_run(conn, run_id)
            if rows_updated == 0:
                # Run was already in terminal state - this is a no-op, not a failure
                self._broadcast_log(
                    run_id,
                    {
                        "run_id": run_id,
                        "level": "info",
                        "message": "Cancel skipped: run was already in terminal state",
                    },
                )
            # Both success and no-op return True (no fallback needed)
            return True
        except Exception as e:
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to update run status to cancelled: {e}",
                },
            )
            return False

    def _try_complete_status(
        self,
        conn: sqlite3.Connection,
        run_id: int,
    ) -> bool:
        """Try to update run status to completed.

        Returns:
            True if completed or no-op (no fallback needed).
            False if failed with exception (fallback needed).
        """
        try:
            with transaction(conn):
                was_updated = complete_run_if_not_cancelled(conn, run_id)
            if not was_updated:
                # Run was already cancelled/failed - this is a no-op, not a failure
                # No fallback needed since the terminal state is already set
                self._broadcast_log(
                    run_id,
                    {
                        "run_id": run_id,
                        "level": "info",
                        "message": "Completion skipped: run was already "
                        "cancelled or in terminal state",
                    },
                )
            # Both success and no-op return True (no fallback needed)
            return True
        except Exception as e:
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to update run status to completed: {e}",
                },
            )
            return False

    def _try_failed_status(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        error_message: str,
    ) -> bool:
        """Try to update run status to failed.

        Returns:
            True if failed or already in terminal state (no fallback needed).
            False if failed with exception (fallback needed).
        """
        try:
            with transaction(conn):
                was_updated = fail_run_if_not_terminal(conn, run_id, error_message)
            if not was_updated:
                # Run was already in terminal state - this is a no-op, not a failure
                self._broadcast_log(
                    run_id,
                    {
                        "run_id": run_id,
                        "level": "info",
                        "message": "Failed status skipped: run was already "
                        "in terminal state",
                    },
                )
            # Both success and no-op return True (no fallback needed)
            return True
        except Exception as e:
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to update run status: {e}",
                },
            )
            return False

    def _update_failed_status(
        self,
        conn: sqlite3.Connection | None,
        run_id: int,
        error_message: str,
    ) -> None:
        """Update run status to failed with fallback connection support.

        Tries to update using the provided connection first. If that fails
        (connection is None or unusable), falls back to a new connection.

        Args:
            conn: Primary database connection (may be None or unusable).
            run_id: Run ID to update.
            error_message: Error message to store.
        """
        self._try_status_with_fallback(
            conn,
            run_id,
            lambda c, rid: self._try_failed_status(c, rid, error_message),
            "failed",
        )
