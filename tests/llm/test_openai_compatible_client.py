"""Tests for OpenAICompatibleClient implementation."""
import pytest
import httpx
import respx
from pydantic import BaseModel

from genglossary.llm.openai_compatible_client import OpenAICompatibleClient


class SampleResponse(BaseModel):
    """Sample response model for testing."""
    answer: str
    confidence: float


@pytest.fixture
def openai_client():
    """Create OpenAICompatibleClient instance for testing."""
    return OpenAICompatibleClient(
        base_url="http://localhost:8080/v1",
        api_key="test-key",
        model="gpt-4o-mini",
        timeout=30.0,
        max_retries=3
    )


@pytest.fixture
def azure_client():
    """Create Azure OpenAI client instance for testing."""
    return OpenAICompatibleClient(
        base_url="https://test-resource.openai.azure.com",
        api_key="azure-test-key",
        model="gpt-4",
        timeout=30.0,
        max_retries=3,
        api_version="2024-02-15-preview"
    )


class TestInitialization:
    """Test client initialization."""

    def test_initialization_with_defaults(self):
        """Test that client can be initialized with default values."""
        client = OpenAICompatibleClient()
        assert client.base_url == "https://api.openai.com/v1"
        assert client.model == "gpt-4o-mini"
        assert client.timeout == 60.0
        assert client.max_retries == 3
        assert client.api_version is None

    def test_initialization_with_custom_values(self, openai_client):
        """Test that client can be initialized with custom values."""
        assert openai_client.base_url == "http://localhost:8080/v1"
        assert openai_client.api_key == "test-key"
        assert openai_client.model == "gpt-4o-mini"
        assert openai_client.timeout == 30.0
        assert openai_client.max_retries == 3

    def test_initialization_azure_with_api_version(self, azure_client):
        """Test Azure client initialization with api_version."""
        assert azure_client.api_version == "2024-02-15-preview"
        assert "azure" in azure_client.base_url.lower()


class TestGenerate:
    """Test text generation."""

    @respx.mock
    def test_generate_success(self, openai_client):
        """Test successful text generation."""
        respx.post("http://localhost:8080/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "chatcmpl-123",
                    "object": "chat.completion",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "The sky is blue due to Rayleigh scattering."
                        },
                        "finish_reason": "stop"
                    }]
                }
            )
        )

        result = openai_client.generate("Why is the sky blue?")
        assert result == "The sky is blue due to Rayleigh scattering."

    @respx.mock
    def test_generate_with_openai_base_url(self):
        """Test generation with OpenAI's base URL."""
        client = OpenAICompatibleClient(
            base_url="https://api.openai.com/v1",
            api_key="sk-test123",
            model="gpt-4o-mini"
        )

        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {"content": "Hello, world!"}
                    }]
                }
            )
        )

        result = client.generate("Say hello")
        assert result == "Hello, world!"

    @respx.mock
    def test_generate_connection_error(self, openai_client):
        """Test handling of connection errors."""
        respx.post("http://localhost:8080/v1/chat/completions").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(httpx.ConnectError):
            openai_client.generate("test")

    @respx.mock
    def test_generate_timeout_error(self, openai_client):
        """Test handling of timeout errors."""
        respx.post("http://localhost:8080/v1/chat/completions").mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        with pytest.raises(httpx.TimeoutException):
            openai_client.generate("test")


class TestGenerateStructured:
    """Test structured output generation."""

    @respx.mock
    def test_generate_structured_success(self, openai_client):
        """Test successful structured output generation with JSON mode."""
        respx.post("http://localhost:8080/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "content": '{"answer": "The answer is 42", "confidence": 0.95}'
                        }
                    }]
                }
            )
        )

        result = openai_client.generate_structured("What is the answer?", SampleResponse)
        assert isinstance(result, SampleResponse)
        assert result.answer == "The answer is 42"
        assert result.confidence == 0.95

    @respx.mock
    def test_generate_structured_with_fallback_regex(self, openai_client):
        """Test structured output parsing with regex fallback."""
        respx.post("http://localhost:8080/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "content": 'Here is the JSON: {"answer": "test", "confidence": 0.8}'
                        }
                    }]
                }
            )
        )

        result = openai_client.generate_structured("test", SampleResponse)
        assert isinstance(result, SampleResponse)
        assert result.answer == "test"
        assert result.confidence == 0.8

    @respx.mock
    def test_generate_structured_invalid_json(self, openai_client):
        """Test handling of invalid JSON responses."""
        respx.post("http://localhost:8080/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {"content": "This is not valid JSON"}
                    }]
                }
            )
        )

        with pytest.raises(ValueError, match="Failed to parse structured output"):
            openai_client.generate_structured("test", SampleResponse)


