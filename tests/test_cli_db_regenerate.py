"""Tests for CLI DB regenerate commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from genglossary.cli_db import db
from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import create_term, list_all_terms
from genglossary.db.provisional_repository import list_all_provisional
from genglossary.db.issue_repository import list_all_issues
from genglossary.db.refined_repository import list_all_refined
from genglossary.models.term import ClassifiedTerm, TermCategory


class TestTermsRegenerate:
    """Test db terms regenerate command."""

    @patch("genglossary.cli_db.TermExtractor")
    @patch("genglossary.cli_db.create_llm_client")
    def test_regenerate_extracts_and_saves_terms(
        self, mock_create_client, mock_extractor_class, tmp_path: Path
    ) -> None:
        """Test that terms regenerate extracts terms and saves to DB."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create test document
        (input_dir / "test.txt").write_text("量子コンピュータは量子力学を利用します。")

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_create_client.return_value = mock_llm

        mock_extractor = MagicMock()
        mock_extractor.extract_terms.return_value = [
            ClassifiedTerm(term="量子コンピュータ", category=TermCategory.TECHNICAL_TERM),
            ClassifiedTerm(term="量子力学", category=TermCategory.TECHNICAL_TERM),
        ]
        mock_extractor_class.return_value = mock_extractor

        # Run regenerate
        result = runner.invoke(
            db,
            [
                "terms",
                "regenerate",
                "--input",
                str(input_dir),
                "--db-path",
                str(db_path),
            ],
        )

        assert result.exit_code == 0
        assert "2件の用語を保存しました" in result.output

        # Verify terms were saved
        conn = get_connection(str(db_path))
        terms = list_all_terms(conn)
        conn.close()

        assert len(terms) == 2
        assert terms[0]["term_text"] == "量子コンピュータ"
        assert terms[1]["term_text"] == "量子力学"

    @patch("genglossary.cli_db.TermExtractor")
    @patch("genglossary.cli_db.create_llm_client")
    def test_regenerate_clears_existing_terms(
        self, mock_create_client, mock_extractor_class, tmp_path: Path
    ) -> None:
        """Test that regenerate clears existing terms before extracting."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create test document
        (input_dir / "test.txt").write_text("新しい用語")

        # Initialize database with existing term
        conn = get_connection(str(db_path))
        initialize_db(conn)
        create_term(conn, "古い用語")
        conn.close()

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_create_client.return_value = mock_llm

        mock_extractor = MagicMock()
        mock_extractor.extract_terms.return_value = [
            ClassifiedTerm(term="新しい用語", category=TermCategory.TECHNICAL_TERM),
        ]
        mock_extractor_class.return_value = mock_extractor

        # Run regenerate
        result = runner.invoke(
            db,
            [
                "terms",
                "regenerate",
                "--input",
                str(input_dir),
                "--db-path",
                str(db_path),
            ],
        )

        assert result.exit_code == 0

        # Verify only new terms exist
        conn = get_connection(str(db_path))
        terms = list_all_terms(conn)
        conn.close()

        assert len(terms) == 1
        assert terms[0]["term_text"] == "新しい用語"

    def test_regenerate_requires_input_option(self, tmp_path: Path) -> None:
        """Test that regenerate requires --input option."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        # Run without --input
        result = runner.invoke(
            db,
            ["terms", "regenerate", "--db-path", str(db_path)],
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()


class TestProvisionalRegenerate:
    """Test db provisional regenerate command."""

    @patch("genglossary.cli_db.DocumentLoader")
    @patch("genglossary.cli_db.GlossaryGenerator")
    @patch("genglossary.cli_db.create_llm_client")
    def test_regenerate_generates_provisional_glossary(
        self, mock_create_client, mock_generator_class, mock_loader_class, tmp_path: Path
    ) -> None:
        """Test that provisional regenerate generates glossary from terms."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database with terms (with categories)
        conn = get_connection(str(db_path))
        initialize_db(conn)
        create_term(conn, "量子コンピュータ", category="technical_term")
        create_term(conn, "量子力学", category="technical_term")

        # Note: Need to add documents for GlossaryGenerator
        from genglossary.db.document_repository import create_document
        create_document(conn, "/tmp/test.txt", "abc123")
        conn.close()

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_create_client.return_value = mock_llm

        # Mock DocumentLoader
        from genglossary.models.document import Document
        mock_loader = MagicMock()
        mock_document = Document(file_path="/tmp/test.txt", content="量子コンピュータのテスト")
        mock_loader.load_file.return_value = mock_document
        mock_loader_class.return_value = mock_loader

        # Mock Glossary object
        from genglossary.models.glossary import Glossary
        from genglossary.models.term import Term, TermOccurrence

        mock_glossary = Glossary()
        term1 = Term(
            name="量子コンピュータ",
            definition="量子力学を利用するコンピュータ",
            confidence=0.95,
            occurrences=[TermOccurrence(document_path="/tmp/test.txt", line_number=1, context="量子コンピュータ")]
        )
        mock_glossary.add_term(term1)

        mock_generator = MagicMock()
        mock_generator.generate.return_value = mock_glossary
        mock_generator_class.return_value = mock_generator

        # Run regenerate
        result = runner.invoke(
            db,
            ["provisional", "regenerate", "--db-path", str(db_path)],
        )

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                import traceback
                print(f"Exception: {result.exception}")
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        assert result.exit_code == 0
        assert "1件の暫定用語を保存しました" in result.output

        # Verify provisional terms were saved
        conn = get_connection(str(db_path))
        provisional = list_all_provisional(conn)
        conn.close()

        assert len(provisional) == 1
        assert provisional[0]["term_name"] == "量子コンピュータ"


class TestIssuesRegenerate:
    """Test db issues regenerate command."""

    @patch("genglossary.cli_db.GlossaryReviewer")
    @patch("genglossary.cli_db.create_llm_client")
    def test_regenerate_reviews_provisional_glossary(
        self, mock_create_client, mock_reviewer_class, tmp_path: Path
    ) -> None:
        """Test that issues regenerate reviews provisional glossary."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database with provisional terms
        conn = get_connection(str(db_path))
        initialize_db(conn)

        from genglossary.db.provisional_repository import create_provisional_term
        from genglossary.models.term import TermOccurrence

        create_provisional_term(
            conn,
            "量子コンピュータ",
            "定義が不明瞭",
            0.5,
            [TermOccurrence(document_path="/tmp/test.txt", line_number=1, context="text")]
        )
        conn.close()

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_create_client.return_value = mock_llm

        from genglossary.models.glossary import GlossaryIssue

        mock_issues = [
            GlossaryIssue(
                term_name="量子コンピュータ",
                issue_type="unclear",
                description="定義が不明瞭",
                should_exclude=False,
                exclusion_reason=None
            )
        ]

        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_issues
        mock_reviewer_class.return_value = mock_reviewer

        # Run regenerate
        result = runner.invoke(
            db,
            ["issues", "regenerate", "--db-path", str(db_path)],
        )

        assert result.exit_code == 0
        assert "1件の問題を保存しました" in result.output

        # Verify issues were saved
        conn = get_connection(str(db_path))
        issues = list_all_issues(conn)
        conn.close()

        assert len(issues) == 1
        assert issues[0]["term_name"] == "量子コンピュータ"


class TestRefinedRegenerate:
    """Test db refined regenerate command."""

    @patch("genglossary.cli_db.DocumentLoader")
    @patch("genglossary.cli_db.GlossaryRefiner")
    @patch("genglossary.cli_db.create_llm_client")
    def test_regenerate_refines_glossary(
        self, mock_create_client, mock_refiner_class, mock_loader_class, tmp_path: Path
    ) -> None:
        """Test that refined regenerate refines glossary based on issues."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"

        # Initialize database with provisional terms and issues
        conn = get_connection(str(db_path))
        initialize_db(conn)

        from genglossary.db.provisional_repository import create_provisional_term
        from genglossary.db.issue_repository import create_issue
        from genglossary.db.document_repository import create_document
        from genglossary.models.term import TermOccurrence

        create_provisional_term(
            conn,
            "量子コンピュータ",
            "定義が不明瞭",
            0.5,
            [TermOccurrence(document_path="/tmp/test.txt", line_number=1, context="text")]
        )
        create_issue(
            conn,
            "量子コンピュータ",
            "unclear",
            "定義を改善する必要がある"
        )
        create_document(conn, "/tmp/test.txt", "abc123")
        conn.close()

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_create_client.return_value = mock_llm

        # Mock DocumentLoader
        from genglossary.models.document import Document
        mock_loader = MagicMock()
        mock_document = Document(file_path="/tmp/test.txt", content="量子コンピュータのテスト")
        mock_loader.load_file.return_value = mock_document
        mock_loader_class.return_value = mock_loader

        from genglossary.models.glossary import Glossary
        from genglossary.models.term import Term

        mock_glossary = Glossary()
        refined_term = Term(
            name="量子コンピュータ",
            definition="量子力学の原理を利用して計算を行うコンピュータ",
            confidence=0.98,
            occurrences=[TermOccurrence(document_path="/tmp/test.txt", line_number=1, context="text")]
        )
        mock_glossary.add_term(refined_term)

        mock_refiner = MagicMock()
        mock_refiner.refine.return_value = mock_glossary
        mock_refiner_class.return_value = mock_refiner

        # Run regenerate
        result = runner.invoke(
            db,
            ["refined", "regenerate", "--db-path", str(db_path)],
        )

        assert result.exit_code == 0
        assert "1件の最終用語を保存しました" in result.output

        # Verify refined terms were saved
        conn = get_connection(str(db_path))
        refined = list_all_refined(conn)
        conn.close()

        assert len(refined) == 1
        assert refined[0]["term_name"] == "量子コンピュータ"
        assert refined[0]["confidence"] == 0.98
