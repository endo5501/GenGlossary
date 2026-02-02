"""Tests for runs_repository module."""

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from genglossary.db.connection import get_connection
from genglossary.db.runs_repository import (
    _current_utc_iso,
    _to_iso_string,
    cancel_run,
    complete_run_if_not_cancelled,
    create_run,
    get_active_run,
    get_run,
    list_runs,
    update_run_progress,
    update_run_status,
    update_run_status_if_running,
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
            scope="extract",
            triggered_by="api",
        )

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["scope"] == "extract"
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
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

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
            project_db, run_id, "completed", finished_at=datetime.now(timezone.utc)
        )

        active_run = get_active_run(project_db)
        assert active_run is None

    def test_get_active_run_returns_most_recent_when_multiple(
        self, project_db: sqlite3.Connection
    ) -> None:
        """複数のアクティブなRunがある場合は最新のものを返す"""
        import time

        run_id1 = create_run(project_db, scope="full")
        update_run_status(project_db, run_id1, "running", started_at=datetime.now(timezone.utc))

        # Ensure different created_at timestamp
        time.sleep(1.1)

        run_id2 = create_run(project_db, scope="extract")
        update_run_status(project_db, run_id2, "running", started_at=datetime.now(timezone.utc))

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
        id2 = create_run(project_db, "extract")
        id3 = create_run(project_db, "generate")

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
        id2 = create_run(project_db, "extract")
        time.sleep(1.1)
        id3 = create_run(project_db, "generate")

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
        started = datetime.now(timezone.utc)

        update_run_status(project_db, run_id, "running", started_at=started)

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "running"
        assert run["started_at"] is not None

    def test_update_to_completed(self, project_db: sqlite3.Connection) -> None:
        """ステータスをcompletedに更新できる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        finished = datetime.now(timezone.utc)

        update_run_status(project_db, run_id, "completed", finished_at=finished)

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_update_to_failed_with_error(self, project_db: sqlite3.Connection) -> None:
        """ステータスをfailedに更新し、エラーメッセージを設定できる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

        update_run_status(
            project_db,
            run_id,
            "failed",
            finished_at=datetime.now(timezone.utc),
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
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

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


class TestUpdateRunStatusIfRunning:
    """Tests for update_run_status_if_running function."""

    def test_updates_running_to_completed(
        self, project_db: sqlite3.Connection
    ) -> None:
        """running状態のRunをcompletedに更新できる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

        rows_updated = update_run_status_if_running(project_db, run_id, "completed")

        assert rows_updated == 1
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_does_not_update_pending(
        self, project_db: sqlite3.Connection
    ) -> None:
        """pending状態のRunは更新されない（0を返す）"""
        run_id = create_run(project_db, scope="full")

        rows_updated = update_run_status_if_running(project_db, run_id, "completed")

        assert rows_updated == 0
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "pending"

    def test_does_not_update_completed(
        self, project_db: sqlite3.Connection
    ) -> None:
        """completed状態のRunは更新されない"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(project_db, run_id, "completed", finished_at=datetime.now(timezone.utc))

        rows_updated = update_run_status_if_running(project_db, run_id, "failed")

        assert rows_updated == 0
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"

    def test_does_not_update_cancelled(
        self, project_db: sqlite3.Connection
    ) -> None:
        """cancelled状態のRunは更新されない"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        cancel_run(project_db, run_id)

        rows_updated = update_run_status_if_running(project_db, run_id, "completed")

        assert rows_updated == 0
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "cancelled"

    def test_does_not_update_failed(
        self, project_db: sqlite3.Connection
    ) -> None:
        """failed状態のRunは更新されない"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(
            project_db, run_id, "failed",
            finished_at=datetime.now(timezone.utc), error_message="Test error"
        )

        rows_updated = update_run_status_if_running(project_db, run_id, "completed")

        assert rows_updated == 0
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "failed"

    def test_returns_zero_for_nonexistent_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """存在しないRunに対しては0を返す"""
        rows_updated = update_run_status_if_running(project_db, 999, "completed")

        assert rows_updated == 0

    def test_rejects_naive_finished_at(
        self, project_db: sqlite3.Connection
    ) -> None:
        """naive datetimeのfinished_atを拒否する"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        naive_datetime = datetime.now()  # No timezone

        with pytest.raises(ValueError, match="timezone-aware"):
            update_run_status_if_running(
                project_db, run_id, "completed", finished_at=naive_datetime
            )


class TestCompleteRunIfNotCancelled:
    """Tests for complete_run_if_not_cancelled function."""

    def test_complete_running_run(self, project_db: sqlite3.Connection) -> None:
        """実行中のRunをcompletedに更新できる"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

        result = complete_run_if_not_cancelled(project_db, run_id)

        assert result is True
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_does_not_complete_pending_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """pending状態のRunはcompletedに更新されない"""
        run_id = create_run(project_db, scope="full")

        result = complete_run_if_not_cancelled(project_db, run_id)

        assert result is False
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "pending"

    def test_does_not_complete_cancelled_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """cancelledのRunは更新されない"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
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
        result = complete_run_if_not_cancelled(project_db, 999)

        assert result is False

    def test_does_not_overwrite_failed_status(
        self, project_db: sqlite3.Connection
    ) -> None:
        """failedのRunは更新されない"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(
            project_db, run_id, "failed",
            finished_at=datetime.now(timezone.utc), error_message="Test error"
        )

        result = complete_run_if_not_cancelled(project_db, run_id)

        assert result is False
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "failed"
        assert run["error_message"] == "Test error"

    def test_does_not_overwrite_completed_status(
        self, project_db: sqlite3.Connection
    ) -> None:
        """既にcompletedのRunは更新されない"""
        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(project_db, run_id, "completed", finished_at=datetime.now(timezone.utc))

        result = complete_run_if_not_cancelled(project_db, run_id)

        assert result is False
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"


