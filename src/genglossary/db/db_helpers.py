"""Common database helper functions."""

import sqlite3
from collections.abc import Sequence


def batch_insert(
    conn: sqlite3.Connection,
    table_name: str,
    columns: list[str],
    data: Sequence[tuple],
) -> None:
    """Insert multiple rows into a table in a single batch operation.

    Args:
        conn: Database connection.
        table_name: Name of the table to insert into.
        columns: List of column names to insert.
        data: Sequence of tuples containing the values to insert.

    Raises:
        sqlite3.IntegrityError: If any constraint is violated.
    """
    if not data:
        return

    placeholders = ", ".join("?" * len(columns))
    columns_str = ", ".join(columns)
    cursor = conn.cursor()
    cursor.executemany(
        f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
        data,
    )
