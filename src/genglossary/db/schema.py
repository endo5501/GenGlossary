"""Database schema initialization and migration."""

import sqlite3

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Execution history
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_path TEXT NOT NULL,
    llm_provider TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    error_message TEXT
);

-- Input documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    UNIQUE(run_id, file_path)
);

-- Extracted terms
CREATE TABLE IF NOT EXISTS terms_extracted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_text TEXT NOT NULL,
    category TEXT,
    UNIQUE(run_id, term_text)
);

-- Provisional glossary
CREATE TABLE IF NOT EXISTS glossary_provisional (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_name TEXT NOT NULL,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT NOT NULL,
    UNIQUE(run_id, term_name)
);

-- Review issues
CREATE TABLE IF NOT EXISTS glossary_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    should_exclude INTEGER DEFAULT 0,
    exclusion_reason TEXT
);

-- Refined glossary
CREATE TABLE IF NOT EXISTS glossary_refined (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_name TEXT NOT NULL,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT NOT NULL,
    UNIQUE(run_id, term_name)
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

    # Set schema version if not already set
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schema_version WHERE version = ?", (SCHEMA_VERSION,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))

    conn.commit()


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
