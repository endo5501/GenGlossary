"""Tests for CLI project commands."""

import sqlite3
from pathlib import Path

from click.testing import CliRunner

from genglossary.cli_project import project
from genglossary.db.project_repository import create_project, get_project_by_name
from genglossary.db.registry_connection import get_registry_connection
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.project import ProjectStatus


class TestProjectInit:
    """Test project init command."""

    def test_init_creates_project(self, tmp_path: Path) -> None:
        """プロジェクト作成コマンドが正常に動作する"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        result = runner.invoke(
            project,
            [
                "init",
                "test-project",
                "--doc-root",
                str(doc_root),
                "--registry",
                str(registry_path),
            ],
        )

        assert result.exit_code == 0
        assert "プロジェクトを作成しました" in result.output
        assert "test-project" in result.output
        assert registry_path.exists()

    def test_init_with_llm_settings(self, tmp_path: Path) -> None:
        """LLM設定を指定してプロジェクトを作成できる"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        result = runner.invoke(
            project,
            [
                "init",
                "test-project",
                "--doc-root",
                str(doc_root),
                "--llm-provider",
                "openai",
                "--llm-model",
                "gpt-4",
                "--registry",
                str(registry_path),
            ],
        )

        assert result.exit_code == 0

        # Verify settings were saved
        conn = get_registry_connection(str(registry_path))
        proj = get_project_by_name(conn, "test-project")
        conn.close()

        assert proj is not None
        assert proj.llm_provider == "openai"
        assert proj.llm_model == "gpt-4"

    def test_init_duplicate_name_fails(self, tmp_path: Path) -> None:
        """重複する名前でプロジェクトを作成しようとすると失敗する"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        # Create first project
        result1 = runner.invoke(
            project,
            [
                "init",
                "test-project",
                "--doc-root",
                str(doc_root),
                "--registry",
                str(registry_path),
            ],
        )
        assert result1.exit_code == 0

        # Try to create duplicate
        result2 = runner.invoke(
            project,
            [
                "init",
                "test-project",
                "--doc-root",
                str(doc_root),
                "--registry",
                str(registry_path),
            ],
        )
        assert result2.exit_code != 0
        assert "既に存在します" in result2.output or "UNIQUE constraint failed" in result2.output

    def test_init_creates_project_db(self, tmp_path: Path) -> None:
        """プロジェクト作成時にプロジェクトDBが作成される"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        runner.invoke(
            project,
            [
                "init",
                "test-project",
                "--doc-root",
                str(doc_root),
                "--registry",
                str(registry_path),
            ],
        )

        # Verify project DB was created
        conn = get_registry_connection(str(registry_path))
        proj = get_project_by_name(conn, "test-project")
        conn.close()

        assert proj is not None
        project_db_path = Path(proj.db_path)
        assert project_db_path.exists()

    def test_init_with_relative_registry_stores_absolute_db_path(
        self, tmp_path: Path
    ) -> None:
        """相対パスのregistryを使用した場合でも絶対パスが保存される"""
        import os

        runner = CliRunner()
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        # Use relative path for registry
        registry_dir = tmp_path / "registry_dir"
        registry_dir.mkdir()
        registry_path = registry_dir / "registry.db"

        # Change to tmp_path and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            relative_registry = Path("registry_dir") / "registry.db"

            result = runner.invoke(
                project,
                [
                    "init",
                    "test-project",
                    "--doc-root",
                    str(doc_root.absolute()),
                    "--registry",
                    str(relative_registry),
                ],
            )

            assert result.exit_code == 0

            # Verify db_path is absolute
            conn = get_registry_connection(str(registry_path))
            proj = get_project_by_name(conn, "test-project")
            conn.close()

            assert proj is not None
            db_path = Path(proj.db_path)
            assert db_path.is_absolute()
        finally:
            os.chdir(original_cwd)


