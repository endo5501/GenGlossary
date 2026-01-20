"""Repository for metadata table operations."""

import sqlite3


def get_metadata(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Get global metadata.

    Args:
        conn: Database connection.

    Returns:
        Metadata row if exists, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metadata WHERE id = 1")
    return cursor.fetchone()


def upsert_metadata(
    conn: sqlite3.Connection, llm_provider: str, llm_model: str
) -> None:
    """Insert or update global metadata.

    Uses SQLite's ON CONFLICT clause to perform upsert operation.
    The created_at timestamp is preserved when updating.

    Args:
        conn: Database connection.
        llm_provider: LLM provider name (e.g., "ollama", "openai").
        llm_model: LLM model name (e.g., "llama3.2", "gpt-4").
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO metadata (id, llm_provider, llm_model)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            llm_provider = excluded.llm_provider,
            llm_model = excluded.llm_model
        """,
        (llm_provider, llm_model),
    )
    conn.commit()


def clear_metadata(conn: sqlite3.Connection) -> None:
    """Delete metadata record.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM metadata WHERE id = 1")
    conn.commit()
