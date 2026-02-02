"""Tests for Ollama API endpoints."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient


@respx.mock
def test_list_models_success(client: TestClient):
    """Test GET /api/ollama/models returns model list."""
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={
                "models": [
                    {"name": "llama2", "size": 3826793677},
                    {"name": "llama3.2", "size": 2019393189},
                ]
            },
        )
    )

    response = client.get("/api/ollama/models")

    assert response.status_code == 200
    data = response.json()
    assert data == {"models": [{"name": "llama2"}, {"name": "llama3.2"}]}


@respx.mock
def test_list_models_with_localhost_port(client: TestClient):
    """Test GET /api/ollama/models with localhost and custom port."""
    respx.get("http://localhost:12345/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={"models": [{"name": "codellama"}]},
        )
    )

    response = client.get(
        "/api/ollama/models", params={"base_url": "http://localhost:12345"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {"models": [{"name": "codellama"}]}


@respx.mock
def test_list_models_with_127_0_0_1(client: TestClient):
    """Test GET /api/ollama/models with 127.0.0.1."""
    respx.get("http://127.0.0.1:11434/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={"models": [{"name": "llama2"}]},
        )
    )

    response = client.get(
        "/api/ollama/models", params={"base_url": "http://127.0.0.1:11434"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {"models": [{"name": "llama2"}]}


@respx.mock
def test_list_models_empty(client: TestClient):
    """Test GET /api/ollama/models returns empty list when no models."""
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(200, json={"models": []})
    )

    response = client.get("/api/ollama/models")

    assert response.status_code == 200
    data = response.json()
    assert data == {"models": []}


@respx.mock
def test_list_models_connection_error(client: TestClient):
    """Test GET /api/ollama/models returns 503 on connection error."""
    respx.get("http://localhost:11434/api/tags").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    response = client.get("/api/ollama/models")

    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Failed to connect to Ollama server"


@respx.mock
def test_list_models_timeout_error(client: TestClient):
    """Test GET /api/ollama/models returns 504 on timeout."""
    respx.get("http://localhost:11434/api/tags").mock(
        side_effect=httpx.TimeoutException("Request timeout")
    )

    response = client.get("/api/ollama/models")

    assert response.status_code == 504
    data = response.json()
    assert data["detail"] == "Ollama server timeout"


def test_list_models_invalid_url_format(client: TestClient):
    """Test GET /api/ollama/models returns 400 for invalid URL."""
    response = client.get("/api/ollama/models", params={"base_url": "not-a-valid-url"})

    assert response.status_code == 400
    data = response.json()
    assert "http" in data["detail"].lower() or "scheme" in data["detail"].lower()


def test_list_models_ssrf_protection_remote_host(client: TestClient):
    """Test GET /api/ollama/models blocks remote hosts (SSRF protection)."""
    response = client.get(
        "/api/ollama/models", params={"base_url": "http://remote-server:11434"}
    )

    assert response.status_code == 400
    data = response.json()
    assert "localhost" in data["detail"].lower()


def test_list_models_ssrf_protection_private_ip(client: TestClient):
    """Test GET /api/ollama/models blocks private IPs (SSRF protection)."""
    response = client.get(
        "/api/ollama/models", params={"base_url": "http://192.168.1.1:11434"}
    )

    assert response.status_code == 400
    data = response.json()
    assert "localhost" in data["detail"].lower()


def test_list_models_ssrf_protection_metadata_ip(client: TestClient):
    """Test GET /api/ollama/models blocks cloud metadata IPs (SSRF protection)."""
    response = client.get(
        "/api/ollama/models", params={"base_url": "http://169.254.169.254/"}
    )

    assert response.status_code == 400


def test_list_models_empty_url(client: TestClient):
    """Test GET /api/ollama/models returns 400 for empty URL."""
    response = client.get("/api/ollama/models", params={"base_url": ""})

    assert response.status_code == 400
    data = response.json()
    assert "empty" in data["detail"].lower()


def test_list_models_whitespace_url(client: TestClient):
    """Test GET /api/ollama/models returns 400 for whitespace-only URL."""
    response = client.get("/api/ollama/models", params={"base_url": "   "})

    assert response.status_code == 400
    data = response.json()
    assert "empty" in data["detail"].lower()
