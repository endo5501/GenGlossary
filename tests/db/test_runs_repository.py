"""Tests for runs_repository module."""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from genglossary.db.connection import get_connection
from genglossary.db.runs_repository import (
    cancel_run,
    create_run,
    get_active_run,
    get_run,
    list_runs,
    update_run_progress,
    update_run_status,
)
from genglossary.db.schema import initialize_db


@pytest.fixture
def project_db(tmp_path: Path) -> sqlite3.Connection:
    """Create an in-memory project database with runs table for testing."""
    db_path = tmp_path / "test_project.db"
    connection = get_connection(str(db_path))
    initialize_db(connection)
    yield connection
    connection.close()


class TestCreateRun:
    """Tests for create_run function."""

    def test_create_run_returns_id(self, project_db: sqlite3.Connection) -> None:
        """Run作成は生成されたIDを返す"""
        run_id = create_run(project_db, scope="full")

        assert run_id > 0

    def test_create_run_with_all_fields(self, project_db: sqlite3.Connection) -> None:
        """全フィールドを指定してRunを作成できる"""
        run_id = create_run(
            project_db,
            scope="from_terms",
            triggered_by="api",
        )

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["scope"] == "from_terms"
        assert run["status"] == "pending"
        assert run["triggered_by"] == "api"

    def test_create_run_sets_timestamps(self, project_db: sqlite3.Connection) -> None:
        """Run作成時にタイムスタンプが設定される"""
        run_id = create_run(project_db, scope="full")

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["created_at"] is not None
        assert run["started_at"] is None
        assert run["finished_at"] is None

    def test_create_run_defaults_to_pending_status(
        self, project_db: sqlite3.Connection
    ) -> None:
        """Run作成時のデフォルトステータスはpending"""
        run_id = create_run(project_db, scope="full")

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "pending"


class TestGetRun:
    """Tests for get_run function."""

    def test_get_run_by_id(self, project_db: sqlite3.Connection) -> None:
        """IDでRunを取得できる"""
        run_id = create_run(project_db, scope="full")

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["id"] == run_id
        assert run["scope"] == "full"

    def test_get_nonexistent_returns_none(
        self, project_db: sqlite3.Connection
    ) -> None:
        """存在しないIDを指定するとNoneを返す"""
        run = get_run(project_db, 999)
        assert run is None


