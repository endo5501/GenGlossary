"""LLM client factory."""

from genglossary.config import Config
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.ollama_client import OllamaClient
from genglossary.llm.openai_compatible_client import OpenAICompatibleClient


def create_llm_client(
    provider: str,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = 180.0,
) -> BaseLLMClient:
    """Create LLM client based on provider.

    Args:
        provider: LLM provider ("ollama" or "openai").
        model: Model name (provider-specific default if None).
        base_url: Base URL for the API (optional). Falls back to config default.
        timeout: Request timeout in seconds.

    Returns:
        Configured LLM client instance.

    Raises:
        ValueError: If provider is unknown.
    """
    if provider == "ollama":
        config = Config()
        return OllamaClient(
            base_url=base_url or config.ollama_base_url,
            model=model or "dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
            timeout=timeout,
        )

    if provider == "openai":
        config = Config()
        return OpenAICompatibleClient(
            base_url=base_url or config.openai_base_url,
            api_key=config.openai_api_key,
            model=model or config.openai_model,
            timeout=timeout,
            api_version=config.azure_openai_api_version,
        )

    raise ValueError(f"Unknown provider: {provider}. Must be 'ollama' or 'openai'.")
