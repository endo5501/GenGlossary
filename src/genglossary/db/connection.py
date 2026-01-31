"""Database connection management."""

import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a SQLite database connection.

    Creates parent directories if they don't exist.
    Enables foreign key constraints and Row factory.

    Args:
        db_path: Path to database file or ":memory:" for in-memory database.

    Returns:
        sqlite3.Connection: Database connection with foreign keys enabled
            and Row factory configured.
    """
    # Create parent directories if needed (except for in-memory db)
    if db_path != ":memory:":
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    # Create connection (check_same_thread=False for FastAPI async support)
    conn = sqlite3.connect(db_path, check_same_thread=False)

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Set Row factory for dict-like access
    conn.row_factory = sqlite3.Row

    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """Context manager for database transactions with nested transaction support.

    Supports nested transactions using SQLite SAVEPOINT mechanism.
    - Top-level transaction: Uses COMMIT/ROLLBACK
    - Nested transaction: Uses SAVEPOINT/RELEASE/ROLLBACK TO

    On successful completion, commits the transaction (or releases savepoint).
    On exception, rolls back changes (or rolls back to savepoint).

    Args:
        conn: Database connection to manage transaction for.

    Yields:
        None

    Raises:
        Exception: Re-raises any exception that occurs within the transaction.

    Example:
        with transaction(conn):
            create_document(conn, path, content, hash)
            with transaction(conn):  # Nested - uses SAVEPOINT
                create_term(conn, "term1", "category")
            # Both operations committed together, or rolled back on error
    """
    if conn.in_transaction:
        # Nested transaction - use SAVEPOINT
        savepoint_name = f"sp_{uuid.uuid4().hex[:8]}"
        conn.execute(f"SAVEPOINT {savepoint_name}")

        def release_savepoint() -> None:
            conn.execute(f"RELEASE {savepoint_name}")

        def rollback_savepoint() -> None:
            # ROLLBACK TO undoes changes but keeps savepoint active
            # RELEASE removes the savepoint from the stack
            conn.execute(f"ROLLBACK TO {savepoint_name}")
            conn.execute(f"RELEASE {savepoint_name}")

        commit_fn = release_savepoint
        rollback_fn = rollback_savepoint
    else:
        # Top-level transaction
        commit_fn = conn.commit
        rollback_fn = conn.rollback

    try:
        yield
        commit_fn()
    except Exception:
        rollback_fn()
        raise


@contextmanager
def database_connection(db_path: str) -> Iterator[sqlite3.Connection]:
    """Context manager for database connections.

    Ensures connections are properly closed even if exceptions occur.

    Args:
        db_path: Path to database file or ":memory:" for in-memory database.

    Yields:
        sqlite3.Connection: Database connection.

    Example:
        with database_connection("./db.sqlite") as conn:
            run = get_run(conn, 1)
    """
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()