class TestGetActiveRun:
    """Tests for get_active_run function."""

    def test_get_active_run_returns_running_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """実行中のRunを取得できる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now())

        active_run = get_active_run(project_db)
        assert active_run is not None
        assert active_run["id"] == run_id
        assert active_run["status"] == "running"

    def test_get_active_run_returns_pending_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """待機中のRunを取得できる"""
        run_id = create_run(project_db, scope="full")

        active_run = get_active_run(project_db)
        assert active_run is not None
        assert active_run["id"] == run_id
        assert active_run["status"] == "pending"

    def test_get_active_run_returns_none_when_no_active(
        self, project_db: sqlite3.Connection
    ) -> None:
        """アクティブなRunがない場合はNoneを返す"""
        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "completed", finished_at=datetime.now()
        )

        active_run = get_active_run(project_db)
        assert active_run is None

    def test_get_active_run_returns_most_recent_when_multiple(
        self, project_db: sqlite3.Connection
    ) -> None:
        """複数のアクティブなRunがある場合は最新のものを返す"""
        import time

        run_id1 = create_run(project_db, scope="full")
        update_run_status(project_db, run_id1, "running", started_at=datetime.now())

        # Ensure different created_at timestamp
        time.sleep(1.1)

        run_id2 = create_run(project_db, scope="from_terms")
        update_run_status(project_db, run_id2, "running", started_at=datetime.now())

        active_run = get_active_run(project_db)
        assert active_run is not None
        assert active_run["id"] == run_id2  # Most recent


class TestListRuns:
    """Tests for list_runs function."""

    def test_list_empty(self, project_db: sqlite3.Connection) -> None:
        """Runがない場合は空リストを返す"""
        runs = list_runs(project_db)
        assert runs == []

    def test_list_multiple(self, project_db: sqlite3.Connection) -> None:
        """複数のRunをリストできる"""
        id1 = create_run(project_db, "full")
        id2 = create_run(project_db, "from_terms")
        id3 = create_run(project_db, "provisional_to_refined")

        runs = list_runs(project_db)
        assert len(runs) == 3

        run_ids = {r["id"] for r in runs}
        assert run_ids == {id1, id2, id3}

    def test_list_runs_ordered_by_created_at_desc(
        self, project_db: sqlite3.Connection
    ) -> None:
        """Runはcreated_atの降順でリストされる"""
        import time

        id1 = create_run(project_db, "full")
        time.sleep(1.1)  # SQLite datetime('now') is second-precision
        id2 = create_run(project_db, "from_terms")
        time.sleep(1.1)
        id3 = create_run(project_db, "provisional_to_refined")

        runs = list_runs(project_db)
        # Most recent first
        assert runs[0]["id"] == id3
        assert runs[1]["id"] == id2
        assert runs[2]["id"] == id1


class TestUpdateRunStatus:
    """Tests for update_run_status function."""

    def test_update_to_running(self, project_db: sqlite3.Connection) -> None:
        """ステータスをrunningに更新できる"""
        run_id = create_run(project_db, scope="full")
        started = datetime.now()

        update_run_status(project_db, run_id, "running", started_at=started)

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "running"
        assert run["started_at"] is not None

    def test_update_to_completed(self, project_db: sqlite3.Connection) -> None:
        """ステータスをcompletedに更新できる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now())
        finished = datetime.now()

        update_run_status(project_db, run_id, "completed", finished_at=finished)

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_update_to_failed_with_error(self, project_db: sqlite3.Connection) -> None:
        """ステータスをfailedに更新し、エラーメッセージを設定できる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now())

        update_run_status(
            project_db,
            run_id,
            "failed",
            finished_at=datetime.now(),
            error_message="LLM API error",
        )

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "failed"
        assert run["error_message"] == "LLM API error"


class TestUpdateRunProgress:
    """Tests for update_run_progress function."""

    def test_update_progress(self, project_db: sqlite3.Connection) -> None:
        """進捗情報を更新できる"""
        run_id = create_run(project_db, scope="full")

        update_run_progress(
            project_db, run_id, current=5, total=10, current_step="terms"
        )

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["progress_current"] == 5
        assert run["progress_total"] == 10
        assert run["current_step"] == "terms"

    def test_update_progress_multiple_times(
        self, project_db: sqlite3.Connection
    ) -> None:
        """進捗情報を複数回更新できる"""
        run_id = create_run(project_db, scope="full")

        update_run_progress(
            project_db, run_id, current=5, total=10, current_step="terms"
        )
        update_run_progress(
            project_db, run_id, current=10, total=10, current_step="provisional"
        )

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["progress_current"] == 10
        assert run["progress_total"] == 10
        assert run["current_step"] == "provisional"


class TestCancelRun:
    """Tests for cancel_run function."""

    def test_cancel_run(self, project_db: sqlite3.Connection) -> None:
        """Runをキャンセルできる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now())

        cancel_run(project_db, run_id)

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "cancelled"
        assert run["finished_at"] is not None

    def test_cancel_nonexistent_run_does_not_fail(
        self, project_db: sqlite3.Connection
    ) -> None:
        """存在しないRunをキャンセルしようとしても失敗しない"""
        cancel_run(project_db, 999)  # Should not raise


class TestCompleteRunIfNotCancelled:
    """Tests for complete_run_if_not_cancelled function."""

    def test_complete_running_run(self, project_db: sqlite3.Connection) -> None:
        """実行中のRunをcompletedに更新できる"""
        from genglossary.db.runs_repository import complete_run_if_not_cancelled

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now())

        result = complete_run_if_not_cancelled(project_db, run_id)

        assert result is True
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_does_not_complete_cancelled_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """cancelledのRunは更新されない"""
        from genglossary.db.runs_repository import complete_run_if_not_cancelled

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now())
        cancel_run(project_db, run_id)

        result = complete_run_if_not_cancelled(project_db, run_id)

        assert result is False
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "cancelled"

    def test_returns_false_for_nonexistent_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """存在しないRunに対してはFalseを返す"""
        from genglossary.db.runs_repository import complete_run_if_not_cancelled

        result = complete_run_if_not_cancelled(project_db, 999)

        assert result is False