class TestFailRunIfNotTerminal:
    """Tests for fail_run_if_not_terminal function."""

    def test_fail_running_run(self, project_db: sqlite3.Connection) -> None:
        """実行中のRunをfailedに更新できる"""
        from genglossary.db.runs_repository import fail_run_if_not_terminal

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

        result = fail_run_if_not_terminal(
            project_db, run_id, error_message="Test error"
        )

        assert result is True
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "failed"
        assert run["error_message"] == "Test error"
        assert run["finished_at"] is not None

    def test_fail_pending_run(self, project_db: sqlite3.Connection) -> None:
        """pending状態のRunをfailedに更新できる"""
        from genglossary.db.runs_repository import fail_run_if_not_terminal

        run_id = create_run(project_db, scope="full")

        result = fail_run_if_not_terminal(
            project_db, run_id, error_message="Test error"
        )

        assert result is True
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "failed"
        assert run["error_message"] == "Test error"

    def test_does_not_overwrite_cancelled_status(
        self, project_db: sqlite3.Connection
    ) -> None:
        """cancelledのRunは上書きされない"""
        from genglossary.db.runs_repository import fail_run_if_not_terminal

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        cancel_run(project_db, run_id)

        result = fail_run_if_not_terminal(
            project_db, run_id, error_message="Test error"
        )

        assert result is False
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "cancelled"
        assert run["error_message"] is None

    def test_does_not_overwrite_completed_status(
        self, project_db: sqlite3.Connection
    ) -> None:
        """completedのRunは上書きされない"""
        from genglossary.db.runs_repository import fail_run_if_not_terminal

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(project_db, run_id, "completed", finished_at=datetime.now(timezone.utc))

        result = fail_run_if_not_terminal(
            project_db, run_id, error_message="Test error"
        )

        assert result is False
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"
        assert run["error_message"] is None

    def test_does_not_overwrite_failed_status(
        self, project_db: sqlite3.Connection
    ) -> None:
        """既にfailedのRunは上書きされない（べき等性）"""
        from genglossary.db.runs_repository import fail_run_if_not_terminal

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(
            project_db, run_id, "failed",
            finished_at=datetime.now(timezone.utc), error_message="Original error"
        )

        result = fail_run_if_not_terminal(
            project_db, run_id, error_message="New error"
        )

        assert result is False
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "failed"
        assert run["error_message"] == "Original error"

    def test_returns_false_for_nonexistent_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """存在しないRunに対してはFalseを返す"""
        from genglossary.db.runs_repository import fail_run_if_not_terminal

        result = fail_run_if_not_terminal(
            project_db, 999, error_message="Test error"
        )

        assert result is False


