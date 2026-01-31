"""Repository for documents table CRUD operations."""

import sqlite3
from typing import cast


def create_document(
    conn: sqlite3.Connection, file_name: str, content: str, content_hash: str
) -> int:
    """Create a new document record.

    Args:
        conn: Database connection.
        file_name: Name of the document file.
        content: Content of the document.
        content_hash: Hash of the document content (for change detection).

    Returns:
        int: The ID of the created document.

    Raises:
        sqlite3.IntegrityError: If file_name already exists.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO documents (file_name, content, content_hash)
        VALUES (?, ?, ?)
        """,
        (file_name, content, content_hash),
    )
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


def get_document_by_name(
    conn: sqlite3.Connection, file_name: str
) -> sqlite3.Row | None:
    """Get a document by file_name.

    Args:
        conn: Database connection.
        file_name: The file name.

    Returns:
        sqlite3.Row | None: The document record if found, None otherwise.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM documents WHERE file_name = ?",
        (file_name,),
    )
    return cursor.fetchone()


def delete_document(conn: sqlite3.Connection, document_id: int) -> None:
    """Delete a document record.

    Args:
        conn: Database connection.
        document_id: The document ID to delete.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))


def delete_all_documents(conn: sqlite3.Connection) -> None:
    """Delete all documents.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents")


def create_documents_batch(
    conn: sqlite3.Connection,
    documents: list[tuple[str, str, str]],
) -> None:
    """Create multiple document records in a batch.

    Args:
        conn: Database connection.
        documents: List of tuples (file_name, content, content_hash).

    Raises:
        sqlite3.IntegrityError: If any file_name already exists.
    """
    if not documents:
        return

    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO documents (file_name, content, content_hash)
        VALUES (?, ?, ?)
        """,
        documents,
    )
