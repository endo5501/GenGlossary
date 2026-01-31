"""Run manager for background pipeline execution."""

import sqlite3
import traceback
from datetime import datetime
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread

from genglossary.db.connection import database_connection, get_connection, transaction
from genglossary.db.runs_repository import (
    cancel_run,
    complete_run_if_not_cancelled,
    create_run,
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
        # Check if a run is already active
        with database_connection(self.db_path) as conn:
            active_run = get_active_run(conn)
            if active_run is not None:
                raise RuntimeError(f"Run already running: {active_run['id']}")

            # Create run record
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
            executor.execute(
                conn,
                scope,
                context,
                doc_root=self.doc_root,
            )

            # Check if cancelled first, then try atomic completion
            if cancel_event.is_set():
                with transaction(conn):
                    cancel_run(conn, run_id)
            else:
                # Use atomic update to prevent race condition:
                # If cancelled between is_set() check and this update,
                # complete_run_if_not_cancelled will detect it and return False
                with transaction(conn):
                    complete_run_if_not_cancelled(conn, run_id)

        except Exception as e:
            # Capture traceback for debugging
            error_traceback = traceback.format_exc()
            # Update status to failed
            self._update_failed_status(conn, run_id, str(e))
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "error",
                    "message": f"Run failed: {str(e)}",
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

    def _try_update_status(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        error_message: str,
    ) -> bool:
        """Try to update run status to failed, return True if successful."""
        try:
            with transaction(conn):
                update_run_status(
                    conn,
                    run_id,
                    "failed",
                    finished_at=datetime.now(),
                    error_message=error_message,
                )
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
        # Try primary connection
        if conn is not None and self._try_update_status(conn, run_id, error_message):
            return

        # Fallback to new connection
        try:
            with database_connection(self.db_path) as fallback_conn:
                self._try_update_status(fallback_conn, run_id, error_message)
        except Exception as e:
            # Both failed, status update is lost but error log will still be broadcast
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to create fallback connection: {e}",
                },
            )
