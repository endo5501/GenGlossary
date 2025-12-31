"""Tests for BaseLLMClient abstract base class."""
import pytest
from typing import Type
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient


class SampleResponse(BaseModel):
    """Sample response model for testing."""
    text: str


def test_base_llm_client_is_abstract():
    """Test that BaseLLMClient cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseLLMClient()


def test_base_llm_client_has_generate_method():
    """Test that BaseLLMClient has abstract generate method."""
    assert hasattr(BaseLLMClient, 'generate')
    assert getattr(BaseLLMClient.generate, '__isabstractmethod__', False)


def test_base_llm_client_has_generate_structured_method():
    """Test that BaseLLMClient has abstract generate_structured method."""
    assert hasattr(BaseLLMClient, 'generate_structured')
    assert getattr(BaseLLMClient.generate_structured, '__isabstractmethod__', False)


def test_base_llm_client_has_is_available_method():
    """Test that BaseLLMClient has abstract is_available method."""
    assert hasattr(BaseLLMClient, 'is_available')
    assert getattr(BaseLLMClient.is_available, '__isabstractmethod__', False)


def test_concrete_implementation_can_be_instantiated():
    """Test that a concrete implementation of BaseLLMClient can be instantiated."""

    class ConcreteLLMClient(BaseLLMClient):
        """Concrete implementation for testing."""

        def generate(self, prompt: str) -> str:
            return "test response"

        def generate_structured(self, prompt: str, response_model: Type[BaseModel]) -> BaseModel:
            return response_model(text="test")

        def is_available(self) -> bool:
            return True

    # Should not raise an error
    client = ConcreteLLMClient()
    assert client.generate("test") == "test response"
    assert client.is_available() is True
