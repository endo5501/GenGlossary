"""Repository for runs table operations."""

import sqlite3
from datetime import datetime, timezone
from typing import Any


def create_run(
    conn: sqlite3.Connection,
    scope: str,
    triggered_by: str = "api",
) -> int:
    """Create a new run.

    Args:
        conn: Project database connection.
        scope: Run scope ('full', 'from_terms', 'provisional_to_refined').
        triggered_by: Source that triggered the run (default: 'api').

    Returns:
        int: The ID of the newly created run.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO runs (scope, triggered_by)
        VALUES (?, ?)
        """,
        (scope, triggered_by),
    )

    run_id = cursor.lastrowid
    if run_id is None:
        raise RuntimeError("Failed to create run: lastrowid is None")

    return run_id


def get_run(conn: sqlite3.Connection, run_id: int) -> sqlite3.Row | None:
    """Get a run by ID.

    Args:
        conn: Project database connection.
        run_id: Run ID.

    Returns:
        sqlite3.Row if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    return cursor.fetchone()


def get_active_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Get the most recent active run (pending or running).

    Args:
        conn: Project database connection.

    Returns:
        sqlite3.Row if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM runs
        WHERE status IN ('pending', 'running')
        ORDER BY created_at DESC
        LIMIT 1
        """,
    )
    return cursor.fetchone()


def list_runs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """List all runs ordered by created_at descending.

    Args:
        conn: Project database connection.

    Returns:
        List of sqlite3.Row instances, most recent first.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM runs ORDER BY created_at DESC")
    return cursor.fetchall()


def update_run_status(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    error_message: str | None = None,
) -> None:
    """Update run status and timestamps.

    Args:
        conn: Project database connection.
        run_id: Run ID to update.
        status: New status ('pending', 'running', 'completed', 'failed', 'cancelled').
        started_at: Started timestamp (optional).
        finished_at: Finished timestamp (optional).
        error_message: Error message if failed (optional).
    """
    updates = ["status = ?"]
    values: list[Any] = [status]

    if started_at is not None:
        updates.append("started_at = ?")
        values.append(started_at.isoformat(timespec="seconds"))

    if finished_at is not None:
        updates.append("finished_at = ?")
        values.append(finished_at.isoformat(timespec="seconds"))

    if error_message is not None:
        updates.append("error_message = ?")
        values.append(error_message)

    query = f"UPDATE runs SET {', '.join(updates)} WHERE id = ?"
    values.append(run_id)

    cursor = conn.cursor()
    cursor.execute(query, values)


def update_run_progress(
    conn: sqlite3.Connection,
    run_id: int,
    current: int,
    total: int,
    current_step: str,
) -> None:
    """Update run progress information.

    Args:
        conn: Project database connection.
        run_id: Run ID to update.
        current: Current progress value.
        total: Total progress value.
        current_step: Current step name ('terms', 'provisional', 'issues', 'refined').
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET progress_current = ?,
            progress_total = ?,
            current_step = ?
        WHERE id = ?
        """,
        (current, total, current_step, run_id),
    )


def update_run_status_if_active(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    error_message: str | None = None,
) -> int:
    """Update run status only if run is active (pending or running).

    This function atomically checks the run status before updating,
    preventing race conditions and avoiding overwriting terminal states.

    Args:
        conn: Project database connection.
        run_id: Run ID to update.
        status: New status ('completed', 'cancelled', 'failed').
        error_message: Error message if status is 'failed' (optional).

    Returns:
        Number of rows updated (0 if run was already in terminal state or not found).
    """
    finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET status = ?,
            finished_at = ?,
            error_message = ?
        WHERE id = ? AND status IN ('pending', 'running')
        """,
        (status, finished_at, error_message, run_id),
    )
    return cursor.rowcount


def cancel_run(conn: sqlite3.Connection, run_id: int) -> int:
    """Cancel a run.

    Sets status to 'cancelled' and sets finished_at to now.

    Args:
        conn: Project database connection.
        run_id: Run ID to cancel.

    Returns:
        Number of rows updated (0 if run was already in terminal state or not found).
    """
    return update_run_status_if_active(conn, run_id, "cancelled")


def complete_run_if_not_cancelled(conn: sqlite3.Connection, run_id: int) -> bool:
    """Complete a run only if it is still running.

    This function atomically checks the run status before updating
    to completed, preventing race conditions between cancellation
    and completion. It also avoids overwriting other terminal states
    like 'failed' or 'completed'.

    Args:
        conn: Project database connection.
        run_id: Run ID to complete.

    Returns:
        bool: True if the run was updated to completed, False if already
              in a terminal state or not found.
    """
    return update_run_status_if_active(conn, run_id, "completed") > 0


def fail_run_if_not_terminal(
    conn: sqlite3.Connection, run_id: int, error_message: str
) -> bool:
    """Fail a run only if it is not already in a terminal state.

    This function atomically checks the run status before updating
    to failed, preventing race conditions and avoiding overwriting
    terminal states like 'cancelled', 'completed', or 'failed'.

    Args:
        conn: Project database connection.
        run_id: Run ID to fail.
        error_message: Error message to store.

    Returns:
        bool: True if the run was updated to failed, False if already
              in a terminal state or not found.
    """
    return update_run_status_if_active(conn, run_id, "failed", error_message) > 0
