"""Repository for runs table operations."""

import sqlite3
from datetime import datetime, timezone
from typing import Any

VALID_STATUSES = {"pending", "running", "completed", "failed", "cancelled"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def _validate_status(status: str, allowed: set[str] | None = None) -> None:
    """Validate status value.

    Args:
        status: Status value to validate.
        allowed: Set of allowed status values. Defaults to VALID_STATUSES.

    Raises:
        ValueError: If status is not in the allowed set.
    """
    allowed = allowed or VALID_STATUSES
    if status not in allowed:
        raise ValueError(f"Invalid status: {status}. Must be one of {allowed}")


def create_run(
    conn: sqlite3.Connection,
    scope: str,
    triggered_by: str = "api",
) -> int:
    """Create a new run.

    Args:
        conn: Project database connection.
        scope: Run scope ('full', 'extract', 'generate', 'review', 'refine').
        triggered_by: Source that triggered the run (default: 'api').

    Returns:
        int: The ID of the newly created run.
    """
    created_at = _current_utc_iso()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO runs (scope, triggered_by, created_at)
        VALUES (?, ?, ?)
        """,
        (scope, triggered_by, created_at),
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
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
    )
    return cursor.fetchone()


def get_current_or_latest_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Get the active run if exists, otherwise the latest run.

    This function first looks for an active run (pending or running).
    If no active run exists, it returns the most recent run regardless of status.
    This is useful for the /current endpoint to show completed runs.

    Args:
        conn: Project database connection.

    Returns:
        sqlite3.Row if found, None otherwise.
    """
    # First, try to get an active run
    active = get_active_run(conn)
    if active is not None:
        return active

    # No active run, return the most recent run
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM runs
        ORDER BY created_at DESC, id DESC
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


def _validate_timezone_aware(dt: datetime, param_name: str) -> None:
    """Validate that a datetime is timezone-aware.

    Args:
        dt: Datetime to validate.
        param_name: Parameter name for error message.

    Raises:
        ValueError: If datetime is naive (no timezone info).
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f"{param_name} must be timezone-aware")


def _to_iso_string(dt: datetime | None, param_name: str) -> str | None:
    """Convert timezone-aware datetime to ISO string.

    Args:
        dt: Datetime to convert (must be timezone-aware if not None).
        param_name: Parameter name for error message.

    Returns:
        ISO 8601 formatted string with second precision, or None if dt is None.

    Raises:
        ValueError: If dt is naive (no timezone info).
    """
    if dt is None:
        return None
    _validate_timezone_aware(dt, param_name)
    return dt.isoformat(timespec="seconds")


def _current_utc_iso() -> str:
    """Get current UTC time as ISO string.

    Returns:
        Current UTC time as ISO 8601 formatted string with second precision.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
        started_at: Started timestamp (optional, must be timezone-aware).
        finished_at: Finished timestamp (optional, must be timezone-aware).
        error_message: Error message if failed (optional).

    Raises:
        ValueError: If status is invalid, or started_at/finished_at is naive.
    """
    _validate_status(status)

    updates = ["status = ?"]
    values: list[Any] = [status]

    started_at_str = _to_iso_string(started_at, "started_at")
    if started_at_str is not None:
        updates.append("started_at = ?")
        values.append(started_at_str)

    finished_at_str = _to_iso_string(finished_at, "finished_at")
    if finished_at_str is not None:
        updates.append("finished_at = ?")
        values.append(finished_at_str)

    # Clear error_message on non-terminal status transition
    if status not in TERMINAL_STATUSES:
        updates.append("error_message = ?")
        values.append(None)
    elif error_message is not None:
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
        current_step: Current step name ('extract', 'provisional', 'issues', 'refined').
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
    conn.commit()  # Commit immediately for real-time UI updates


def update_run_status_if_active(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    error_message: str | None = None,
    finished_at: datetime | None = None,
) -> int:
    """Update run status only if run is active (pending or running).

    This function atomically checks the run status before updating,
    preventing race conditions and avoiding overwriting terminal states.

    Args:
        conn: Project database connection.
        run_id: Run ID to update.
        status: New terminal status ('completed', 'cancelled', 'failed').
        error_message: Error message if status is 'failed' (optional).
        finished_at: Finished timestamp (optional, must be timezone-aware).
            If not provided, uses current UTC time.

    Returns:
        Number of rows updated (0 if run was already in terminal state or not found).

    Raises:
        ValueError: If status is not terminal, or finished_at is naive.
    """
    _validate_status(status, TERMINAL_STATUSES)

    finished_at_str = _to_iso_string(finished_at, "finished_at")
    if finished_at_str is None:
        finished_at_str = _current_utc_iso()

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET status = ?,
            finished_at = ?,
            error_message = ?
        WHERE id = ? AND status IN ('pending', 'running')
        """,
        (status, finished_at_str, error_message, run_id),
    )
    rowcount = cursor.rowcount
    if rowcount > 0:
        conn.commit()  # Commit immediately for real-time UI updates
    return rowcount


def update_run_status_if_running(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    finished_at: datetime | None = None,
) -> int:
    """Update run status only if run is currently running.

    Unlike update_run_status_if_active, this function only updates
    runs in 'running' state, not 'pending'. This ensures that a run
    cannot transition to 'completed' without first being started.

    This function always sets finished_at, making it suitable for
    terminal state transitions. Currently used by complete_run_if_not_cancelled.

    Args:
        conn: Project database connection.
        run_id: Run ID to update.
        status: New terminal status ('completed', 'failed', 'cancelled').
        finished_at: Finished timestamp (optional, must be timezone-aware).
            If not provided, uses current UTC time.

    Returns:
        Number of rows updated (0 if run is not running or not found).

    Raises:
        ValueError: If status is not terminal, or finished_at is naive.
    """
    _validate_status(status, TERMINAL_STATUSES)

    finished_at_str = _to_iso_string(finished_at, "finished_at")
    if finished_at_str is None:
        finished_at_str = _current_utc_iso()

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET status = ?,
            finished_at = ?
        WHERE id = ? AND status = 'running'
        """,
        (status, finished_at_str, run_id),
    )
    rowcount = cursor.rowcount
    if rowcount > 0:
        conn.commit()  # Commit immediately for real-time UI updates
    return rowcount


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
    """Complete a run only if it is currently running.

    This function atomically checks the run status before updating
    to completed, preventing race conditions between cancellation
    and completion. It also avoids overwriting other terminal states
    like 'failed' or 'completed'.

    Runs in 'pending' state cannot be completed directly - they must
    first transition to 'running' state.

    Args:
        conn: Project database connection.
        run_id: Run ID to complete.

    Returns:
        bool: True if the run was updated to completed, False if not
              running, already in a terminal state, or not found.
    """
    return update_run_status_if_running(conn, run_id, "completed") > 0


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
