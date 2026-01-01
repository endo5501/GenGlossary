"""Tests for Config management."""

import os
from pathlib import Path

import pytest

from genglossary.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_config_initialization(self):
        """Test that Config can be initialized with defaults."""
        config = Config()
        assert config is not None

    def test_default_ollama_base_url(self):
        """Test default Ollama base URL."""
        config = Config()
        assert config.ollama_base_url == "http://localhost:11434"

    def test_default_ollama_model(self):
        """Test default Ollama model."""
        config = Config()
        assert config.ollama_model == "llama2"

    def test_default_ollama_timeout(self):
        """Test default Ollama timeout."""
        config = Config()
        assert config.ollama_timeout == 120

    def test_default_input_dir(self):
        """Test default input directory."""
        config = Config()
        assert config.input_dir == "./target_docs"

    def test_default_output_file(self):
        """Test default output file."""
        config = Config()
        assert config.output_file == "./output/glossary.md"

    def test_config_from_env_ollama_base_url(self, monkeypatch: pytest.MonkeyPatch):
        """Test loading Ollama base URL from environment variable."""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:8080")
        config = Config()
        assert config.ollama_base_url == "http://custom:8080"

    def test_config_from_env_ollama_model(self, monkeypatch: pytest.MonkeyPatch):
        """Test loading Ollama model from environment variable."""
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
        config = Config()
        assert config.ollama_model == "llama3.2"

    def test_config_from_env_ollama_timeout(self, monkeypatch: pytest.MonkeyPatch):
        """Test loading Ollama timeout from environment variable."""
        monkeypatch.setenv("OLLAMA_TIMEOUT", "300")
        config = Config()
        assert config.ollama_timeout == 300

    def test_config_from_env_input_dir(self, monkeypatch: pytest.MonkeyPatch):
        """Test loading input directory from environment variable."""
        monkeypatch.setenv("GENGLOSSARY_INPUT_DIR", "/custom/input")
        config = Config()
        assert config.input_dir == "/custom/input"

    def test_config_from_env_output_file(self, monkeypatch: pytest.MonkeyPatch):
        """Test loading output file from environment variable."""
        monkeypatch.setenv("GENGLOSSARY_OUTPUT_FILE", "/custom/output.md")
        config = Config()
        assert config.output_file == "/custom/output.md"

    def test_config_from_dotenv_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Test loading configuration from .env file."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
OLLAMA_BASE_URL=http://dotenv:9999
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=200
GENGLOSSARY_INPUT_DIR=./docs
GENGLOSSARY_OUTPUT_FILE=./out/glossary.md
"""
        )

        # Change to temp directory so .env is found
        monkeypatch.chdir(tmp_path)

        # Load config (should pick up .env)
        config = Config()

        assert config.ollama_base_url == "http://dotenv:9999"
        assert config.ollama_model == "llama3.2"
        assert config.ollama_timeout == 200
        assert config.input_dir == "./docs"
        assert config.output_file == "./out/glossary.md"

    def test_env_variables_override_dotenv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Test that environment variables override .env file."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("OLLAMA_MODEL=llama2\n")

        monkeypatch.chdir(tmp_path)

        # Set environment variable (should override .env)
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")

        config = Config()
        assert config.ollama_model == "llama3.2"

    def test_invalid_timeout_type(self, monkeypatch: pytest.MonkeyPatch):
        """Test that invalid timeout type raises validation error."""
        monkeypatch.setenv("OLLAMA_TIMEOUT", "not-a-number")

        with pytest.raises(ValueError):
            Config()

    def test_timeout_must_be_positive(self, monkeypatch: pytest.MonkeyPatch):
        """Test that timeout must be positive."""
        monkeypatch.setenv("OLLAMA_TIMEOUT", "-10")

        with pytest.raises(ValueError):
            Config()

    def test_config_fields_are_readonly_after_init(self):
        """Test that config fields cannot be modified after initialization."""
        config = Config()

        # Pydantic models with frozen=True should raise ValidationError
        with pytest.raises(Exception):  # ValidationError or AttributeError
            config.ollama_model = "new-model"  # type: ignore

    def test_config_with_custom_values(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Test creating config with all custom values."""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:5000")
        monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
        monkeypatch.setenv("OLLAMA_TIMEOUT", "500")
        monkeypatch.setenv("GENGLOSSARY_INPUT_DIR", "/path/to/input")
        monkeypatch.setenv("GENGLOSSARY_OUTPUT_FILE", "/path/to/output.md")

        config = Config()

        assert config.ollama_base_url == "http://custom:5000"
        assert config.ollama_model == "custom-model"
        assert config.ollama_timeout == 500
        assert config.input_dir == "/path/to/input"
        assert config.output_file == "/path/to/output.md"

    def test_config_loads_dotenv_automatically(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Test that Config automatically loads .env file if present."""
        env_file = tmp_path / ".env"
        env_file.write_text("OLLAMA_MODEL=auto-loaded-model\n")

        monkeypatch.chdir(tmp_path)

        config = Config()
        assert config.ollama_model == "auto-loaded-model"

    def test_config_without_dotenv_uses_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Test that Config uses defaults when no .env file exists."""
        # Ensure we're in a directory without .env
        monkeypatch.chdir(tmp_path)

        config = Config()

        assert config.ollama_base_url == "http://localhost:11434"
        assert config.ollama_model == "llama2"
        assert config.ollama_timeout == 120
