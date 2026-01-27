"""Repository for project statistics queries."""

import sqlite3


def count_documents(conn: sqlite3.Connection) -> int:
    """Count the number of documents in the database.

    Args:
        conn: Database connection.

    Returns:
        int: Number of documents.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    result = cursor.fetchone()
    return result[0] if result else 0


def count_provisional_terms(conn: sqlite3.Connection) -> int:
    """Count the number of provisional glossary terms.

    Args:
        conn: Database connection.

    Returns:
        int: Number of provisional terms.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM glossary_provisional")
    result = cursor.fetchone()
    return result[0] if result else 0


def count_issues(conn: sqlite3.Connection) -> int:
    """Count the number of glossary issues.

    Args:
        conn: Database connection.

    Returns:
        int: Number of issues.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM glossary_issues")
    result = cursor.fetchone()
    return result[0] if result else 0
