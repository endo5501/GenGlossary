"""Base LLM client interface."""
from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from genglossary.llm.debug_logger import LlmDebugLogger

T = TypeVar("T", bound=BaseModel)


def _wrap_generate(original: Any) -> Any:
    """Wrap a generate method with debug logging."""
    if getattr(original, "_debug_wrapped", False):
        return original

    def wrapped(self: BaseLLMClient, prompt: str, *args: Any, **kwargs: Any) -> str:
        start = time.time()
        result = original(self, prompt, *args, **kwargs)
        duration = time.time() - start
        if self._debug_logger is not None:
            model_name = getattr(self, "model", "unknown")
            self._debug_logger.log(
                model=model_name,
                method="generate",
                request=prompt,
                response=result,
                duration=round(duration, 2),
            )
        return result

    wrapped._debug_wrapped = True  # type: ignore[attr-defined]
    return wrapped


def _wrap_generate_structured(original: Any) -> Any:
    """Wrap a generate_structured method with debug logging."""
    if getattr(original, "_debug_wrapped", False):
        return original

    def wrapped(self: BaseLLMClient, prompt: str, *args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = original(self, prompt, *args, **kwargs)
        duration = time.time() - start
        if self._debug_logger is not None:
            model_name = getattr(self, "model", "unknown")
            response_str = (
                result.model_dump_json(indent=2)
                if isinstance(result, BaseModel)
                else str(result)
            )
            self._debug_logger.log(
                model=model_name,
                method="generate_structured",
                request=prompt,
                response=response_str,
                duration=round(duration, 2),
            )
        return result

    wrapped._debug_wrapped = True  # type: ignore[attr-defined]
    return wrapped


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.

    Defines the interface that all LLM client implementations must follow.
    Provides common functionality for JSON parsing and prompt building.

    Subclasses that override generate() or generate_structured() are
    automatically wrapped with debug logging support via __init_subclass__.
    """

    _debug_logger: LlmDebugLogger | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "generate" in cls.__dict__:
            setattr(cls, "generate", _wrap_generate(cls.__dict__["generate"]))
        if "generate_structured" in cls.__dict__:
            setattr(
                cls,
                "generate_structured",
                _wrap_generate_structured(cls.__dict__["generate_structured"]),
            )

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

    def close(self) -> None:
        """Close the client and release resources.

        This method can be called from another thread to cancel
        ongoing requests. Default implementation does nothing.
        Subclasses should override to close HTTP connections etc.
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