class TestUpdateRunStatusIfActive:
    """Tests for update_run_status_if_active function."""

    def test_update_running_run_to_completed(
        self, project_db: sqlite3.Connection
    ) -> None:
        """running状態のRunをcompletedに更新できる"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

        rows_updated = update_run_status_if_active(project_db, run_id, "completed")

        assert rows_updated == 1
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_update_pending_run_to_cancelled(
        self, project_db: sqlite3.Connection
    ) -> None:
        """pending状態のRunをcancelledに更新できる"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")

        rows_updated = update_run_status_if_active(project_db, run_id, "cancelled")

        assert rows_updated == 1
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "cancelled"
        assert run["finished_at"] is not None

    def test_update_running_run_to_failed_with_error_message(
        self, project_db: sqlite3.Connection
    ) -> None:
        """running状態のRunをfailedに更新し、エラーメッセージを設定できる"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

        rows_updated = update_run_status_if_active(
            project_db, run_id, "failed", error_message="Test error"
        )

        assert rows_updated == 1
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "failed"
        assert run["error_message"] == "Test error"
        assert run["finished_at"] is not None

    def test_does_not_update_terminal_state(
        self, project_db: sqlite3.Connection
    ) -> None:
        """terminal状態のRunは更新されない"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        cancel_run(project_db, run_id)

        rows_updated = update_run_status_if_active(project_db, run_id, "completed")

        assert rows_updated == 0
        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "cancelled"

    def test_returns_zero_for_nonexistent_run(
        self, project_db: sqlite3.Connection
    ) -> None:
        """存在しないRunに対しては0を返す"""
        from genglossary.db.runs_repository import update_run_status_if_active

        rows_updated = update_run_status_if_active(project_db, 999, "completed")

        assert rows_updated == 0


