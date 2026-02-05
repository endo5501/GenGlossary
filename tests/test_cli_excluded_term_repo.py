"""Tests for excluded_term_repo being passed to TermExtractor in CLI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from genglossary.cli import main
from genglossary.cli_db import db
from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.models.term import ClassifiedTerm, Term, TermCategory, TermOccurrence


def _create_mock_glossary() -> Glossary:
    """Create a mock glossary for testing."""
    glossary = Glossary()
    glossary.add_term(
        Term(
            name="量子コンピュータ",
            definition="量子力学を利用するコンピュータ",
            confidence=0.95,
            occurrences=[
                TermOccurrence(
                    document_path="test.txt", line_number=1, context="量子コンピュータ"
                )
            ],
        )
    )
    return glossary


class TestCliExcludedTermRepo:
    """Test that CLI passes excluded_term_repo to TermExtractor when DB is enabled."""

    @patch("genglossary.cli.DocumentLoader")
    @patch("genglossary.cli.TermExtractor")
    @patch("genglossary.cli.GlossaryRefiner")
    @patch("genglossary.cli.GlossaryReviewer")
    @patch("genglossary.cli.GlossaryGenerator")
    @patch("genglossary.cli.create_llm_client")
    def test_generate_passes_excluded_term_repo_when_db_enabled(
        self,
        mock_create_client,
        mock_generator_class,
        mock_reviewer_class,
        mock_refiner_class,
        mock_extractor_class,
        mock_loader_class,
        tmp_path: Path,
    ) -> None:
        """Test that generate command passes excluded_term_repo when DB is enabled."""
        runner = CliRunner()
        db_path = tmp_path / "test.db"
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_file = tmp_path / "output" / "glossary.md"

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_create_client.return_value = mock_llm

        # Mock DocumentLoader
        mock_loader = MagicMock()
        mock_loader.load_directory.return_value = [
            Document(file_path=str(input_dir / "test.txt"), content="量子コンピュータは量子力学を利用します。")
        ]
        mock_loader_class.return_value = mock_loader

        mock_extractor = MagicMock()
        mock_extractor.extract_terms.return_value = [
            ClassifiedTerm(term="量子コンピュータ", category=TermCategory.TECHNICAL_TERM),
        ]
        mock_extractor_class.return_value = mock_extractor

        mock_glossary = _create_mock_glossary()

        mock_generator = MagicMock()
        mock_generator.generate.return_value = mock_glossary
        mock_generator_class.return_value = mock_generator

        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = []
        mock_reviewer_class.return_value = mock_reviewer

        mock_refiner = MagicMock()
        mock_refiner.refine.return_value = mock_glossary
        mock_refiner_class.return_value = mock_refiner

        # Run generate with DB enabled
        result = runner.invoke(
            main,
            [
                "generate",
                "--input",
                str(input_dir),
                "--output",
                str(output_file),
                "--db-path",
                str(db_path),
            ],
        )

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                import traceback

                traceback.print_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )

        assert result.exit_code == 0

        # Verify TermExtractor was called with excluded_term_repo
        mock_extractor_class.assert_called_once()
        call_kwargs = mock_extractor_class.call_args.kwargs
        assert "excluded_term_repo" in call_kwargs
        # The connection should not be None when DB is enabled
        assert call_kwargs["excluded_term_repo"] is not None

    @patch("genglossary.cli.DocumentLoader")
    @patch("genglossary.cli.TermExtractor")
    @patch("genglossary.cli.GlossaryRefiner")
    @patch("genglossary.cli.GlossaryReviewer")
    @patch("genglossary.cli.GlossaryGenerator")
    @patch("genglossary.cli.create_llm_client")
    def test_generate_passes_none_when_db_disabled(
        self,
        mock_create_client,
        mock_generator_class,
        mock_reviewer_class,
        mock_refiner_class,
        mock_extractor_class,
        mock_loader_class,
        tmp_path: Path,
    ) -> None:
        """Test that generate command passes excluded_term_repo=None when --no-db."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_file = tmp_path / "output" / "glossary.md"

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_create_client.return_value = mock_llm

        # Mock DocumentLoader
        mock_loader = MagicMock()
        mock_loader.load_directory.return_value = [
            Document(file_path=str(input_dir / "test.txt"), content="量子コンピュータは量子力学を利用します。")
        ]
        mock_loader_class.return_value = mock_loader

        mock_extractor = MagicMock()
        mock_extractor.extract_terms.return_value = ["量子コンピュータ"]
        mock_extractor_class.return_value = mock_extractor

        mock_glossary = _create_mock_glossary()

        mock_generator = MagicMock()
        mock_generator.generate.return_value = mock_glossary
        mock_generator_class.return_value = mock_generator

        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = []
        mock_reviewer_class.return_value = mock_reviewer

        mock_refiner = MagicMock()
        mock_refiner.refine.return_value = mock_glossary
        mock_refiner_class.return_value = mock_refiner

        # Run generate with --no-db
        result = runner.invoke(
            main,
            [
                "generate",
                "--input",
                str(input_dir),
                "--output",
                str(output_file),
                "--no-db",
            ],
        )

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                import traceback

                traceback.print_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )

        assert result.exit_code == 0

        # Verify TermExtractor was called without excluded_term_repo (or with None)
        mock_extractor_class.assert_called_once()
        call_kwargs = mock_extractor_class.call_args.kwargs
        # Either excluded_term_repo is not in kwargs, or it's None
        assert call_kwargs.get("excluded_term_repo") is None


class TestCliDbExcludedTermRepo:
    """Test that CLI DB commands pass excluded_term_repo to TermExtractor."""

    @patch("genglossary.cli_db.TermExtractor")
    @patch("genglossary.cli_db.create_llm_client")
    def test_terms_regenerate_passes_excluded_term_repo(
        self, mock_create_client, mock_extractor_class, tmp_path: Path
    ) -> None:
        """Test that terms regenerate passes excluded_term_repo to TermExtractor."""
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

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                import traceback

                traceback.print_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )

        assert result.exit_code == 0

        # Verify TermExtractor was called with excluded_term_repo
        mock_extractor_class.assert_called_once()
        call_kwargs = mock_extractor_class.call_args.kwargs
        assert "excluded_term_repo" in call_kwargs
        # The connection should not be None
        assert call_kwargs["excluded_term_repo"] is not None
