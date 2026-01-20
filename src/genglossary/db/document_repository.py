"""Repository for documents table CRUD operations."""

import sqlite3
from typing import cast


def create_document(
    conn: sqlite3.Connection, run_id: int, file_path: str, content_hash: str
) -> int:
    """Create a new document record.

    Args:
        conn: Database connection.
        run_id: The run ID this document belongs to.
        file_path: Path to the document file.
        content_hash: Hash of the document content (for change detection).

    Returns:
        int: The ID of the created document.

    Raises:
        sqlite3.IntegrityError: If (run_id, file_path) already exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO documents (run_id, file_path, content_hash)
        VALUES (?, ?, ?)
        """,
        (run_id, file_path, content_hash),
    )
    conn.commit()
    # lastrowid is guaranteed to be non-None after INSERT
    return cast(int, cursor.lastrowid)


def get_document(conn: sqlite3.Connection, document_id: int) -> sqlite3.Row | None:
    """Get a document by ID.

    Args:
        conn: Database connection.
        document_id: The document ID to retrieve.

    Returns:
        sqlite3.Row | None: The document record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
    return cursor.fetchone()


def list_documents_by_run(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    """List all documents for a specific run.

    Args:
        conn: Database connection.
        run_id: The run ID to filter by.

    Returns:
        list[sqlite3.Row]: List of document records for the specified run.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM documents WHERE run_id = ? ORDER BY id",
        (run_id,),
    )
    return cursor.fetchall()


def get_document_by_path(
    conn: sqlite3.Connection, run_id: int, file_path: str
) -> sqlite3.Row | None:
    """Get a document by run_id and file_path.

    Args:
        conn: Database connection.
        run_id: The run ID.
        file_path: The file path.

    Returns:
        sqlite3.Row | None: The document record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM documents WHERE run_id = ? AND file_path = ?",
        (run_id, file_path),
    )
    return cursor.fetchone()
