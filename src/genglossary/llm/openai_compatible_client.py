"""OpenAI-compatible LLM client implementation."""
import json
import re
import time
from typing import Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

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
    ):
        """Initialize OpenAICompatibleClient.

        Args:
            base_url: Base URL for the API (without /chat/completions).
            api_key: API key for authentication. Required for OpenAI/Azure.
            model: Model name to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            api_version: Azure OpenAI API version (e.g., "2024-02-15-preview").
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_version = api_version
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
        json_prompt = f"{prompt}\n\nPlease respond in valid JSON format matching this structure: {response_model.model_json_schema()}"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": json_prompt}],
            "response_format": {"type": "json_object"},
        }

        last_error = None
        response_text = ""

        for attempt in range(max_json_retries):
            response = self._request_with_retry(payload)
            response_text = response.json()["choices"][0]["message"]["content"]

            parsed_model = self._parse_json_response(response_text, response_model)
            if parsed_model is not None:
                return parsed_model

            last_error = ValueError(f"Failed to parse JSON on attempt {attempt + 1}")
            if attempt < max_json_retries - 1:
                time.sleep(0.5)

        raise ValueError(
            f"Failed to parse structured output after {max_json_retries} attempts.\n"
            f"Last error: {last_error}\n"
            f"Response text: {response_text[:500]}"
        )

    def _parse_json_response(
        self, response_text: str, response_model: Type[T]
    ) -> T | None:
        """Parse JSON response with fallback to regex extraction.

        Args:
            response_text: Raw text response from LLM.
            response_model: Pydantic model for validation.

        Returns:
            Validated model instance if parsing succeeds, None otherwise.
        """
        # Try direct JSON parsing
        try:
            data = json.loads(response_text)
            return response_model(**data)
        except (json.JSONDecodeError, ValidationError):
            pass

        # Fallback: extract JSON using regex
        json_match = re.search(r"\{[^{}]*\}", response_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return response_model(**data)
            except (json.JSONDecodeError, ValidationError):
                pass

        return None

    def is_available(self) -> bool:
        """Check if the API service is available.

        Attempts to fetch the /models endpoint to verify connectivity.

        Returns:
            True if service is available, False otherwise.
        """
        try:
            url = f"{self.base_url}/models"
            params = {}
            if self.api_version:
                params["api-version"] = self.api_version

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
        params = {}
        if self.api_version:
            params["api-version"] = self.api_version

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(
                    self._endpoint_url,
                    json=payload,
                    headers=self._headers,
                    params=params,
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    if attempt < self.max_retries:
                        retry_after = int(
                            response.headers.get("Retry-After", 2**attempt)
                        )
                        time.sleep(min(retry_after, 60))  # Cap at 60 seconds
                        continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise

                # Retry on server errors (5xx)
                if attempt < self.max_retries and e.response.status_code >= 500:
                    time.sleep(2**attempt)
                    continue
                raise

            except httpx.HTTPError:
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                else:
                    raise

        # This should never be reached, but for type safety
        raise httpx.HTTPError("Maximum retries exceeded")

    def __del__(self):
        """Clean up HTTP client on deletion."""
        if hasattr(self, "client"):
            self.client.close()
