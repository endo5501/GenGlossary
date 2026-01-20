"""Repository for documents table CRUD operations."""

import sqlite3
from typing import cast


def create_document(
    conn: sqlite3.Connection, file_path: str, content_hash: str
) -> int:
    """Create a new document record.

    Args:
        conn: Database connection.
        file_path: Path to the document file.
        content_hash: Hash of the document content (for change detection).

    Returns:
        int: The ID of the created document.

    Raises:
        sqlite3.IntegrityError: If file_path already exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO documents (file_path, content_hash)
        VALUES (?, ?)
        """,
        (file_path, content_hash),
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


def list_all_documents(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """List all documents.

    Args:
        conn: Database connection.

    Returns:
        list[sqlite3.Row]: List of all document records ordered by id.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY id")
    return cursor.fetchall()


def get_document_by_path(
    conn: sqlite3.Connection, file_path: str
) -> sqlite3.Row | None:
    """Get a document by file_path.

    Args:
        conn: Database connection.
        file_path: The file path.

    Returns:
        sqlite3.Row | None: The document record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM documents WHERE file_path = ?",
        (file_path,),
    )
    return cursor.fetchone()
