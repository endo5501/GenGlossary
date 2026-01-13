"""Base LLM client interface."""
import json
import re
import time
from abc import ABC, abstractmethod
from typing import Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.

    Defines the interface that all LLM client implementations must follow.
    Provides common functionality for JSON parsing and prompt building.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text response from the LLM.

        Args:
            prompt: The input prompt for the LLM.

        Returns:
            The generated text response.
        """
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, response_model: Type[T]) -> T:
        """Generate structured output from the LLM.

        Args:
            prompt: The input prompt for the LLM.
            response_model: Pydantic model class for the expected response structure.

        Returns:
            An instance of the response_model with the LLM's response.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available.

        Returns:
            True if the service is available, False otherwise.
        """
        pass

    # Common helper methods (available to subclasses)

    def _build_json_prompt(self, prompt: str, response_model: Type[T]) -> str:
        """Build JSON-formatted prompt with schema information.

        Args:
            prompt: Original user prompt.
            response_model: Pydantic model for response validation.

        Returns:
            Enhanced prompt requesting JSON format.
        """
        return (
            f"{prompt}\n\n"
            f"Please respond in valid JSON format matching this structure: "
            f"{response_model.model_json_schema()}"
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

    def _retry_json_parsing(
        self,
        generate_fn: Callable[[], str],
        response_model: Type[T],
        max_retries: int = 3,
    ) -> T:
        """Retry JSON parsing with configurable attempts.

        Args:
            generate_fn: Function that generates response text (no args).
            response_model: Pydantic model for validation.
            max_retries: Maximum number of parsing retry attempts.

        Returns:
            Validated response model instance.

        Raises:
            ValueError: If parsing fails after all retries.
        """
        last_error = None
        response_text = ""

        for attempt in range(max_retries):
            response_text = generate_fn()
            parsed_model = self._parse_json_response(response_text, response_model)

            if parsed_model is not None:
                return parsed_model

            last_error = ValueError(f"Failed to parse JSON on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(0.5)

        raise ValueError(
            f"Failed to parse structured output after {max_retries} attempts.\n"
            f"Last error: {last_error}\n"
            f"Response text: {response_text[:500]}"
        )
