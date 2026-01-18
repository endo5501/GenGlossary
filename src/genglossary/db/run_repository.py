"""Repository for runs table CRUD operations."""

import sqlite3
from typing import cast


def create_run(
    conn: sqlite3.Connection, input_path: str, llm_provider: str, llm_model: str
) -> int:
    """Create a new run record.

    Args:
        conn: Database connection.
        input_path: Path to the input document.
        llm_provider: LLM provider name (e.g., "ollama", "openai").
        llm_model: LLM model name (e.g., "llama3.2", "gpt-4").

    Returns:
        int: The ID of the created run.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO runs (input_path, llm_provider, llm_model)
        VALUES (?, ?, ?)
        """,
        (input_path, llm_provider, llm_model),
    )
    conn.commit()
    # lastrowid is guaranteed to be non-None after INSERT
    return cast(int, cursor.lastrowid)


def get_run(conn: sqlite3.Connection, run_id: int) -> sqlite3.Row | None:
    """Get a run by ID.

    Args:
        conn: Database connection.
        run_id: The run ID to retrieve.

    Returns:
        sqlite3.Row | None: The run record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    return cursor.fetchone()


def update_run_status(conn: sqlite3.Connection, run_id: int, status: str) -> None:
    """Update the status of a run.

    Args:
        conn: Database connection.
        run_id: The run ID to update.
        status: New status value (e.g., "running", "completed", "failed").
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE runs SET status = ? WHERE id = ?",
        (status, run_id),
    )
    conn.commit()


def complete_run(conn: sqlite3.Connection, run_id: int) -> None:
    """Mark a run as completed.

    Sets status to 'completed' and sets completed_at timestamp.

    Args:
        conn: Database connection.
        run_id: The run ID to complete.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET status = 'completed', completed_at = datetime('now')
        WHERE id = ?
        """,
        (run_id,),
    )
    conn.commit()


def fail_run(conn: sqlite3.Connection, run_id: int, error_message: str) -> None:
    """Mark a run as failed.

    Sets status to 'failed', sets completed_at timestamp, and stores error message.

    Args:
        conn: Database connection.
        run_id: The run ID to mark as failed.
        error_message: The error message to store.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET status = 'failed', completed_at = datetime('now'), error_message = ?
        WHERE id = ?
        """,
        (error_message, run_id),
    )
    conn.commit()


def list_runs(conn: sqlite3.Connection, limit: int | None = None) -> list[sqlite3.Row]:
    """List all runs, ordered by ID descending (most recent first).

    Args:
        conn: Database connection.
        limit: Maximum number of runs to return. None for all runs.

    Returns:
        list[sqlite3.Row]: List of run records.
    """
    cursor = conn.cursor()

    if limit is not None:
        cursor.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
    else:
        cursor.execute("SELECT * FROM runs ORDER BY id DESC")

    return cursor.fetchall()


def get_latest_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Get the most recent run.

    Args:
        conn: Database connection.

    Returns:
        sqlite3.Row | None: The most recent run record if exists, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1")
    return cursor.fetchone()
