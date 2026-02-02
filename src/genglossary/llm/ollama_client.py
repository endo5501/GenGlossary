"""Ollama LLM client implementation."""
import time
from typing import Type, TypeVar

import httpx
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient

T = TypeVar("T", bound=BaseModel)


class OllamaClient(BaseLLMClient):
    """Ollama LLM client with retry logic and error handling.

    Implements the BaseLLMClient interface for Ollama API.
    Supports text generation, structured output, and health checks.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """Initialize OllamaClient.

        Args:
            base_url: Base URL for Ollama API.
            model: Model name to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> str:
        """Generate text response from Ollama.

        Args:
            prompt: The input prompt.

        Returns:
            Generated text response.

        Raises:
            httpx.HTTPError: If the request fails after all retries.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        response = self._request_with_retry(url, payload)
        return response.json()["response"]

    def generate_structured(
        self, prompt: str, response_model: Type[T], max_json_retries: int = 3
    ) -> T:
        """Generate structured output from Ollama with JSON parsing retry.

        Args:
            prompt: The input prompt.
            response_model: Pydantic model for response validation.
            max_json_retries: Maximum number of retries for JSON parsing failures.

        Returns:
            Validated response model instance.

        Raises:
            ValueError: If JSON parsing or validation fails after all retries.
            httpx.HTTPError: If the request fails after all retries.
        """
        json_prompt = self._build_json_prompt(prompt, response_model)
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": json_prompt, "stream": False}

        def _generate() -> str:
            response = self._request_with_retry(url, payload)
            return response.json()["response"]

        return self._retry_json_parsing(_generate, response_model, max_json_retries)

    def is_available(self) -> bool:
        """Check if Ollama service is available.

        Returns:
            True if service is available, False otherwise.
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = self.client.get(url)
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[str]:
        """Get list of available models from Ollama server.

        Returns:
            List of model names available on the server.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/api/tags"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]

    def _request_with_retry(self, url: str, payload: dict) -> httpx.Response:
        """Make HTTP request with exponential backoff retry.

        Args:
            url: Request URL.
            payload: Request payload.

        Returns:
            HTTP response.

        Raises:
            httpx.HTTPError: If all retries are exhausted.
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(url, json=payload)
                response.raise_for_status()
                return response
            except httpx.HTTPError:
                if attempt < self.max_retries:
                    sleep_time = 2 ** attempt
                    time.sleep(sleep_time)
                else:
                    raise

        # This should never be reached, but for type safety
        raise httpx.HTTPError("Maximum retries exceeded")

    def close(self) -> None:
        """Close the HTTP client to cancel ongoing requests.

        This can be called from another thread to force-cancel ongoing
        LLM API calls by closing the underlying HTTP connection.
        """
        if hasattr(self, 'client'):
            self.client.close()

    def __del__(self):
        """Clean up HTTP client on deletion."""
        self.close()
