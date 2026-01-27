"""Tests for project_repository module."""

import sqlite3
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from genglossary.db.project_repository import (
    clone_project,
    create_project,
    delete_project,
    get_project,
    get_project_by_name,
    list_projects,
    update_project,
)
from genglossary.db.registry_connection import get_registry_connection
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.project import ProjectStatus


@pytest.fixture
def registry_conn() -> sqlite3.Connection:
    """Create an in-memory registry database connection for testing."""
    connection = get_registry_connection(":memory:")
    initialize_registry(connection)
    yield connection
    connection.close()


class TestCreateProject:
    """Tests for create_project function."""

    def test_create_project_returns_id(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """プロジェクト作成は生成されたIDを返す"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        assert project_id > 0

    def test_create_project_with_all_fields(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """全フィールドを指定してプロジェクトを作成できる"""
        project_id = create_project(
            registry_conn,
            name="my-novel",
            doc_root=str(tmp_path / "novels" / "mynovel"),
            db_path=str(tmp_path / "novels" / "mynovel" / "project.db"),
            llm_provider="openai",
            llm_model="gpt-4",
            llm_base_url="https://api.openai.com/v1",
            status=ProjectStatus.COMPLETED,
        )

        project = get_project(registry_conn, project_id)
        assert project is not None
        assert project.name == "my-novel"
        assert project.llm_provider == "openai"
        assert project.llm_model == "gpt-4"
        assert project.llm_base_url == "https://api.openai.com/v1"
        assert project.status == ProjectStatus.COMPLETED

    def test_create_project_with_default_llm_base_url(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """llm_base_urlを指定しない場合は空文字列がデフォルト"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        project = get_project(registry_conn, project_id)
        assert project is not None
        assert project.llm_base_url == ""

    def test_create_project_sets_timestamps(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """プロジェクト作成時にタイムスタンプが設定される"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        project = get_project(registry_conn, project_id)
        assert project is not None
        # Verify timestamps are set (SQLite uses UTC)
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.created_at == project.updated_at

    def test_create_duplicate_name_raises(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """重複する名前でプロジェクトを作成しようとすると例外が発生する"""
        create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            create_project(
                registry_conn,
                name="test-project",
                doc_root=str(tmp_path / "docs2"),
                db_path=str(tmp_path / "project2.db"),
            )

    def test_create_duplicate_db_path_raises(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """重複するdb_pathでプロジェクトを作成しようとすると例外が発生する"""
        create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            create_project(
                registry_conn,
                name="test-project-2",
                doc_root=str(tmp_path / "docs2"),
                db_path=str(tmp_path / "project.db"),
            )

    def test_create_project_db_init_failure_does_not_pollute_registry(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """プロジェクトDB初期化が失敗した場合、レジストリが汚染されない"""
        # Mock initialize_db to raise an exception
        with patch("genglossary.db.project_repository.initialize_db") as mock_init:
            mock_init.side_effect = RuntimeError("DB initialization failed")

            # Attempt to create project should fail
            with pytest.raises(RuntimeError, match="DB initialization failed"):
                create_project(
                    registry_conn,
                    name="test-project",
                    doc_root=str(tmp_path / "docs"),
                    db_path=str(tmp_path / "project.db"),
                )

        # Registry should not have any projects
        projects = list_projects(registry_conn)
        assert len(projects) == 0


class TestGetProject:
    """Tests for get_project function."""

    def test_get_project_by_id(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """IDでプロジェクトを取得できる"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        project = get_project(registry_conn, project_id)
        assert project is not None
        assert project.id == project_id
        assert project.name == "test-project"

    def test_get_nonexistent_returns_none(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """存在しないIDを指定するとNoneを返す"""
        project = get_project(registry_conn, 999)
        assert project is None


class TestGetProjectByName:
    """Tests for get_project_by_name function."""

    def test_get_by_name(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """名前でプロジェクトを取得できる"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        project = get_project_by_name(registry_conn, "test-project")
        assert project is not None
        assert project.id == project_id
        assert project.name == "test-project"

    def test_get_by_name_not_found(self, registry_conn: sqlite3.Connection) -> None:
        """存在しない名前を指定するとNoneを返す"""
        project = get_project_by_name(registry_conn, "nonexistent")
        assert project is None


class TestListProjects:
    """Tests for list_projects function."""

    def test_list_empty(self, registry_conn: sqlite3.Connection) -> None:
        """プロジェクトがない場合は空リストを返す"""
        projects = list_projects(registry_conn)
        assert projects == []

    def test_list_multiple(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """複数のプロジェクトをリストできる"""
        id1 = create_project(
            registry_conn,
            "project-1",
            str(tmp_path / "docs1"),
            str(tmp_path / "project1.db"),
        )
        id2 = create_project(
            registry_conn,
            "project-2",
            str(tmp_path / "docs2"),
            str(tmp_path / "project2.db"),
        )
        id3 = create_project(
            registry_conn,
            "project-3",
            str(tmp_path / "docs3"),
            str(tmp_path / "project3.db"),
        )

        projects = list_projects(registry_conn)
        assert len(projects) == 3

        project_ids = {p.id for p in projects}
        assert project_ids == {id1, id2, id3}

        project_names = {p.name for p in projects}
        assert project_names == {"project-1", "project-2", "project-3"}

    def test_list_projects_ordered_by_created_at(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """プロジェクトはcreated_atの降順でリストされる"""
        import time

        create_project(
            registry_conn,
            "project-old",
            str(tmp_path / "docs1"),
            str(tmp_path / "project1.db"),
        )
        time.sleep(1.1)  # SQLite datetime('now') is second-precision
        create_project(
            registry_conn,
            "project-mid",
            str(tmp_path / "docs2"),
            str(tmp_path / "project2.db"),
        )
        time.sleep(1.1)
        create_project(
            registry_conn,
            "project-new",
            str(tmp_path / "docs3"),
            str(tmp_path / "project3.db"),
        )

        projects = list_projects(registry_conn)
        # Most recent first
        assert projects[0].name == "project-new"
        assert projects[1].name == "project-mid"
        assert projects[2].name == "project-old"


class TestUpdateProject:
    """Tests for update_project function."""

    def test_update_llm_settings(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """LLM設定を更新できる"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        update_project(
            registry_conn,
            project_id,
            llm_provider="openai",
            llm_model="gpt-4",
        )

        project = get_project(registry_conn, project_id)
        assert project is not None
        assert project.llm_provider == "openai"
        assert project.llm_model == "gpt-4"

    def test_update_llm_base_url(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """llm_base_urlを更新できる"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        update_project(
            registry_conn,
            project_id,
            llm_base_url="https://api.openai.com/v1",
        )

        project = get_project(registry_conn, project_id)
        assert project is not None
        assert project.llm_base_url == "https://api.openai.com/v1"

    def test_update_status(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """ステータスを更新できる"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        update_project(registry_conn, project_id, status=ProjectStatus.RUNNING)

        project = get_project(registry_conn, project_id)
        assert project is not None
        assert project.status == ProjectStatus.RUNNING

    def test_update_last_run_at(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """last_run_atを更新できる"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        run_time = datetime.now()
        update_project(registry_conn, project_id, last_run_at=run_time)

        project = get_project(registry_conn, project_id)
        assert project is not None
        assert project.last_run_at is not None
        assert project.last_run_at == run_time

    def test_update_updates_updated_at(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """更新時にupdated_atタイムスタンプが更新される"""
        import time

        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        original_project = get_project(registry_conn, project_id)
        assert original_project is not None
        original_updated_at = original_project.updated_at

        # Delay to ensure timestamp difference (SQLite datetime is second-precision)
        time.sleep(1.1)

        update_project(registry_conn, project_id, llm_provider="openai")

        updated_project = get_project(registry_conn, project_id)
        assert updated_project is not None
        assert updated_project.updated_at > original_updated_at

    def test_update_nonexistent_raises(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """存在しないプロジェクトを更新しようとすると例外が発生する"""
        with pytest.raises(ValueError, match="Project with id 999 not found"):
            update_project(registry_conn, 999, llm_provider="openai")


class TestDeleteProject:
    """Tests for delete_project function."""

    def test_delete_removes_project(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """プロジェクトを削除できる"""
        project_id = create_project(
            registry_conn,
            name="test-project",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "project.db"),
        )

        delete_project(registry_conn, project_id)

        project = get_project(registry_conn, project_id)
        assert project is None

    def test_delete_nonexistent_does_not_fail(
        self, registry_conn: sqlite3.Connection
    ) -> None:
        """存在しないプロジェクトを削除しようとしても失敗しない"""
        delete_project(registry_conn, 999)  # Should not raise


class TestCloneProject:
    """Tests for clone_project function."""

    def test_clone_creates_copy(self, registry_conn: sqlite3.Connection, tmp_path: Path) -> None:
        """プロジェクトを複製できる"""
        original_id = create_project(
            registry_conn,
            name="original",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "original.db"),
            llm_provider="openai",
            llm_model="gpt-4",
        )

        clone_id = clone_project(
            registry_conn,
            original_id,
            new_name="clone",
            new_db_path=str(tmp_path / "clone.db"),
        )

        assert clone_id != original_id

        original = get_project(registry_conn, original_id)
        clone = get_project(registry_conn, clone_id)

        assert original is not None
        assert clone is not None

        # Clone should have new name and db_path
        assert clone.name == "clone"

        # Clone should inherit other properties
        assert clone.doc_root == original.doc_root
        assert clone.llm_provider == original.llm_provider
        assert clone.llm_model == original.llm_model

        # Clone should have its own ID
        assert clone.id != original.id

    def test_clone_resets_status_and_last_run(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """複製時にstatusとlast_run_atがリセットされる"""
        original_id = create_project(
            registry_conn,
            name="original",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "original.db"),
        )

        # Update original to completed status with last_run_at
        update_project(
            registry_conn,
            original_id,
            status=ProjectStatus.COMPLETED,
            last_run_at=datetime.now(),
        )

        clone_id = clone_project(
            registry_conn,
            original_id,
            new_name="clone",
            new_db_path=str(tmp_path / "clone.db"),
        )

        clone = get_project(registry_conn, clone_id)
        assert clone is not None
        assert clone.status == ProjectStatus.CREATED
        assert clone.last_run_at is None

    def test_clone_nonexistent_raises(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """存在しないプロジェクトを複製しようとすると例外が発生する"""
        with pytest.raises(ValueError, match="Project with id 999 not found"):
            clone_project(
                registry_conn,
                999,
                new_name="clone",
                new_db_path=str(tmp_path / "clone.db"),
            )

    def test_clone_with_duplicate_name_raises(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """既存の名前で複製しようとすると例外が発生する"""
        original_id = create_project(
            registry_conn,
            name="original",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "original.db"),
        )
        create_project(
            registry_conn,
            name="existing",
            doc_root=str(tmp_path / "docs2"),
            db_path=str(tmp_path / "existing.db"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            clone_project(
                registry_conn,
                original_id,
                new_name="existing",
                new_db_path=str(tmp_path / "clone.db"),
            )

    def test_clone_copies_database_content(
        self, registry_conn: sqlite3.Connection, tmp_path: Path
    ) -> None:
        """複製時にソースDBの内容が新DBにコピーされる"""
        from genglossary.db.connection import get_connection

        # Create original project
        original_id = create_project(
            registry_conn,
            name="original",
            doc_root=str(tmp_path / "docs"),
            db_path=str(tmp_path / "original.db"),
        )

        # Insert test data into source DB
        source_conn = get_connection(str(tmp_path / "original.db"))
        source_conn.execute(
            "INSERT INTO documents (file_path, content_hash) VALUES (?, ?)",
            ("/path/to/doc.txt", "hash123"),
        )
        source_conn.commit()
        source_conn.close()

        # Clone project
        clone_id = clone_project(
            registry_conn,
            original_id,
            new_name="clone",
            new_db_path=str(tmp_path / "clone.db"),
        )

        # Verify cloned DB has the same data
        clone_conn = get_connection(str(tmp_path / "clone.db"))
        cursor = clone_conn.cursor()
        cursor.execute("SELECT file_path, content_hash FROM documents")
        rows = cursor.fetchall()
        clone_conn.close()

        assert len(rows) == 1
        assert rows[0]["file_path"] == "/path/to/doc.txt"
        assert rows[0]["content_hash"] == "hash123"
