"""Pytest fixtures for database tests."""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide an in-memory SQLite database connection for testing.

    Yields:
        sqlite3.Connection: An in-memory database connection.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database file path.

    Args:
        tmp_path: Pytest's temporary directory fixture.

    Returns:
        Path: Path to a temporary database file.
    """
    return tmp_path / "test_genglossary.db"
