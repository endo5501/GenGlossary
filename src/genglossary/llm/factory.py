"""LLM client factory."""

from genglossary.config import Config
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.debug_logger import LlmDebugLogger
from genglossary.llm.ollama_client import OllamaClient
from genglossary.llm.openai_compatible_client import OpenAICompatibleClient


def create_llm_client(
    provider: str,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = 180.0,
    llm_debug: bool = False,
    debug_dir: str | None = None,
) -> BaseLLMClient:
    """Create LLM client based on provider.

    Args:
        provider: LLM provider ("ollama" or "openai").
        model: Model name (provider-specific default if None).
        base_url: Base URL for the API (optional). Falls back to config default.
        timeout: Request timeout in seconds.
        llm_debug: Enable debug logging of prompts and responses.
        debug_dir: Directory for debug log files (required when llm_debug=True).

    Returns:
        Configured LLM client instance.

    Raises:
        ValueError: If provider is unknown.
    """
    client: BaseLLMClient

    if provider == "ollama":
        config = Config()
        client = OllamaClient(
            base_url=base_url or config.ollama_base_url,
            model=model or "dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
            timeout=timeout,
        )
    elif provider == "openai":
        config = Config()
        client = OpenAICompatibleClient(
            base_url=base_url or config.openai_base_url,
            api_key=config.openai_api_key,
            model=model or config.openai_model,
            timeout=timeout,
            api_version=config.azure_openai_api_version,
        )
    else:
        raise ValueError(
            f"Unknown provider: {provider}. Must be 'ollama' or 'openai'."
        )

    if llm_debug:
        if not debug_dir:
            raise ValueError(
                "debug_dir is required when llm_debug is enabled."
            )
        client._debug_logger = LlmDebugLogger(debug_dir=debug_dir)

    return client
