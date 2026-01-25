"""Run manager for background pipeline execution."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from queue import Queue
from threading import Event, Thread

from genglossary.db.connection import get_connection
from genglossary.db.runs_repository import (
    cancel_run,
    create_run,
    get_active_run,
    get_run,
    update_run_status,
)
from genglossary.runs.executor import PipelineExecutor


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
        self._cancel_event = Event()
        self._log_queue: Queue = Queue(maxsize=self.MAX_LOG_QUEUE_SIZE)
        self._current_run_id: int | None = None

    @contextmanager
    def _db_connection(self):
        """Provide a database connection with automatic cleanup.

        Yields:
            sqlite3.Connection: Database connection.
        """
        conn = get_connection(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

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
        with self._db_connection() as conn:
            active_run = get_active_run(conn)
            if active_run is not None:
                raise RuntimeError(f"Run already running: {active_run['id']}")

            # Create run record
            run_id = create_run(conn, scope=scope, triggered_by=triggered_by)

        self._current_run_id = run_id

        # Clear previous cancel event
        self._cancel_event.clear()

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
        # Create a new connection for this thread
        conn = get_connection(self.db_path)

        try:
            # Update status to running
            update_run_status(
                conn, run_id, "running", started_at=datetime.now()
            )

            # Execute pipeline with project settings
            executor = PipelineExecutor(
                provider=self.llm_provider,
                model=self.llm_model,
            )
            executor.execute(
                conn,
                scope,
                self._cancel_event,
                self._log_queue,
                doc_root=self.doc_root,
                run_id=run_id,
            )

            # Check if cancelled
            if self._cancel_event.is_set():
                cancel_run(conn, run_id)
            else:
                # Update status to completed
                update_run_status(
                    conn, run_id, "completed", finished_at=datetime.now()
                )

        except Exception as e:
            # Update status to failed
            update_run_status(
                conn,
                run_id,
                "failed",
                finished_at=datetime.now(),
                error_message=str(e),
            )
            self._log_queue.put({"run_id": run_id, "level": "error", "message": f"Run failed: {str(e)}"})
        finally:
            # Send completion signal to close SSE stream
            self._log_queue.put({"run_id": run_id, "complete": True})
            # Close the connection when thread completes
            conn.close()

    def cancel_run(self, run_id: int) -> None:
        """Cancel a running run.

        Args:
            run_id: Run ID to cancel.
        """
        # Set cancellation event
        self._cancel_event.set()

        # Update database status
        with self._db_connection() as conn:
            cancel_run(conn, run_id)

    def get_active_run(self) -> sqlite3.Row | None:
        """Get the currently active run.

        Returns:
            sqlite3.Row if found, None otherwise.
        """
        with self._db_connection() as conn:
            return get_active_run(conn)

    def get_run(self, run_id: int) -> sqlite3.Row | None:
        """Get run details by ID.

        Args:
            run_id: Run ID.

        Returns:
            sqlite3.Row if found, None otherwise.
        """
        with self._db_connection() as conn:
            return get_run(conn, run_id)

    def get_log_queue(self) -> Queue:
        """Get the log queue for streaming logs.

        Returns:
            Queue: The log queue.
        """
        return self._log_queue
