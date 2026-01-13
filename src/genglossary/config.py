"""Configuration management using Pydantic Settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables and .env file.

    Attributes:
        llm_provider: LLM provider to use (ollama or openai).
        ollama_base_url: Base URL for Ollama API.
        ollama_model: Model name to use with Ollama.
        ollama_timeout: Timeout in seconds for Ollama API calls.
        openai_base_url: Base URL for OpenAI-compatible API.
        openai_api_key: API key for OpenAI-compatible API.
        openai_model: Model name to use with OpenAI-compatible API.
        openai_timeout: Timeout in seconds for OpenAI API calls.
        azure_openai_api_version: Azure OpenAI API version.
        input_dir: Directory containing input documents.
        output_file: Path to output glossary file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    llm_provider: str = Field(
        default="ollama",
        validation_alias="LLM_PROVIDER",
        description="LLM provider to use: 'ollama' or 'openai'",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
        description="Base URL for Ollama API",
    )

    ollama_model: str = Field(
        default="dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
        validation_alias="OLLAMA_MODEL",
        description="Model name to use with Ollama",
    )

    ollama_timeout: int = Field(
        default=120,
        validation_alias="OLLAMA_TIMEOUT",
        description="Timeout in seconds for Ollama API calls",
        gt=0,
    )

    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="OPENAI_BASE_URL",
        description="Base URL for OpenAI-compatible API",
    )

    openai_api_key: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        description="API key for OpenAI-compatible API",
    )

    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="OPENAI_MODEL",
        description="Model name to use with OpenAI-compatible API",
    )

    openai_timeout: int = Field(
        default=60,
        validation_alias="OPENAI_TIMEOUT",
        description="Timeout in seconds for OpenAI API calls",
        gt=0,
    )

    azure_openai_api_version: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_API_VERSION",
        description="Azure OpenAI API version (e.g., '2024-02-15-preview')",
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

    @field_validator("ollama_timeout", "openai_timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate that timeout is positive."""
        if v <= 0:
            raise ValueError("timeout must be positive")
        return v

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is one of the supported values."""
        if v not in ("ollama", "openai"):
            raise ValueError("llm_provider must be 'ollama' or 'openai'")
        return v
