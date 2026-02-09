"""Tests for Project model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from genglossary.models.project import Project, ProjectStatus


class TestProjectCreation:
    """Tests for Project model creation."""

    def test_project_creation_with_defaults(self) -> None:
        """最小必須フィールドでProjectを作成できる"""
        project = Project(
            name="test-project",
            doc_root="/path/to/docs",
            db_path="/path/to/project.db",
        )

        assert project.name == "test-project"
        assert project.doc_root == "/path/to/docs"
        assert project.db_path == "/path/to/project.db"
        assert project.llm_provider == "ollama"
        assert project.llm_model == ""
        assert project.status == ProjectStatus.CREATED
        assert project.last_run_at is None

    def test_project_creation_with_all_fields(self) -> None:
        """全フィールドを指定してProjectを作成できる"""
        now = datetime.now()
        project = Project(
            id=1,
            name="my-novel",
            doc_root="/novels/mynovel",
            db_path="/novels/mynovel/project.db",
            llm_provider="openai",
            llm_model="gpt-4",
            llm_base_url="https://api.openai.com/v1",
            created_at=now,
            updated_at=now,
            last_run_at=now,
            status=ProjectStatus.COMPLETED,
        )

        assert project.id == 1
        assert project.name == "my-novel"
        assert project.doc_root == "/novels/mynovel"
        assert project.db_path == "/novels/mynovel/project.db"
        assert project.llm_provider == "openai"
        assert project.llm_model == "gpt-4"
        assert project.llm_base_url == "https://api.openai.com/v1"
        assert project.created_at == now
        assert project.updated_at == now
        assert project.last_run_at == now
        assert project.status == ProjectStatus.COMPLETED

    def test_project_has_llm_base_url_with_default(self) -> None:
        """llm_base_urlはデフォルトで空文字列"""
        project = Project(
            name="test-project",
            doc_root="/path/to/docs",
            db_path="/path/to/project.db",
        )

        assert project.llm_base_url == ""

    def test_project_name_cannot_be_empty(self) -> None:
        """プロジェクト名が空文字列の場合はエラーになる"""
        with pytest.raises(ValidationError):
            Project(
                name="",
                doc_root="/path/to/docs",
                db_path="/path/to/project.db",
            )

    def test_project_name_whitespace_only_fails(self) -> None:
        """プロジェクト名が空白のみの場合はエラーになる"""
        with pytest.raises(ValidationError):
            Project(
                name="   ",
                doc_root="/path/to/docs",
                db_path="/path/to/project.db",
            )

    def test_project_doc_root_can_be_empty(self) -> None:
        """doc_rootは空文字列を許容する (API経由の場合doc_rootは不要)"""
        project = Project(
            name="test-project",
            doc_root="",
            db_path="/path/to/project.db",
        )
        assert project.doc_root == ""

    def test_project_db_path_cannot_be_empty(self) -> None:
        """db_pathが空文字列の場合はエラーになる"""
        with pytest.raises(ValidationError):
            Project(
                name="test-project",
                doc_root="/path/to/docs",
                db_path="",
            )


class TestProjectStatus:
    """Tests for ProjectStatus enum."""

    def test_project_status_enum(self) -> None:
        """ProjectStatusは期待値を持つ"""
        assert ProjectStatus.CREATED == "created"
        assert ProjectStatus.RUNNING == "running"
        assert ProjectStatus.COMPLETED == "completed"
        assert ProjectStatus.ERROR == "error"

    def test_project_status_values(self) -> None:
        """ProjectStatusの全ての値が定義されている"""
        expected_values = {"created", "running", "completed", "error"}
        actual_values = {status.value for status in ProjectStatus}
        assert actual_values == expected_values


class TestProjectModel:
    """Tests for Project model behavior."""

    def test_project_model_config(self) -> None:
        """Projectモデルが正しい設定を持つ"""
        project = Project(
            name="test-project",
            doc_root="/path/to/docs",
            db_path="/path/to/project.db",
        )

        # Pydantic v2 behavior - can create dict from model
        project_dict = project.model_dump()
        assert isinstance(project_dict, dict)
        assert project_dict["name"] == "test-project"
