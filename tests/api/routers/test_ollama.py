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
def test_list_models_with_custom_base_url(client: TestClient):
    """Test GET /api/ollama/models with custom base_url parameter."""
    respx.get("http://remote-server:11434/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={"models": [{"name": "codellama"}]},
        )
    )

    response = client.get(
        "/api/ollama/models", params={"base_url": "http://remote-server:11434"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {"models": [{"name": "codellama"}]}


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
    assert "Invalid base URL format" in data["detail"]