class TestTimestampFormatConsistency:
    """Tests for timestamp format consistency across repository functions."""

    # ISO 8601 format with UTC timezone: 2026-01-31T15:13:13+00:00
    ISO_UTC_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$"
    )

    def test_create_run_uses_utc_iso_format_for_created_at(
        self, project_db: sqlite3.Connection
    ) -> None:
        """create_runはcreated_atにUTC ISO形式のタイムスタンプを保存する"""
        run_id = create_run(project_db, scope="full")

        run = get_run(project_db, run_id)
        assert run is not None
        assert self.ISO_UTC_PATTERN.match(
            run["created_at"]
        ), f"created_at format mismatch: {run['created_at']}"

    def test_update_run_status_uses_utc_iso_format(
        self, project_db: sqlite3.Connection
    ) -> None:
        """update_run_statusはUTC ISO形式のタイムスタンプを保存する"""
        run_id = create_run(project_db, scope="full")
        started = datetime.now(timezone.utc)
        finished = datetime.now(timezone.utc)

        update_run_status(
            project_db, run_id, "completed",
            started_at=started, finished_at=finished
        )

        run = get_run(project_db, run_id)
        assert run is not None
        assert self.ISO_UTC_PATTERN.match(
            run["started_at"]
        ), f"started_at format mismatch: {run['started_at']}"
        assert self.ISO_UTC_PATTERN.match(
            run["finished_at"]
        ), f"finished_at format mismatch: {run['finished_at']}"

    def test_update_run_status_if_active_uses_utc_iso_format(
        self, project_db: sqlite3.Connection
    ) -> None:
        """update_run_status_if_activeはUTC ISO形式のタイムスタンプを保存する"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "running",
            started_at=datetime.now(timezone.utc)
        )

        update_run_status_if_active(project_db, run_id, "completed")

        run = get_run(project_db, run_id)
        assert run is not None
        assert self.ISO_UTC_PATTERN.match(
            run["finished_at"]
        ), f"finished_at format mismatch: {run['finished_at']}"

    def test_cancel_run_uses_utc_iso_format(
        self, project_db: sqlite3.Connection
    ) -> None:
        """cancel_runはUTC ISO形式のタイムスタンプを保存する"""
        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "running",
            started_at=datetime.now(timezone.utc)
        )

        cancel_run(project_db, run_id)

        run = get_run(project_db, run_id)
        assert run is not None
        assert self.ISO_UTC_PATTERN.match(
            run["finished_at"]
        ), f"finished_at format mismatch: {run['finished_at']}"

    def test_timestamps_are_consistent_between_functions(
        self, project_db: sqlite3.Connection
    ) -> None:
        """異なる関数で保存されたタイムスタンプのフォーマットが一致する"""
        from genglossary.db.runs_repository import update_run_status_if_active

        # Run 1: update_run_statusでfinished_atを設定
        run_id1 = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id1, "running",
            started_at=datetime.now(timezone.utc)
        )
        update_run_status(
            project_db, run_id1, "completed",
            finished_at=datetime.now(timezone.utc)
        )

        # Run 2: update_run_status_if_activeでfinished_atを設定
        run_id2 = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id2, "running",
            started_at=datetime.now(timezone.utc)
        )
        update_run_status_if_active(project_db, run_id2, "completed")

        run1 = get_run(project_db, run_id1)
        run2 = get_run(project_db, run_id2)
        assert run1 is not None
        assert run2 is not None

        # 両方のタイムスタンプが同じフォーマットであることを確認
        # (正規表現で検証することで、フォーマットの一致を保証)
        assert self.ISO_UTC_PATTERN.match(run1["finished_at"])
        assert self.ISO_UTC_PATTERN.match(run2["finished_at"])


class TestTimezoneValidation:
    """Tests for timezone-aware datetime validation."""

    def test_update_run_status_rejects_naive_started_at(
        self, project_db: sqlite3.Connection
    ) -> None:
        """update_run_statusはnaive datetimeのstarted_atを拒否する"""
        run_id = create_run(project_db, scope="full")
        naive_datetime = datetime.now()  # No timezone

        with pytest.raises(ValueError, match="timezone-aware"):
            update_run_status(project_db, run_id, "running", started_at=naive_datetime)

    def test_update_run_status_rejects_naive_finished_at(
        self, project_db: sqlite3.Connection
    ) -> None:
        """update_run_statusはnaive datetimeのfinished_atを拒否する"""
        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "running", started_at=datetime.now(timezone.utc)
        )
        naive_datetime = datetime.now()  # No timezone

        with pytest.raises(ValueError, match="timezone-aware"):
            update_run_status(
                project_db, run_id, "completed", finished_at=naive_datetime
            )

    def test_update_run_status_accepts_timezone_aware_datetime(
        self, project_db: sqlite3.Connection
    ) -> None:
        """update_run_statusはtimezone-aware datetimeを受け付ける"""
        run_id = create_run(project_db, scope="full")
        aware_datetime = datetime.now(timezone.utc)

        # Should not raise
        update_run_status(project_db, run_id, "running", started_at=aware_datetime)

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["status"] == "running"


class TestUpdateRunStatusIfActiveWithFinishedAt:
    """Tests for update_run_status_if_active with explicit finished_at parameter."""

    # ISO 8601 format with UTC timezone: 2026-01-31T15:13:13+00:00
    ISO_UTC_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$"
    )

    def test_uses_provided_finished_at(
        self, project_db: sqlite3.Connection
    ) -> None:
        """明示的に渡されたfinished_atを使用する"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "running", started_at=datetime.now(timezone.utc)
        )

        # Use a specific timestamp
        finished = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        update_run_status_if_active(
            project_db, run_id, "completed", finished_at=finished
        )

        run = get_run(project_db, run_id)
        assert run is not None
        assert run["finished_at"] == "2026-01-15T12:00:00+00:00"

    def test_defaults_to_current_time_when_finished_at_not_provided(
        self, project_db: sqlite3.Connection
    ) -> None:
        """finished_atが渡されない場合は現在時刻を使用する"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "running", started_at=datetime.now(timezone.utc)
        )

        before = datetime.now(timezone.utc).replace(microsecond=0)
        update_run_status_if_active(project_db, run_id, "completed")
        after = datetime.now(timezone.utc).replace(microsecond=0)

        run = get_run(project_db, run_id)
        assert run is not None
        # Verify it's in the expected format
        assert self.ISO_UTC_PATTERN.match(run["finished_at"])
        # Verify the timestamp is between before and after (second precision)
        finished = datetime.fromisoformat(run["finished_at"])
        assert before <= finished <= after + timedelta(seconds=1)

    def test_rejects_naive_finished_at(
        self, project_db: sqlite3.Connection
    ) -> None:
        """naive datetimeのfinished_atを拒否する"""
        from genglossary.db.runs_repository import update_run_status_if_active

        run_id = create_run(project_db, scope="full")
        update_run_status(
            project_db, run_id, "running", started_at=datetime.now(timezone.utc)
        )
        naive_datetime = datetime.now()

        with pytest.raises(ValueError, match="timezone-aware"):
            update_run_status_if_active(
                project_db, run_id, "completed", finished_at=naive_datetime
            )


class TestToIsoString:
    """Tests for _to_iso_string helper function."""

    # ISO 8601 format with UTC timezone: 2026-01-31T15:13:13+00:00
    ISO_UTC_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$"
    )

    def test_returns_none_for_none_input(self) -> None:
        """Noneを渡すとNoneを返す"""
        result = _to_iso_string(None, "test_param")
        assert result is None

    def test_returns_iso_string_for_timezone_aware_datetime(self) -> None:
        """timezone-aware datetimeをISO文字列に変換する"""
        dt = datetime(2026, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        result = _to_iso_string(dt, "test_param")
        assert result == "2026-01-15T12:30:45+00:00"

    def test_raises_for_naive_datetime(self) -> None:
        """naive datetimeはValueErrorを発生させる"""
        naive_dt = datetime(2026, 1, 15, 12, 30, 45)
        with pytest.raises(ValueError, match="timezone-aware"):
            _to_iso_string(naive_dt, "test_param")

    def test_uses_param_name_in_error_message(self) -> None:
        """エラーメッセージにパラメータ名を含む"""
        naive_dt = datetime(2026, 1, 15, 12, 30, 45)
        with pytest.raises(ValueError, match="my_timestamp"):
            _to_iso_string(naive_dt, "my_timestamp")


class TestGetCurrentOrLatestRun:
    """Tests for get_current_or_latest_run function."""

    def test_returns_active_run_when_exists(
        self, project_db: sqlite3.Connection
    ) -> None:
        """アクティブなRunがある場合はそれを返す"""
        from genglossary.db.runs_repository import get_current_or_latest_run

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))

        result = get_current_or_latest_run(project_db)
        assert result is not None
        assert result["id"] == run_id
        assert result["status"] == "running"

    def test_returns_completed_run_when_no_active(
        self, project_db: sqlite3.Connection
    ) -> None:
        """アクティブなRunがない場合は最新の完了Runを返す"""
        from genglossary.db.runs_repository import get_current_or_latest_run

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(project_db, run_id, "completed", finished_at=datetime.now(timezone.utc))

        result = get_current_or_latest_run(project_db)
        assert result is not None
        assert result["id"] == run_id
        assert result["status"] == "completed"

    def test_returns_latest_run_among_multiple_completed(
        self, project_db: sqlite3.Connection
    ) -> None:
        """複数の完了Runがある場合は最新のものを返す"""
        import time
        from genglossary.db.runs_repository import get_current_or_latest_run

        # Create first run and complete it
        run_id1 = create_run(project_db, scope="full")
        update_run_status(project_db, run_id1, "running", started_at=datetime.now(timezone.utc))
        update_run_status(project_db, run_id1, "completed", finished_at=datetime.now(timezone.utc))

        # Ensure different created_at timestamp
        time.sleep(1.1)

        # Create second run and complete it
        run_id2 = create_run(project_db, scope="extract")
        update_run_status(project_db, run_id2, "running", started_at=datetime.now(timezone.utc))
        update_run_status(project_db, run_id2, "completed", finished_at=datetime.now(timezone.utc))

        result = get_current_or_latest_run(project_db)
        assert result is not None
        assert result["id"] == run_id2  # Most recent

    def test_returns_active_over_completed(
        self, project_db: sqlite3.Connection
    ) -> None:
        """完了RunとアクティブRunがある場合はアクティブRunを返す"""
        import time
        from genglossary.db.runs_repository import get_current_or_latest_run

        # Create first run and complete it
        run_id1 = create_run(project_db, scope="full")
        update_run_status(project_db, run_id1, "running", started_at=datetime.now(timezone.utc))
        update_run_status(project_db, run_id1, "completed", finished_at=datetime.now(timezone.utc))

        # Ensure different created_at timestamp
        time.sleep(1.1)

        # Create second run (still running)
        run_id2 = create_run(project_db, scope="extract")
        update_run_status(project_db, run_id2, "running", started_at=datetime.now(timezone.utc))

        result = get_current_or_latest_run(project_db)
        assert result is not None
        assert result["id"] == run_id2  # Active run takes priority
        assert result["status"] == "running"

    def test_returns_none_when_no_runs(
        self, project_db: sqlite3.Connection
    ) -> None:
        """Runがない場合はNoneを返す"""
        from genglossary.db.runs_repository import get_current_or_latest_run

        result = get_current_or_latest_run(project_db)
        assert result is None

    def test_returns_failed_run_when_no_active(
        self, project_db: sqlite3.Connection
    ) -> None:
        """アクティブなRunがない場合は失敗したRunも返す"""
        from genglossary.db.runs_repository import get_current_or_latest_run

        run_id = create_run(project_db, scope="full")
        update_run_status(project_db, run_id, "running", started_at=datetime.now(timezone.utc))
        update_run_status(
            project_db, run_id, "failed",
            finished_at=datetime.now(timezone.utc),
            error_message="Test error"
        )

        result = get_current_or_latest_run(project_db)
        assert result is not None
        assert result["id"] == run_id
        assert result["status"] == "failed"


class TestCurrentUtcIso:
    """Tests for _current_utc_iso helper function."""

    # ISO 8601 format with UTC timezone: 2026-01-31T15:13:13+00:00
    ISO_UTC_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+00:00|Z)$"
    )

    def test_returns_utc_iso_format_string(self) -> None:
        """UTC ISO形式の文字列を返す"""
        result = _current_utc_iso()
        assert self.ISO_UTC_PATTERN.match(result), f"Format mismatch: {result}"

    def test_returns_current_time(self) -> None:
        """現在時刻を返す"""
        before = datetime.now(timezone.utc).replace(microsecond=0)
        result = _current_utc_iso()
        after = datetime.now(timezone.utc).replace(microsecond=0)

        result_dt = datetime.fromisoformat(result)
        assert before <= result_dt <= after + timedelta(seconds=1)
