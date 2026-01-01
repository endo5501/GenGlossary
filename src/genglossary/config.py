"""Configuration management using Pydantic Settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables and .env file.

    Attributes:
        ollama_base_url: Base URL for Ollama API.
        ollama_model: Model name to use with Ollama.
        ollama_timeout: Timeout in seconds for Ollama API calls.
        input_dir: Directory containing input documents.
        output_file: Path to output glossary file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
        description="Base URL for Ollama API",
    )

    ollama_model: str = Field(
        default="llama2",
        validation_alias="OLLAMA_MODEL",
        description="Model name to use with Ollama",
    )

    ollama_timeout: int = Field(
        default=120,
        validation_alias="OLLAMA_TIMEOUT",
        description="Timeout in seconds for Ollama API calls",
        gt=0,
    )

    input_dir: str = Field(
        default="./target_docs",
        validation_alias="GENGLOSSARY_INPUT_DIR",
        description="Directory containing input documents",
    )

    output_file: str = Field(
        default="./output/glossary.md",
        validation_alias="GENGLOSSARY_OUTPUT_FILE",
        description="Path to output glossary file",
    )

    @field_validator("ollama_timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate that timeout is positive."""
        if v <= 0:
            raise ValueError("ollama_timeout must be positive")
        return v