class TestRetryLogic:
    """Test retry logic and error handling."""

    @respx.mock
    def test_retry_on_rate_limit(self, openai_client):
        """Test retry logic on 429 rate limit error."""
        route = respx.post("http://localhost:8080/v1/chat/completions")
        route.side_effect = [
            httpx.Response(
                429,
                json={"error": {"message": "Rate limit exceeded"}},
                headers={"Retry-After": "1"}
            ),
            httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Success after retry"}}]}
            )
        ]

        result = openai_client.generate("test")
        assert result == "Success after retry"
        assert route.call_count == 2

    @respx.mock
    def test_retry_on_server_error(self, openai_client):
        """Test retry logic on 5xx server errors."""
        route = respx.post("http://localhost:8080/v1/chat/completions")
        route.side_effect = [
            httpx.Response(500, json={"error": {"message": "Internal server error"}}),
            httpx.Response(503, json={"error": {"message": "Service unavailable"}}),
            httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Success"}}]}
            )
        ]

        result = openai_client.generate("test")
        assert result == "Success"
        assert route.call_count == 3

    @respx.mock
    def test_retry_exhausted(self, openai_client):
        """Test that retries are exhausted after max attempts."""
        route = respx.post("http://localhost:8080/v1/chat/completions")
        route.side_effect = [
            httpx.Response(500, json={"error": {"message": "Error"}}),
            httpx.Response(500, json={"error": {"message": "Error"}}),
            httpx.Response(500, json={"error": {"message": "Error"}}),
            httpx.Response(500, json={"error": {"message": "Error"}}),
        ]

        with pytest.raises(httpx.HTTPStatusError):
            openai_client.generate("test")

        # max_retries=3 means 4 total attempts (initial + 3 retries)
        assert route.call_count == 4

    @respx.mock
    def test_no_retry_on_authentication_error(self, openai_client):
        """Test that 401 authentication errors are not retried."""
        route = respx.post("http://localhost:8080/v1/chat/completions")
        route.mock(
            return_value=httpx.Response(
                401,
                json={"error": {"message": "Invalid API key"}}
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            openai_client.generate("test")

        # Should fail immediately without retries
        assert route.call_count == 1


class TestIsAvailable:
    """Test service availability check."""

    @respx.mock
    def test_is_available_success(self, openai_client):
        """Test is_available when service is up."""
        respx.get("http://localhost:8080/v1/models").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "gpt-4o-mini"}]}
            )
        )

        assert openai_client.is_available() is True

    @respx.mock
    def test_is_available_failure(self, openai_client):
        """Test is_available when service is down."""
        respx.get("http://localhost:8080/v1/models").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        assert openai_client.is_available() is False

    @respx.mock
    def test_is_available_with_auth_error(self, openai_client):
        """Test is_available with authentication error."""
        respx.get("http://localhost:8080/v1/models").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )

        assert openai_client.is_available() is False


class TestAzureOpenAI:
    """Test Azure OpenAI specific features."""

    @respx.mock
    def test_azure_api_version_in_endpoint(self, azure_client):
        """Test that Azure API version is included in endpoint URL."""
        route = respx.post(
            "https://test-resource.openai.azure.com/chat/completions",
            params={"api-version": "2024-02-15-preview"}
        ).mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Azure response"}}]}
            )
        )

        result = azure_client.generate("test")
        assert result == "Azure response"
        assert route.called

    @respx.mock
    def test_azure_authentication_header(self, azure_client):
        """Test that Azure uses api-key header for authentication."""
        route = respx.post(
            "https://test-resource.openai.azure.com/chat/completions"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "test"}}]}
            )
        )

        azure_client.generate("test")

        # Check that api-key header was used
        request = route.calls.last.request
        assert "api-key" in request.headers
        assert request.headers["api-key"] == "azure-test-key"

    @respx.mock
    def test_openai_authentication_header(self, openai_client):
        """Test that non-Azure uses Bearer token for authentication."""
        route = respx.post("http://localhost:8080/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "test"}}]}
            )
        )

        openai_client.generate("test")

        # Check that Authorization Bearer header was used
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-key"


class TestClose:
    """Test resource cleanup."""

    def test_close_closes_http_client(self):
        """Test that close() closes the underlying httpx client."""
        client = OpenAICompatibleClient(
            base_url="http://localhost:8080/v1",
            api_key="test-key",
        )
        client.close()
        assert client.client.is_closed

    def test_close_without_client_attribute(self):
        """Test that close() does not raise when client attribute is missing."""
        client = OpenAICompatibleClient(
            base_url="http://localhost:8080/v1",
            api_key="test-key",
        )
        del client.client
        client.close()  # Should not raise
