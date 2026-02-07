"""Tests for CLI database commands."""

import sqlite3
from pathlib import Path

from click.testing import CliRunner

from genglossary.cli_db import db
from genglossary.db.connection import get_connection, transaction
from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import create_term


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
            "metadata",
            "runs",
            "schema_version",
            "terms_excluded",
            "terms_extracted",
            "terms_required",
        ]
        assert tables == expected_tables


class TestDbInfo:
    """Test db info command."""

    def test_info_shows_no_metadata_message(self, tmp_path: Path) -> None:
        """Test that info shows message when no metadata exists."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        result = runner.invoke(db, ["info", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "メタデータがありません" in result.output

    def test_info_shows_metadata(self, tmp_path: Path) -> None:
        """Test that info displays metadata."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create metadata
        conn = get_connection(str(db_path))
        initialize_db(conn)
        from genglossary.db.metadata_repository import upsert_metadata

        with transaction(conn):
            upsert_metadata(conn, "./docs", "ollama", "llama3.2")
        conn.close()

        result = runner.invoke(db, ["info", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "./docs" in result.output
        assert "ollama" in result.output
        assert "llama3.2" in result.output


class TestDbTermsList:
    """Test db terms list command."""

    def test_terms_list_shows_no_terms_message(self, tmp_path: Path) -> None:
        """Test that terms list shows message when no terms exist."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        result = runner.invoke(db, ["terms", "list", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "用語がありません" in result.output

    def test_terms_list_shows_terms(self, tmp_path: Path) -> None:
        """Test that terms list displays terms."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create terms
        conn = get_connection(str(db_path))
        initialize_db(conn)
        with transaction(conn):
            create_term(conn, "量子コンピュータ", "technical_term")
            create_term(conn, "量子ビット", "technical_term")
        conn.close()

        result = runner.invoke(db, ["terms", "list", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "量子コンピュータ" in result.output
        assert "量子ビット" in result.output


class TestDbTermsShow:
    """Test db terms show command."""

    def test_terms_show_displays_term_details(self, tmp_path: Path) -> None:
        """Test that terms show displays term details."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create a term
        conn = get_connection(str(db_path))
        initialize_db(conn)
        with transaction(conn):
            term_id = create_term(conn, "量子コンピュータ", "technical_term")
        conn.close()

        result = runner.invoke(
            db, ["terms", "show", str(term_id), "--db-path", str(db_path)]
        )

        assert result.exit_code == 0
        assert f"Term #{term_id}" in result.output
        assert "量子コンピュータ" in result.output
        assert "technical_term" in result.output

    def test_terms_show_nonexistent_term(self, tmp_path: Path) -> None:
        """Test that terms show handles nonexistent term ID."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        result = runner.invoke(db, ["terms", "show", "999", "--db-path", str(db_path)])

        assert result.exit_code == 1
        assert "が見つかりません" in result.output


class TestDbTermsUpdate:
    """Test db terms update command."""

    def test_terms_update_updates_term(self, tmp_path: Path) -> None:
        """Test that terms update updates a term."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create a term
        conn = get_connection(str(db_path))
        initialize_db(conn)
        with transaction(conn):
            term_id = create_term(conn, "量子コンピュータ", "technical_term")
        conn.close()

        result = runner.invoke(
            db,
            [
                "terms",
                "update",
                str(term_id),
                "--text",
                "量子計算機",
                "--category",
                "updated_category",
                "--db-path",
                str(db_path),
            ],
        )

        assert result.exit_code == 0
        assert "更新しました" in result.output

        # Verify update
        conn = get_connection(str(db_path))
        from genglossary.db.term_repository import get_term

        term = get_term(conn, term_id)
        conn.close()

        assert term is not None
        assert term["term_text"] == "量子計算機"
        assert term["category"] == "updated_category"


class TestDbTermsDelete:
    """Test db terms delete command."""

    def test_terms_delete_deletes_term(self, tmp_path: Path) -> None:
        """Test that terms delete deletes a term."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create a term
        conn = get_connection(str(db_path))
        initialize_db(conn)
        with transaction(conn):
            term_id = create_term(conn, "量子コンピュータ", "technical_term")
        conn.close()

        result = runner.invoke(
            db, ["terms", "delete", str(term_id), "--db-path", str(db_path)]
        )

        assert result.exit_code == 0
        assert "削除しました" in result.output

        # Verify deletion
        conn = get_connection(str(db_path))
        from genglossary.db.term_repository import get_term

        term = get_term(conn, term_id)
        conn.close()

        assert term is None


class TestDbTermsImport:
    """Test db terms import command."""

    def test_terms_import_imports_terms(self, tmp_path: Path) -> None:
        """Test that terms import imports terms from a file."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        # Create import file
        import_file = tmp_path / "terms.txt"
        import_file.write_text("量子コンピュータ\n量子ビット\nキュービット\n")

        result = runner.invoke(
            db,
            [
                "terms",
                "import",
                "--file",
                str(import_file),
                "--db-path",
                str(db_path),
            ],
        )

        assert result.exit_code == 0
        assert "3件の用語をインポートしました" in result.output

        # Verify import
        conn = get_connection(str(db_path))
        from genglossary.db.term_repository import list_all_terms

        terms = list_all_terms(conn)
        conn.close()

        assert len(terms) == 3
        assert terms[0]["term_text"] == "量子コンピュータ"
        assert terms[1]["term_text"] == "量子ビット"
        assert terms[2]["term_text"] == "キュービット"


class TestDbProvisionalList:
    """Test db provisional list command."""

    def test_provisional_list_shows_terms(self, tmp_path: Path) -> None:
        """Test that provisional list displays terms."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create provisional terms
        conn = get_connection(str(db_path))
        initialize_db(conn)

        from genglossary.db.provisional_repository import create_provisional_term
        from genglossary.models.term import TermOccurrence

        with transaction(conn):
            occurrences = [
                TermOccurrence(
                    document_path="/path/to/doc.txt", line_number=1, context="Context"
                )
            ]
            create_provisional_term(
                conn, "量子コンピュータ", "定義", 0.95, occurrences
            )
        conn.close()

        result = runner.invoke(
            db, ["provisional", "list", "--db-path", str(db_path)]
        )

        assert result.exit_code == 0
        assert "量子コンピュータ" in result.output


class TestDbRefinedList:
    """Test db refined list command."""

    def test_refined_list_shows_terms(self, tmp_path: Path) -> None:
        """Test that refined list displays terms."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database and create refined terms
        conn = get_connection(str(db_path))
        initialize_db(conn)

        from genglossary.db.refined_repository import create_refined_term
        from genglossary.models.term import TermOccurrence

        with transaction(conn):
            occurrences = [
                TermOccurrence(
                    document_path="/path/to/doc.txt", line_number=1, context="Context"
                )
            ]
            create_refined_term(
                conn, "量子コンピュータ", "定義", 0.98, occurrences
            )
        conn.close()

        result = runner.invoke(
            db, ["refined", "list", "--db-path", str(db_path)]
        )

        assert result.exit_code == 0
        assert "量子コンピュータ" in result.output


class TestDbRefinedExportMd:
    """Test db refined export-md command."""

    def test_refined_export_md_creates_file(self, tmp_path: Path) -> None:
        """Test that refined export-md creates a markdown file."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"
        output_path = tmp_path / "glossary.md"

        # Initialize database and create refined terms
        conn = get_connection(str(db_path))
        initialize_db(conn)

        from genglossary.db.refined_repository import create_refined_term
        from genglossary.models.term import TermOccurrence

        with transaction(conn):
            occurrences = [
                TermOccurrence(
                    document_path="/path/to/doc.txt", line_number=1, context="Context"
                )
            ]
            create_refined_term(
                conn, "量子コンピュータ", "量子力学の原理を利用したコンピュータ", 0.98, occurrences
            )
        conn.close()

        result = runner.invoke(
            db,
            [
                "refined",
                "export-md",
                "--output",
                str(output_path),
                "--db-path",
                str(db_path),
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()
        content = output_path.read_text()
        assert "量子コンピュータ" in content
        assert "量子力学の原理を利用したコンピュータ" in content
