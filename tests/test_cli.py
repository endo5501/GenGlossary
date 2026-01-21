"""Tests for CLI interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from genglossary.cli import main


class TestCLI:
    """Tests for CLI interface."""

    def test_main_exists(self):
        """Test that main function exists and is callable."""
        assert callable(main)

    def test_help_option(self):
        """Test that --help option works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "GenGlossary" in result.output or "glossary" in result.output.lower()

    def test_version_option(self):
        """Test that --version option works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_generate_command_help(self):
        """Test that generate command help works."""
        runner = CliRunner()
        result = runner.invoke(main, ["generate", "--help"])

        assert result.exit_code == 0
        assert "generate" in result.output.lower()

    def test_generate_with_default_options(self, tmp_path: Path):
        """Test generate command with default options."""
        runner = CliRunner()

        # Create dummy input directory
        input_dir = tmp_path / "target_docs"
        input_dir.mkdir()
        (input_dir / "test.md").write_text("# Test Document\n\nSome content.")

        output_file = tmp_path / "output" / "glossary.md"

        with patch("genglossary.cli.generate_glossary") as mock_generate:
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            mock_generate.assert_called_once()

    def test_generate_with_input_option(self, tmp_path: Path):
        """Test generate command with --input option."""
        runner = CliRunner()
        input_dir = tmp_path / "custom_docs"
        input_dir.mkdir()

        with patch("genglossary.cli.generate_glossary"):
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(tmp_path / "out.md"),
                ],
            )

            assert result.exit_code == 0

    def test_generate_with_output_option(self, tmp_path: Path):
        """Test generate command with --output option."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()
        output_file = tmp_path / "custom_output.md"

        with patch("genglossary.cli.generate_glossary"):
            result = runner.invoke(
                main,
                ["generate", "--input", str(input_dir), "--output", str(output_file)],
            )

            assert result.exit_code == 0

    def test_generate_with_model_option(self, tmp_path: Path):
        """Test generate command with --model option."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()

        with patch("genglossary.cli.generate_glossary") as mock_generate:
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(tmp_path / "out.md"),
                    "--model",
                    "llama3.2",
                ],
            )

            assert result.exit_code == 0
            # Verify model was passed to config or function
            assert mock_generate.called

    def test_generate_with_verbose_option(self, tmp_path: Path):
        """Test generate command with --verbose option."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()

        with patch("genglossary.cli.generate_glossary"):
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(tmp_path / "out.md"),
                    "--verbose",
                ],
            )

            assert result.exit_code == 0

    def test_generate_missing_input_directory(self, tmp_path: Path):
        """Test generate command with non-existent input directory."""
        runner = CliRunner()
        missing_dir = tmp_path / "nonexistent"

        result = runner.invoke(
            main,
            [
                "generate",
                "--input",
                str(missing_dir),
                "--output",
                str(tmp_path / "out.md"),
            ],
        )

        # Should fail or show error message
        assert result.exit_code != 0 or "存在しません" in result.output or "not exist" in result.output

    def test_generate_error_handling(self, tmp_path: Path):
        """Test that errors during generation are handled gracefully."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()

        with patch("genglossary.cli.generate_glossary", side_effect=Exception("Test error")):
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(tmp_path / "out.md"),
                ],
            )

            # Should show error message
            assert result.exit_code != 0
            assert "エラー" in result.output or "error" in result.output.lower()

    def test_generate_success_message(self, tmp_path: Path):
        """Test that success message is displayed after generation."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()
        output_file = tmp_path / "glossary.md"

        with patch("genglossary.cli.generate_glossary"):
            result = runner.invoke(
                main,
                ["generate", "--input", str(input_dir), "--output", str(output_file)],
            )

            assert result.exit_code == 0
            # Should show success message
            assert (
                "完了" in result.output
                or "成功" in result.output
                or "success" in result.output.lower()
                or "complete" in result.output.lower()
            )

    def test_generate_shows_progress(self, tmp_path: Path):
        """Test that generate command shows progress information."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()

        with patch("genglossary.cli.generate_glossary"):
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(tmp_path / "out.md"),
                ],
            )

            assert result.exit_code == 0
            # Output should contain some progress information
            assert len(result.output) > 0

    def test_generate_with_default_db_path(self, tmp_path: Path):
        """Test that generate command uses default db_path when not specified."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()
        output_file = tmp_path / "out.md"

        with patch("genglossary.cli.generate_glossary") as mock_generate:
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            # Verify that generate_glossary was called with default db_path
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args.kwargs["db_path"] == "genglossary.db"

    def test_generate_with_custom_db_path(self, tmp_path: Path):
        """Test that generate command uses custom db_path when specified."""
        runner = CliRunner()
        input_dir = tmp_path / "docs"
        input_dir.mkdir()
        output_file = tmp_path / "out.md"
        custom_db = tmp_path / "custom.db"

        with patch("genglossary.cli.generate_glossary") as mock_generate:
            result = runner.invoke(
                main,
                [
                    "generate",
                    "--input",
                    str(input_dir),
                    "--output",
                    str(output_file),
                    "--db-path",
                    str(custom_db),
                ],
            )

            assert result.exit_code == 0
            # Verify that generate_glossary was called with custom db_path
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args.kwargs["db_path"] == str(custom_db)
