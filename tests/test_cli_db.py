"""Tests for CLI database commands."""

import sqlite3
from pathlib import Path

from click.testing import CliRunner

from genglossary.cli_db import db
from genglossary.db.connection import get_connection
from genglossary.db.run_repository import create_run
from genglossary.db.schema import initialize_db


class TestDbInit:
    """Test db init command."""

    def test_db_init_creates_database(self, tmp_path: Path) -> None:
        """Test that db init creates a database file."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        result = runner.invoke(db, ["init", "--path", str(db_path)])

        assert result.exit_code == 0
        assert db_path.exists()
        assert "データベースを初期化しました" in result.output

    def test_db_init_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test that db init creates parent directories."""
        runner = CliRunner()
        db_path = tmp_path / "subdir" / "db" / "test.db"

        result = runner.invoke(db, ["init", "--path", str(db_path)])

        assert result.exit_code == 0
        assert db_path.exists()
        assert db_path.parent.exists()

    def test_db_init_is_idempotent(self, tmp_path: Path) -> None:
        """Test that db init can be run multiple times."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # First init
        result1 = runner.invoke(db, ["init", "--path", str(db_path)])
        assert result1.exit_code == 0

        # Second init (should not fail)
        result2 = runner.invoke(db, ["init", "--path", str(db_path)])
        assert result2.exit_code == 0

    def test_db_init_creates_all_tables(self, tmp_path: Path) -> None:
        """Test that db init creates all required tables."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        runner.invoke(db, ["init", "--path", str(db_path)])

        # Verify tables exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected_tables = [
            "documents",
            "glossary_issues",
            "glossary_provisional",
            "glossary_refined",
            "runs",
            "schema_version",
            "terms_extracted",
        ]
        assert tables == expected_tables


class TestDbRunsList:
    """Test db runs list command."""

    def test_runs_list_shows_no_runs_message(self, tmp_path: Path) -> None:
        """Test that runs list shows message when no runs exist."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        result = runner.invoke(db, ["runs", "list", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "実行履歴がありません" in result.output

    def test_runs_list_shows_runs(self, tmp_path: Path) -> None:
        """Test that runs list displays runs."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create runs
        conn = get_connection(str(db_path))
        initialize_db(conn)
        create_run(conn, "/path/to/doc.txt", "ollama", "llama3.2")
        create_run(conn, "/path/to/other.txt", "openai", "gpt-4")
        conn.close()

        result = runner.invoke(db, ["runs", "list", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "実行履歴" in result.output
        # Rich table may truncate paths, so check for provider/model instead
        assert "ollama" in result.output
        assert "openai" in result.output
        assert "llama3.2" in result.output
        assert "gpt-4" in result.output

    def test_runs_list_respects_limit(self, tmp_path: Path) -> None:
        """Test that runs list respects limit parameter."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create multiple runs
        conn = get_connection(str(db_path))
        initialize_db(conn)
        for i in range(5):
            create_run(conn, f"/path/to/doc{i}.txt", "ollama", "llama3.2")
        conn.close()

        result = runner.invoke(
            db, ["runs", "list", "--db-path", str(db_path), "--limit", "2"]
        )

        assert result.exit_code == 0
        # Check that only 2 runs are shown (most recent ones)
        # Rich table may truncate, so check for parts
        assert "doc4" in result.output
        assert "doc3" in result.output
        assert "doc0" not in result.output


class TestDbRunsShow:
    """Test db runs show command."""

    def test_runs_show_displays_run_details(self, tmp_path: Path) -> None:
        """Test that runs show displays run details."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create a run
        conn = get_connection(str(db_path))
        initialize_db(conn)
        run_id = create_run(conn, "/path/to/doc.txt", "ollama", "llama3.2")
        conn.close()

        result = runner.invoke(db, ["runs", "show", str(run_id), "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert f"Run #{run_id}" in result.output
        assert "/path/to/doc.txt" in result.output
        assert "ollama" in result.output
        assert "llama3.2" in result.output
        assert "running" in result.output

    def test_runs_show_nonexistent_run(self, tmp_path: Path) -> None:
        """Test that runs show handles nonexistent run ID."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        result = runner.invoke(db, ["runs", "show", "999", "--db-path", str(db_path)])

        assert result.exit_code == 1
        assert "が見つかりません" in result.output


class TestDbRunsLatest:
    """Test db runs latest command."""

    def test_runs_latest_shows_no_runs_message(self, tmp_path: Path) -> None:
        """Test that runs latest shows message when no runs exist."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        result = runner.invoke(db, ["runs", "latest", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "実行履歴がありません" in result.output

    def test_runs_latest_shows_most_recent_run(self, tmp_path: Path) -> None:
        """Test that runs latest shows the most recent run."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create runs
        conn = get_connection(str(db_path))
        initialize_db(conn)
        create_run(conn, "/path/to/old.txt", "ollama", "llama3.2")
        run_id = create_run(conn, "/path/to/new.txt", "openai", "gpt-4")
        conn.close()

        result = runner.invoke(db, ["runs", "latest", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert f"Run #{run_id}" in result.output
        assert "(最新)" in result.output
        assert "/path/to/new.txt" in result.output
        assert "openai" in result.output
        # Old run should not be shown
        assert "/path/to/old.txt" not in result.output
