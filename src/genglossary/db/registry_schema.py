"""Registry database schema initialization and migration."""

import sqlite3

REGISTRY_SCHEMA_VERSION = 2

REGISTRY_SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Projects registry
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    doc_root TEXT NOT NULL,
    db_path TEXT NOT NULL UNIQUE,
    llm_provider TEXT NOT NULL DEFAULT 'ollama',
    llm_model TEXT NOT NULL DEFAULT '',
    llm_base_url TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_run_at TEXT,
    status TEXT NOT NULL DEFAULT 'created'
);
"""


def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Migrate from schema version 1 to 2.

    Adds llm_base_url column to projects table.

    Args:
        conn: SQLite registry database connection.
    """
    conn.execute(
        "ALTER TABLE projects ADD COLUMN llm_base_url TEXT NOT NULL DEFAULT ''"
    )


def initialize_registry(conn: sqlite3.Connection) -> None:
    """Initialize registry database schema.

    Creates all required tables and sets schema version.
    This function is idempotent - it can be called multiple times safely.
    Handles migrations from older schema versions.

    Args:
        conn: SQLite registry database connection.
    """
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Check if this is a fresh database or needs migration
    current_version = get_registry_schema_version(conn)

    if current_version == 0:
        # Fresh database - create with latest schema
        conn.executescript(REGISTRY_SCHEMA_SQL)
    else:
        # Existing database - apply migrations as needed
        if current_version < 2:
            migrate_v1_to_v2(conn)

    # Set schema version if not already set
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version = ?",
        (REGISTRY_SCHEMA_VERSION,),
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (REGISTRY_SCHEMA_VERSION,),
        )

    conn.commit()


def get_registry_schema_version(conn: sqlite3.Connection) -> int:
    """Get current registry schema version.

    Args:
        conn: SQLite registry database connection.

    Returns:
        int: Current schema version, or 0 if schema_version table doesn't exist.
    """
    cursor = conn.cursor()

    # Check if schema_version table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cursor.fetchone() is None:
        return 0

    # Get the latest version
    cursor.execute("SELECT MAX(version) FROM schema_version")
    result = cursor.fetchone()[0]
    return result if result is not None else 0
