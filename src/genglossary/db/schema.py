"""Database schema initialization and migration."""

import sqlite3

SCHEMA_VERSION = 2

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Global metadata (single row, id=1 only)
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
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
