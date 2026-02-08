"""Run manager for background pipeline execution."""

import logging
import sqlite3
import traceback
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread

logger = logging.getLogger(__name__)

from genglossary.config import Config
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
        # Track completed runs with their completion signals
        # Protected by _subscribers_lock
        self._completed_runs: dict[int, dict] = {}

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
            status_update_failed = False
            try:
                with database_connection(self.db_path) as conn:
                    with transaction(conn):
                        update_run_status(
                            conn, run_id, "failed",
                            error_message="Failed to start execution thread",
                            finished_at=datetime.now(timezone.utc),
                        )
            except Exception as db_error:
                status_update_failed = True
                logger.warning(
                    f"Failed to update run status after thread start failure: {db_error}"
                )
                self._broadcast_log(
                    run_id,
                    {
                        "run_id": run_id,
                        "level": "warning",
                        "message": f"Failed to update run status after thread start failure: {db_error}",
                    },
                )

            # Cleanup run resources (cancel event, completion signal, subscribers)
            self._cleanup_run_resources(
                run_id,
                db_status="failed",
                status_update_failed=status_update_failed,
            )

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

        # Track final status for completion signal
        final_status: str | None = None
        status_update_failed: bool = False

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
            config = Config()
            debug_dir = str(Path(self.db_path).parent / "llm-debug")
            executor = PipelineExecutor(
                provider=self.llm_provider,
                model=self.llm_model,
                base_url=self.llm_base_url or None,
                llm_debug=config.llm_debug,
                debug_dir=debug_dir,
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
            final_status, success = self._finalize_run_status(
                conn, run_id, pipeline_error, pipeline_traceback
            )
            status_update_failed = not success

        except Exception as e:
            # Connection errors or other errors outside pipeline execution
            error_message = str(e)
            error_traceback = traceback.format_exc()
            logger.error(
                f"Run {run_id} failed (outside pipeline): {error_message}\n"
                f"{error_traceback}"
            )
            success = self._try_update_status(conn, run_id, "failed", error_message)
            final_status = "failed"
            status_update_failed = not success
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
            self._cleanup_run_resources(
                run_id,
                db_status=final_status,
                status_update_failed=status_update_failed,
            )
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

        If the run has already completed, the completion signal is immediately
        enqueued so the subscriber doesn't miss it.

        Args:
            run_id: Run ID.

        Returns:
            Queue: ログメッセージを受信するためのQueue.
        """
        queue: Queue = Queue(maxsize=self.MAX_LOG_QUEUE_SIZE)
        with self._subscribers_lock:
            # Check if run has already completed
            if run_id in self._completed_runs:
                # Immediately send completion signal
                self._put_to_queue(queue, self._completed_runs[run_id])
            else:
                # Run still active, register for future messages
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

    def _cleanup_run_resources(
        self,
        run_id: int,
        db_status: str | None = None,
        status_update_failed: bool = False,
    ) -> None:
        """Cleanup resources associated with a run.

        This method consolidates the cleanup logic that was previously duplicated
        in start_run exception handler and _execute_run finally block.

        The cleanup includes:
        1. Removing the cancel event
        2. Broadcasting completion signal (with DB status if provided)
        3. Removing subscribers

        This method is idempotent - safe to call multiple times.

        Note: Broadcast and subscriber removal are done atomically under the same
        lock to prevent race conditions where a subscriber registers after broadcast
        but before removal, missing the completion signal.

        Args:
            run_id: Run ID to cleanup.
            db_status: Final DB status to include in completion signal.
            status_update_failed: True if DB status update failed.
        """
        with self._cancel_events_lock:
            self._cancel_events.pop(run_id, None)

        completion_signal: dict = {"run_id": run_id, "complete": True}
        if db_status is not None:
            completion_signal["db_status"] = db_status
        if status_update_failed:
            completion_signal["status_update_failed"] = True

        # Broadcast and remove subscribers atomically to prevent race condition
        # Also store completion signal for late subscribers
        with self._subscribers_lock:
            if run_id in self._subscribers:
                for queue in self._subscribers[run_id]:
                    self._put_to_queue(queue, completion_signal)
                del self._subscribers[run_id]
            # Store completion signal for subscribers that register after cleanup
            self._completed_runs[run_id] = completion_signal

    def _finalize_run_status(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        pipeline_error: Exception | None,
        pipeline_traceback: str | None = None,
    ) -> tuple[str, bool]:
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

        Returns:
            tuple[str, bool]: (target_status, update_succeeded)
                - target_status: 'cancelled', 'failed', or 'completed'
                - update_succeeded: True if DB was updated successfully
        """
        if pipeline_error is not None:
            # Check if it's a cancellation exception
            if isinstance(pipeline_error, PipelineCancelledException):
                success = self._try_update_status(conn, run_id, "cancelled")
                return ("cancelled", success)

            # Pipeline failed - update to failed status
            error_message = str(pipeline_error)
            error_traceback = pipeline_traceback or traceback.format_exc()
            logger.error(
                f"Run {run_id} failed: {error_message}\n{error_traceback}"
            )
            success = self._try_update_status(
                conn, run_id, "failed", error_message
            )
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "error",
                    "message": f"Run failed: {error_message}",
                    "traceback": error_traceback,
                },
            )
            return ("failed", success)

        # Pipeline succeeded - completed
        success = self._try_update_status(conn, run_id, "completed")
        return ("completed", success)

    def _try_update_status(
        self,
        conn: sqlite3.Connection | None,
        run_id: int,
        status: str,
        error_message: str | None = None,
    ) -> bool:
        """Try to update run status with fallback connection support.

        Attempts to update run status using the provided connection. If the
        connection is None or the update fails with an exception, falls back
        to a new connection via database_connection.

        Args:
            conn: Primary database connection (may be None or unusable).
            run_id: Run ID to update.
            status: New status ('cancelled', 'completed', 'failed').
            error_message: Error message if status is 'failed' (optional).

        Returns:
            True if status was updated, already terminal, or run not found
            (no fallback needed). False if both primary and fallback
            connections failed with exceptions.
        """
        if conn is not None:
            try:
                result = update_run_status_if_active(
                    conn, run_id, status, error_message
                )
                self._log_update_result(run_id, status, result)
                return True
            except Exception as e:
                logger.debug(
                    f"Primary connection failed for run {run_id} "
                    f"status update to {status}: {e}"
                )

        # Fallback to new connection
        try:
            with database_connection(self.db_path) as fallback_conn:
                result = update_run_status_if_active(
                    fallback_conn, run_id, status, error_message
                )
                self._log_update_result(run_id, status, result)
                return True
        except Exception as e:
            logger.warning(
                f"Failed to update {status} status for run {run_id}: {e}"
            )
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to update {status} status: {e}",
                },
            )

        return False

    def _log_update_result(
        self, run_id: int, status: str, result: RunUpdateResult
    ) -> None:
        """Log a message when status update was a no-op.

        Args:
            run_id: Run ID.
            status: Target status that was attempted.
            result: Result from update_run_status_if_active.
        """
        if result == RunUpdateResult.UPDATED:
            return
        if result == RunUpdateResult.NOT_FOUND:
            no_op_message = "run not found"
        elif result == RunUpdateResult.ALREADY_TERMINAL:
            no_op_message = "run was already in terminal state"
        else:
            no_op_message = f"unexpected result: {result.value}"
        self._broadcast_log(
            run_id,
            {
                "run_id": run_id,
                "level": "info",
                "message": f"{status.capitalize()} skipped: {no_op_message}",
            },
        )
