"""Database connection management."""

import sqlite3
from pathlib import Path


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

    # Create connection
    conn = sqlite3.connect(db_path)

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Set Row factory for dict-like access
    conn.row_factory = sqlite3.Row

    return conn