class TestProjectList:
    """Test project list command."""

    def test_list_empty(self, tmp_path: Path) -> None:
        """プロジェクトがない場合のリスト表示"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"

        # Initialize empty registry
        conn = get_registry_connection(str(registry_path))
        initialize_registry(conn)
        conn.close()

        result = runner.invoke(project, ["list", "--registry", str(registry_path)])

        assert result.exit_code == 0
        assert "プロジェクトがありません" in result.output or "0" in result.output

    def test_list_shows_projects(self, tmp_path: Path) -> None:
        """プロジェクトリストを表示できる"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        # Initialize registry
        conn = get_registry_connection(str(registry_path))
        initialize_registry(conn)

        # Create projects
        create_project(
            conn,
            "project-1",
            str(doc_root),
            str(tmp_path / "project1.db"),
        )
        create_project(
            conn,
            "project-2",
            str(doc_root),
            str(tmp_path / "project2.db"),
            llm_provider="openai",
            llm_model="gpt-4",
        )
        conn.close()

        result = runner.invoke(project, ["list", "--registry", str(registry_path)])

        assert result.exit_code == 0
        assert "project-1" in result.output
        assert "project-2" in result.output

    def test_list_shows_project_details(self, tmp_path: Path) -> None:
        """プロジェクトリストに詳細情報が表示される"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        # Initialize registry
        conn = get_registry_connection(str(registry_path))
        initialize_registry(conn)

        # Create project with details
        create_project(
            conn,
            "my-novel",
            str(doc_root),
            str(tmp_path / "mynovel.db"),
            llm_provider="openai",
            llm_model="gpt-4",
            status=ProjectStatus.COMPLETED,
        )
        conn.close()

        result = runner.invoke(project, ["list", "--registry", str(registry_path)])

        assert result.exit_code == 0
        assert "my-novel" in result.output
        assert "openai" in result.output or "gpt-4" in result.output
        assert "completed" in result.output or "COMPLETED" in result.output


class TestProjectDelete:
    """Test project delete command."""

    def test_delete_removes_project(self, tmp_path: Path) -> None:
        """プロジェクトを削除できる"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        # Initialize and create project
        conn = get_registry_connection(str(registry_path))
        initialize_registry(conn)
        create_project(
            conn, "test-project", str(doc_root), str(tmp_path / "test.db")
        )
        conn.close()

        # Delete project
        result = runner.invoke(
            project, ["delete", "test-project", "--registry", str(registry_path)]
        )

        assert result.exit_code == 0
        assert "削除しました" in result.output

        # Verify project was deleted
        conn = get_registry_connection(str(registry_path))
        proj = get_project_by_name(conn, "test-project")
        conn.close()

        assert proj is None

    def test_delete_nonexistent_project(self, tmp_path: Path) -> None:
        """存在しないプロジェクトを削除しようとしてもエラーにならない"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"

        # Initialize empty registry
        conn = get_registry_connection(str(registry_path))
        initialize_registry(conn)
        conn.close()

        result = runner.invoke(
            project, ["delete", "nonexistent", "--registry", str(registry_path)]
        )

        # Should succeed (idempotent delete)
        assert result.exit_code == 0


class TestProjectClone:
    """Test project clone command."""

    def test_clone_creates_copy(self, tmp_path: Path) -> None:
        """プロジェクトを複製できる"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        # Initialize and create project
        conn = get_registry_connection(str(registry_path))
        initialize_registry(conn)
        create_project(
            conn,
            "original",
            str(doc_root),
            str(tmp_path / "original.db"),
            llm_provider="openai",
            llm_model="gpt-4",
        )
        conn.close()

        # Clone project
        result = runner.invoke(
            project,
            ["clone", "original", "clone", "--registry", str(registry_path)],
        )

        assert result.exit_code == 0
        assert "複製しました" in result.output

        # Verify clone exists
        conn = get_registry_connection(str(registry_path))
        original = get_project_by_name(conn, "original")
        clone = get_project_by_name(conn, "clone")
        conn.close()

        assert original is not None
        assert clone is not None
        assert clone.name == "clone"
        assert clone.doc_root == original.doc_root
        assert clone.llm_provider == original.llm_provider
        assert clone.llm_model == original.llm_model

    def test_clone_nonexistent_fails(self, tmp_path: Path) -> None:
        """存在しないプロジェクトを複製しようとすると失敗する"""
        runner = CliRunner()
        registry_path = tmp_path / "registry.db"

        # Initialize empty registry
        conn = get_registry_connection(str(registry_path))
        initialize_registry(conn)
        conn.close()

        result = runner.invoke(
            project,
            ["clone", "nonexistent", "clone", "--registry", str(registry_path)],
        )

        assert result.exit_code != 0
        assert "not found" in result.output or "見つかりません" in result.output


class TestBackwardCompatibility:
    """Test backward compatibility with existing db commands."""

    def test_db_commands_work_without_project(self, tmp_path: Path) -> None:
        """既存のdbコマンドはプロジェクトなしで動作する"""
        from genglossary.cli_db import db

        runner = CliRunner()
        db_path = tmp_path / "standalone.db"

        # db init should still work
        result = runner.invoke(db, ["init", "--path", str(db_path)])

        assert result.exit_code == 0
        assert db_path.exists()
        assert "データベースを初期化しました" in result.output
