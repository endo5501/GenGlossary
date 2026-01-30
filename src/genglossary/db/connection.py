"""Database connection management."""

import sqlite3
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
    """Context manager for database transactions.

    Commits the transaction on successful completion, or rolls back
    if an exception occurs.

    Args:
        conn: Database connection to manage transaction for.

    Yields:
        None

    Raises:
        Exception: Re-raises any exception that occurs within the transaction.

    Example:
        with transaction(conn):
            create_document(conn, path, content, hash)
            create_term(conn, "term1", "category")
            # Both operations committed together, or rolled back on error
    """
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
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
