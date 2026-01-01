"""Ollama LLM client implementation."""
import json
import re
import time
from typing import Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

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

    def generate_structured(self, prompt: str, response_model: Type[T], max_json_retries: int = 3) -> T:
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
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nPlease respond in valid JSON format matching this structure: {response_model.model_json_schema()}"

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": json_prompt,
            "stream": False
        }

        last_error = None

        # Retry JSON parsing up to max_json_retries times
        for attempt in range(max_json_retries):
            response = self._request_with_retry(url, payload)
            response_text = response.json()["response"]

            # Try to parse JSON directly
            try:
                data = json.loads(response_text)
                return response_model(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                # Fallback: extract JSON using regex
                json_match = re.search(r'\{[^{}]*\}', response_text)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                        return response_model(**data)
                    except (json.JSONDecodeError, ValidationError):
                        pass

                last_error = e
                if attempt < max_json_retries - 1:
                    # Wait a bit before retrying
                    time.sleep(0.5)
                    continue

        # All retries exhausted
        raise ValueError(
            f"Failed to parse structured output after {max_json_retries} attempts.\n"
            f"Last error: {last_error}\n"
            f"Response text: {response_text[:500]}"  # Show first 500 chars
        )

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
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(url, json=payload)
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Exponential backoff: 2^attempt seconds
                    sleep_time = 2 ** attempt
                    time.sleep(sleep_time)
                else:
                    # Last attempt failed, raise the exception
                    raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")

    def __del__(self):
        """Clean up HTTP client on deletion."""
        if hasattr(self, 'client'):
            self.client.close()
