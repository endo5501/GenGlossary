"""Tests for OllamaClient implementation."""
import pytest
import httpx
import respx
from pydantic import BaseModel

from genglossary.llm.ollama_client import OllamaClient


class SampleResponse(BaseModel):
    """Sample response model for testing."""
    answer: str
    confidence: float


@pytest.fixture
def ollama_client():
    """Create OllamaClient instance for testing."""
    return OllamaClient(
        base_url="http://localhost:11434",
        model="llama2",
        timeout=30.0,
        max_retries=3
    )


@respx.mock
def test_generate_success(ollama_client):
    """Test successful text generation."""
    # Mock the Ollama API response
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "llama2",
                "response": "The sky is blue due to Rayleigh scattering.",
                "done": True
            }
        )
    )

    result = ollama_client.generate("Why is the sky blue?")
    assert result == "The sky is blue due to Rayleigh scattering."


@respx.mock
def test_generate_structured_success(ollama_client):
    """Test successful structured output generation."""
    # Mock the Ollama API response with JSON
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "llama2",
                "response": '{"answer": "42", "confidence": 0.95}',
                "done": True
            }
        )
    )

    result = ollama_client.generate_structured(
        "What is the answer?",
        SampleResponse
    )
    assert isinstance(result, SampleResponse)
    assert result.answer == "42"
    assert result.confidence == 0.95


@respx.mock
def test_generate_connection_error(ollama_client):
    """Test handling of connection errors."""
    # Mock connection error
    respx.post("http://localhost:11434/api/generate").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with pytest.raises(httpx.ConnectError):
        ollama_client.generate("test prompt")


@respx.mock
def test_generate_timeout_error(ollama_client):
    """Test handling of timeout errors."""
    # Mock timeout error
    respx.post("http://localhost:11434/api/generate").mock(
        side_effect=httpx.TimeoutException("Request timeout")
    )

    with pytest.raises(httpx.TimeoutException):
        ollama_client.generate("test prompt")


@respx.mock
def test_generate_structured_invalid_json(ollama_client):
    """Test handling of invalid JSON in structured output."""
    # Mock response with invalid JSON
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "llama2",
                "response": "This is not valid JSON",
                "done": True
            }
        )
    )

    with pytest.raises(ValueError):
        ollama_client.generate_structured("test prompt", SampleResponse)


@respx.mock
def test_retry_logic_with_exponential_backoff(ollama_client):
    """Test retry logic with exponential backoff."""
    # First two requests fail, third succeeds
    route = respx.post("http://localhost:11434/api/generate")
    route.side_effect = [
        httpx.Response(500, json={"error": "Internal Server Error"}),
        httpx.Response(500, json={"error": "Internal Server Error"}),
        httpx.Response(
            200,
            json={
                "model": "llama2",
                "response": "Success after retries",
                "done": True
            }
        )
    ]

    result = ollama_client.generate("test prompt")
    assert result == "Success after retries"
    assert route.call_count == 3


@respx.mock
def test_retry_exhausted():
    """Test that retries are exhausted after max attempts."""
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama2",
        timeout=30.0,
        max_retries=2
    )

    # All requests fail
    route = respx.post("http://localhost:11434/api/generate")
    route.mock(return_value=httpx.Response(500, json={"error": "Server Error"}))

    with pytest.raises(httpx.HTTPStatusError):
        client.generate("test prompt")

    # Should have tried initial + 2 retries = 3 times
    assert route.call_count == 3


@respx.mock
def test_is_available_success(ollama_client):
    """Test is_available when service is up."""
    # Mock the /api/tags endpoint for health check
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={"models": [{"name": "llama2"}]}
        )
    )

    assert ollama_client.is_available() is True


@respx.mock
def test_is_available_failure(ollama_client):
    """Test is_available when service is down."""
    # Mock connection error
    respx.get("http://localhost:11434/api/tags").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    assert ollama_client.is_available() is False


@respx.mock
def test_generate_structured_with_fallback_regex(ollama_client):
    """Test structured output with regex fallback for embedded JSON."""
    # Mock response with JSON embedded in text
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "llama2",
                "response": 'Here is the answer: {"answer": "test", "confidence": 0.8} Hope this helps!',
                "done": True
            }
        )
    )

    result = ollama_client.generate_structured("test prompt", SampleResponse)
    assert isinstance(result, SampleResponse)
    assert result.answer == "test"
    assert result.confidence == 0.8


@respx.mock
def test_list_models_success(ollama_client):
    """Test successful model listing."""
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={
                "models": [
                    {"name": "llama2", "size": 3826793677},
                    {"name": "llama3.2", "size": 2019393189},
                    {"name": "codellama", "size": 3791811617},
                ]
            }
        )
    )

    result = ollama_client.list_models()
    assert result == ["llama2", "llama3.2", "codellama"]


@respx.mock
def test_list_models_empty(ollama_client):
    """Test model listing when no models are available."""
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(200, json={"models": []})
    )

    result = ollama_client.list_models()
    assert result == []


@respx.mock
def test_list_models_connection_error(ollama_client):
    """Test model listing when connection fails."""
    respx.get("http://localhost:11434/api/tags").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with pytest.raises(httpx.ConnectError):
        ollama_client.list_models()


@respx.mock
def test_list_models_timeout_error(ollama_client):
    """Test model listing when request times out."""
    respx.get("http://localhost:11434/api/tags").mock(
        side_effect=httpx.TimeoutException("Request timeout")
    )

    with pytest.raises(httpx.TimeoutException):
        ollama_client.list_models()
