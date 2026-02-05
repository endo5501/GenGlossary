"""Run manager for background pipeline execution."""

import sqlite3
import traceback
from collections.abc import Callable
from datetime import datetime, timezone
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread

from genglossary.db.connection import database_connection, get_connection, transaction
from genglossary.db.runs_repository import (
    RunUpdateResult,
    create_run,
    get_active_run,
    get_current_or_latest_run,
    get_run,
    update_run_status,
    update_run_status_if_active,
)
from genglossary.runs.executor import (
    ExecutionContext,
    PipelineCancelledException,
    PipelineExecutor,
)


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
        llm_base_url: str = "",
    ):
        """Initialize the RunManager.

        Args:
            db_path: Path to project database.
            doc_root: Root directory for documents (default: ".").
            llm_provider: LLM provider name (default: "ollama").
            llm_model: LLM model name (default: "").
            llm_base_url: Base URL for the LLM API (default: "").
        """
        self.db_path = db_path
        self.doc_root = doc_root
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url
        self._thread: Thread | None = None
        self._cancel_events: dict[int, Event] = {}
        self._cancel_events_lock = Lock()
        self._start_run_lock = Lock()  # Synchronize start_run to prevent race conditions
        # Executor管理 (for cancellation)
        self._executors: dict[int, PipelineExecutor] = {}
        self._executors_lock = Lock()
        # Subscriber管理
        self._subscribers: dict[int, set[Queue]] = {}
        self._subscribers_lock = Lock()

    def start_run(self, scope: str, triggered_by: str = "api") -> int:
        """Start a new run in the background.

        Args:
            scope: Run scope ('full', 'extract', 'generate', 'review', 'refine').
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

            # Create cancel event within the same lock to ensure consistency
            cancel_event = Event()
            with self._cancel_events_lock:
                self._cancel_events[run_id] = cancel_event

        # Start background thread (outside lock)
        try:
            self._thread = Thread(target=self._execute_run, args=(run_id, scope))
            self._thread.daemon = True
            self._thread.start()
        except Exception:
            # Reset thread reference (it was never started)
            self._thread = None

            # Try to update DB status, but don't mask the original exception
            try:
                with database_connection(self.db_path) as conn:
                    with transaction(conn):
                        update_run_status(
                            conn, run_id, "failed",
                            error_message="Failed to start execution thread",
                            finished_at=datetime.now(timezone.utc),
                        )
            except Exception as db_error:
                self._broadcast_log(
                    run_id,
                    {
                        "run_id": run_id,
                        "level": "warning",
                        "message": f"Failed to update run status after thread start failure: {db_error}",
                    },
                )

            # Cleanup run resources (cancel event, completion signal, subscribers)
            self._cleanup_run_resources(run_id)

            raise

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
                    conn, run_id, "running", started_at=datetime.now(timezone.utc)
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
                base_url=self.llm_base_url or None,
            )

            # Store executor for cancellation support
            with self._executors_lock:
                self._executors[run_id] = executor

            # Execute pipeline - exceptions indicate cancellation or failure
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
            finally:
                # Cleanup executor reference
                with self._executors_lock:
                    self._executors.pop(run_id, None)

            # Finalize run status (separate from pipeline execution)
            self._finalize_run_status(
                conn, run_id, pipeline_error, pipeline_traceback
            )

        except Exception as e:
            # Connection errors or other errors outside pipeline execution
            error_message = str(e)
            error_traceback = traceback.format_exc()
            # Log to console for debugging
            print(f"[ERROR] Run {run_id} failed (outside pipeline): {error_message}")
            print(f"[ERROR] Traceback:\n{error_traceback}")
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
            # Cleanup run resources (cancel event, completion signal, subscribers)
            self._cleanup_run_resources(run_id)
            # Close the connection when thread completes
            if conn is not None:
                conn.close()

    def cancel_run(self, run_id: int) -> None:
        """Cancel a running run by setting its cancellation event.

        This method sets the cancel event AND closes the LLM client
        to force-cancel any ongoing LLM API requests.

        Note: The database status will be updated by the execution thread
        when it detects the cancellation.

        Args:
            run_id: Run ID to cancel.
        """
        # Set the cancel event
        with self._cancel_events_lock:
            cancel_event = self._cancel_events.get(run_id)
            if cancel_event is not None:
                cancel_event.set()

        # Close the executor's LLM client to force-cancel ongoing requests
        with self._executors_lock:
            executor = self._executors.get(run_id)
            if executor is not None:
                executor.close()

    def get_active_run(self) -> sqlite3.Row | None:
        """Get the currently active run.

        Returns:
            sqlite3.Row if found, None otherwise.
        """
        with database_connection(self.db_path) as conn:
            return get_active_run(conn)

    def get_current_or_latest_run(self) -> sqlite3.Row | None:
        """Get the active run if exists, otherwise the latest run.

        This is useful for the /current endpoint to show completed runs
        after the pipeline finishes.

        Returns:
            sqlite3.Row if found, None otherwise.
        """
        with database_connection(self.db_path) as conn:
            return get_current_or_latest_run(conn)

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

    def _cleanup_run_resources(self, run_id: int) -> None:
        """Cleanup resources associated with a run.

        This method consolidates the cleanup logic that was previously duplicated
        in start_run exception handler and _execute_run finally block.

        The cleanup includes:
        1. Removing the cancel event
        2. Broadcasting completion signal
        3. Removing subscribers

        This method is idempotent - safe to call multiple times.

        Args:
            run_id: Run ID to cleanup.
        """
        with self._cancel_events_lock:
            self._cancel_events.pop(run_id, None)
        self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
        with self._subscribers_lock:
            self._subscribers.pop(run_id, None)

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
        pipeline_error: Exception | None,
        pipeline_traceback: str | None = None,
    ) -> None:
        """Finalize run status after pipeline execution.

        Handles the status update logic separately from pipeline execution
        to prevent misclassification when status update fails.

        Priority:
        1. If PipelineCancelledException -> cancelled
        2. If other exception -> failed
        3. No exception -> completed

        Args:
            conn: Database connection.
            run_id: Run ID.
            pipeline_error: Exception from pipeline execution, or None if successful.
            pipeline_traceback: Traceback from pipeline error, or None if successful.
        """
        if pipeline_error is not None:
            # Check if it's a cancellation exception
            if isinstance(pipeline_error, PipelineCancelledException):
                # Cancelled during execution - try to update status with fallback
                self._try_status_with_fallback(
                    conn,
                    run_id,
                    lambda c, rid: self._try_update_status(c, rid, "cancelled"),
                    "cancelled",
                )
                return

            # Pipeline failed - update to failed status
            error_message = str(pipeline_error)
            error_traceback = pipeline_traceback or traceback.format_exc()
            # Log to console for debugging
            print(f"[ERROR] Run {run_id} failed: {error_message}")
            print(f"[ERROR] Traceback:\n{error_traceback}")
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

        # Pipeline succeeded - completed
        self._try_status_with_fallback(
            conn,
            run_id,
            lambda c, rid: self._try_update_status(c, rid, "completed"),
            "completed",
        )

    def _try_update_status(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        status: str,
        error_message: str | None = None,
    ) -> bool:
        """Try to update run status with error handling and logging.

        This is the generic status update method that handles the common pattern
        of updating status, logging no-op cases, and catching exceptions.

        Args:
            conn: Database connection.
            run_id: Run ID to update.
            status: New status ('cancelled', 'completed', 'failed').
            error_message: Error message if status is 'failed' (optional).

        Returns:
            True if status was updated or already in terminal state (no fallback needed).
            False if failed with exception (fallback needed).
        """
        try:
            with transaction(conn):
                result = update_run_status_if_active(
                    conn, run_id, status, error_message
                )
            if result != RunUpdateResult.UPDATED:
                # Run was not updated - log appropriate message
                if result == RunUpdateResult.NOT_FOUND:
                    no_op_message = "run not found"
                else:  # ALREADY_TERMINAL
                    no_op_message = "run was already in terminal state"
                self._broadcast_log(
                    run_id,
                    {
                        "run_id": run_id,
                        "level": "info",
                        "message": f"{status.capitalize()} skipped: {no_op_message}",
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
                    "message": f"Failed to update run status to {status}: {e}",
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
            lambda c, rid: self._try_update_status(c, rid, "failed", error_message),
            "failed",
        )
