"""Base LLM client interface."""
from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.

    Defines the interface that all LLM client implementations must follow.
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
