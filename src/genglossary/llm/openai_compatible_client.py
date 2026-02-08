"""OpenAI-compatible LLM client implementation."""
import time
from typing import Type, TypeVar

import httpx
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient

T = TypeVar("T", bound=BaseModel)


class OpenAICompatibleClient(BaseLLMClient):
    """OpenAI-compatible API client with retry logic and error handling.

    Supports OpenAI, Azure OpenAI, llama.cpp, LM Studio, and other
    OpenAI-compatible APIs.

    The main difference between providers is the endpoint URL, authentication
    method, and optional API version parameter (for Azure).
    """

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
        max_retries: int = 3,
        api_version: str | None = None,
        max_tokens: int = 4096,
    ):
        """Initialize OpenAICompatibleClient.

        Args:
            base_url: Base URL for the API (without /chat/completions).
            api_key: API key for authentication. Required for OpenAI/Azure.
            model: Model name to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            api_version: Azure OpenAI API version (e.g., "2024-02-15-preview").
            max_tokens: Maximum tokens in response. Some servers (like llama.cpp)
                have low defaults that can truncate responses.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_version = api_version
        self.max_tokens = max_tokens
        self.client = httpx.Client(timeout=timeout)

    @property
    def _endpoint_url(self) -> str:
        """Get the chat completions endpoint URL."""
        return f"{self.base_url}/chat/completions"

    @property
    def _headers(self) -> dict[str, str]:
        """Get request headers including authentication.

        Azure uses "api-key" header, while OpenAI and others use
        "Authorization: Bearer" header.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if "azure" in self.base_url.lower():
                headers["api-key"] = self.api_key
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate(self, prompt: str) -> str:
        """Generate text response from OpenAI-compatible API.

        Args:
            prompt: The input prompt.

        Returns:
            Generated text response.

        Raises:
            httpx.HTTPError: If the request fails after all retries.
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_tokens": self.max_tokens,
        }

        response = self._request_with_retry(payload)
        return response.json()["choices"][0]["message"]["content"]

    def generate_structured(
        self, prompt: str, response_model: Type[T], max_json_retries: int = 3
    ) -> T:
        """Generate structured output from OpenAI-compatible API with JSON parsing retry.

        Uses response_format: {"type": "json_object"} for reliable JSON output.

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
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": json_prompt}],
            "response_format": {"type": "json_object"},
            "stream": False,
            "max_tokens": self.max_tokens,
        }

        def _generate() -> str:
            response = self._request_with_retry(payload)
            return response.json()["choices"][0]["message"]["content"]

        return self._retry_json_parsing(_generate, response_model, max_json_retries)

    def is_available(self) -> bool:
        """Check if the API service is available.

        Attempts to fetch the /models endpoint to verify connectivity.

        Returns:
            True if service is available, False otherwise.
        """
        try:
            url = f"{self.base_url}/models"
            params = {"api-version": self.api_version} if self.api_version else {}
            response = self.client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    def _request_with_retry(self, payload: dict) -> httpx.Response:
        """Make HTTP request with exponential backoff retry.

        Handles rate limits with Retry-After header if present.
        Retries on 429 (rate limit) and 5xx (server errors).
        Does not retry on 401 (authentication error) or 400 (bad request).

        Args:
            payload: Request payload.

        Returns:
            HTTP response.

        Raises:
            httpx.HTTPError: If all retries are exhausted.
        """
        params = {"api-version": self.api_version} if self.api_version else {}

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(
                    self._endpoint_url,
                    json=payload,
                    headers=self._headers,
                    params=params,
                )

                # Handle rate limiting (429) - retry with backoff
                if response.status_code == 429 and attempt < self.max_retries:
                    retry_after = int(response.headers.get("Retry-After", 2**attempt))
                    time.sleep(min(retry_after, 60))  # Cap at 60 seconds
                    continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise

                # Retry on server errors (5xx)
                if e.response.status_code >= 500 and attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                raise

            except httpx.HTTPError:
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                raise

        # This should never be reached, but for type safety
        raise httpx.HTTPError("Maximum retries exceeded")

    def close(self) -> None:
        """Close the HTTP client to cancel ongoing requests.

        This can be called from another thread to force-cancel ongoing
        LLM API calls by closing the underlying HTTP connection.
        """
        if hasattr(self, "client"):
            self.client.close()

    def __del__(self):
        """Clean up HTTP client on deletion."""
        self.close()
