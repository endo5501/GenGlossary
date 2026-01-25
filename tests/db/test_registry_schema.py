"""Tests for registry schema initialization."""

import sqlite3

import pytest

from genglossary.db.registry_connection import get_registry_connection
from genglossary.db.registry_schema import (
    REGISTRY_SCHEMA_VERSION,
    get_registry_schema_version,
    initialize_registry,
)


@pytest.fixture
def registry_conn() -> sqlite3.Connection:
    """Create an in-memory registry database connection for testing."""
    connection = get_registry_connection(":memory:")
    yield connection
    connection.close()


class TestInitializeRegistry:
    """Tests for initialize_registry function."""

    def test_initialize_registry_creates_tables(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """初期化でprojectsテーブルが作成される"""
        initialize_registry(registry_conn)

        cursor = registry_conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "projects"

    def test_initialize_registry_creates_schema_version_table(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """初期化でschema_versionテーブルが作成される"""
        initialize_registry(registry_conn)

        cursor = registry_conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "schema_version"

    def test_initialize_registry_sets_schema_version(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """初期化でスキーマバージョンが設定される"""
        initialize_registry(registry_conn)

        version = get_registry_schema_version(registry_conn)
        assert version == REGISTRY_SCHEMA_VERSION

    def test_initialize_registry_is_idempotent(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """複数回呼び出しても安全"""
        initialize_registry(registry_conn)
        initialize_registry(registry_conn)
        initialize_registry(registry_conn)

        # Should not raise any errors
        cursor = registry_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        assert cursor.fetchone()[0] == 0

    def test_projects_table_has_correct_columns(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """projectsテーブルが正しいカラムを持つ"""
        initialize_registry(registry_conn)

        cursor = registry_conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "name": "TEXT",
            "doc_root": "TEXT",
            "db_path": "TEXT",
            "llm_provider": "TEXT",
            "llm_model": "TEXT",
            "created_at": "TEXT",
            "updated_at": "TEXT",
            "last_run_at": "TEXT",
            "status": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns
            assert columns[col_name] == col_type

    def test_projects_table_has_unique_constraint_on_name(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """projectsテーブルのnameカラムにUNIQUE制約がある"""
        initialize_registry(registry_conn)

        cursor = registry_conn.cursor()

        # Insert first project
        cursor.execute(
            "INSERT INTO projects (name, doc_root, db_path) VALUES (?, ?, ?)",
            ("test-project", "/docs", "/test.db"),
        )

        # Try to insert duplicate name
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO projects (name, doc_root, db_path) VALUES (?, ?, ?)",
                ("test-project", "/docs2", "/test2.db"),
            )

    def test_projects_table_has_unique_constraint_on_db_path(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """projectsテーブルのdb_pathカラムにUNIQUE制約がある"""
        initialize_registry(registry_conn)

        cursor = registry_conn.cursor()

        # Insert first project
        cursor.execute(
            "INSERT INTO projects (name, doc_root, db_path) VALUES (?, ?, ?)",
            ("test-project", "/docs", "/test.db"),
        )

        # Try to insert duplicate db_path
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO projects (name, doc_root, db_path) VALUES (?, ?, ?)",
                ("test-project-2", "/docs2", "/test.db"),
            )


class TestGetRegistrySchemaVersion:
    """Tests for get_registry_schema_version function."""

    def test_returns_zero_when_no_schema_version_table(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """schema_versionテーブルが存在しない場合は0を返す"""
        version = get_registry_schema_version(registry_conn)
        assert version == 0

    def test_returns_current_version_after_initialization(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """初期化後は現在のバージョンを返す"""
        initialize_registry(registry_conn)
        version = get_registry_schema_version(registry_conn)
        assert version == REGISTRY_SCHEMA_VERSION
        assert version > 0
