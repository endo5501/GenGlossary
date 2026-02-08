"""Database schema initialization and migration."""

import sqlite3

SCHEMA_VERSION = 9

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

-- Input documents (v4: file_path → file_name, added content column)
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Extracted terms (v7: user_notes column added)
CREATE TABLE IF NOT EXISTS terms_extracted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_text TEXT NOT NULL UNIQUE,
    category TEXT,
    user_notes TEXT NOT NULL DEFAULT '',
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

-- Review issues (v9: should_exclude, exclusion_reason columns added)
CREATE TABLE IF NOT EXISTS glossary_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    should_exclude INTEGER NOT NULL DEFAULT 0,
    exclusion_reason TEXT,
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

-- Excluded terms (v5: terms to skip during extraction)
CREATE TABLE IF NOT EXISTS terms_excluded (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_text TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Required terms (v6: terms to always include during extraction)
CREATE TABLE IF NOT EXISTS terms_required (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_text TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Synonym groups (v8: link related terms)
CREATE TABLE IF NOT EXISTS term_synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_term_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Synonym group members (v8: each term belongs to at most one group)
CREATE TABLE IF NOT EXISTS term_synonym_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES term_synonym_groups(id) ON DELETE CASCADE,
    term_text TEXT NOT NULL UNIQUE,
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
    created_at TEXT NOT NULL  -- Set by Python, not SQLite default
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
    _migrate_documents_table_v4(conn)
    _migrate_terms_user_notes_v7(conn)
    _migrate_synonym_tables_v8(conn)
    _migrate_issues_exclude_columns_v9(conn)

    # Set schema version if not already set (INSERT OR IGNORE handles race conditions)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,)
    )

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


def _migrate_documents_table_v4(conn: sqlite3.Connection) -> None:
    """Migrate documents table from v3 to v4.

    Changes:
    - file_path → file_name (rename column)
    - Add content column

    For existing data, content is set to empty string (migration requires re-upload).
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(documents)")
    columns = {row[1] for row in cursor.fetchall()}

    # Check if migration is needed (file_path exists but file_name doesn't)
    if "file_path" in columns and "file_name" not in columns:
        # SQLite doesn't support RENAME COLUMN in older versions,
        # so we recreate the table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        # Migrate existing data (extract filename from path, content is empty)
        cursor.execute(
            """
            INSERT INTO documents_new (id, file_name, content, content_hash, created_at)
            SELECT id,
                   CASE
                       WHEN instr(file_path, '/') > 0
                       THEN substr(file_path, length(file_path) - length(replace(file_path, '/', '')) + 1)
                       ELSE file_path
                   END,
                   '',
                   content_hash,
                   created_at
            FROM documents
            """
        )

        # Drop old table and rename new one
        cursor.execute("DROP TABLE documents")
        cursor.execute("ALTER TABLE documents_new RENAME TO documents")


def _migrate_terms_user_notes_v7(conn: sqlite3.Connection) -> None:
    """Migrate terms_extracted table to v7: add user_notes column."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(terms_extracted)")
    columns = {row[1] for row in cursor.fetchall()}
    if "user_notes" not in columns:
        cursor.execute(
            "ALTER TABLE terms_extracted ADD COLUMN user_notes TEXT NOT NULL DEFAULT ''"
        )


def _migrate_synonym_tables_v8(conn: sqlite3.Connection) -> None:
    """Migrate to v8: add synonym group tables if they don't exist."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='term_synonym_groups'"
    )
    if cursor.fetchone() is None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS term_synonym_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_term_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS term_synonym_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL REFERENCES term_synonym_groups(id) ON DELETE CASCADE,
                term_text TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def _migrate_issues_exclude_columns_v9(conn: sqlite3.Connection) -> None:
    """Migrate to v9: add should_exclude and exclusion_reason to glossary_issues."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(glossary_issues)")
    columns = {row[1] for row in cursor.fetchall()}
    if "should_exclude" not in columns:
        cursor.execute(
            "ALTER TABLE glossary_issues ADD COLUMN should_exclude INTEGER NOT NULL DEFAULT 0"
        )
    if "exclusion_reason" not in columns:
        cursor.execute(
            "ALTER TABLE glossary_issues ADD COLUMN exclusion_reason TEXT"
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
