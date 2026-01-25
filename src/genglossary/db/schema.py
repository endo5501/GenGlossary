"""Database schema initialization and migration."""

import sqlite3

SCHEMA_VERSION = 3

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Global metadata (single row, id=1 only)
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    input_path TEXT NOT NULL DEFAULT '',
    llm_provider TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Input documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Extracted terms
CREATE TABLE IF NOT EXISTS terms_extracted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_text TEXT NOT NULL UNIQUE,
    category TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Provisional glossary
CREATE TABLE IF NOT EXISTS glossary_provisional (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_name TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Review issues
CREATE TABLE IF NOT EXISTS glossary_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Refined glossary
CREATE TABLE IF NOT EXISTS glossary_refined (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_name TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Run history
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT,
    finished_at TEXT,
    triggered_by TEXT NOT NULL DEFAULT 'api',
    error_message TEXT,
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 0,
    current_step TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def initialize_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema.

    Creates all required tables and sets schema version.
    This function is idempotent - it can be called multiple times safely.

    Args:
        conn: SQLite database connection.
    """
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Execute schema creation
    conn.executescript(SCHEMA_SQL)

    _ensure_metadata_input_path(conn)

    # Set schema version if not already set
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schema_version WHERE version = ?", (SCHEMA_VERSION,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))

    conn.commit()


def _ensure_metadata_input_path(conn: sqlite3.Connection) -> None:
    """Ensure metadata table has input_path column."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(metadata)")
    columns = {row[1] for row in cursor.fetchall()}
    if "input_path" not in columns:
        cursor.execute(
            "ALTER TABLE metadata ADD COLUMN input_path TEXT NOT NULL DEFAULT ''"
        )


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get current schema version.

    Args:
        conn: SQLite database connection.

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
