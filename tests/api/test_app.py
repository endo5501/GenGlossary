"""Tests for FastAPI application."""

import re
from uuid import UUID

import pytest


def test_health_endpoint_returns_200_and_json(client):
    """Test /health endpoint returns 200 and JSON response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_version_endpoint_returns_package_version(client):
    """Test /version endpoint returns package version."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "genglossary"
    assert "version" in data
    # Version should match semver pattern
    assert re.match(r"\d+\.\d+\.\d+", data["version"])


def test_cors_headers_attached_for_localhost_3000(client):
    """Test CORS headers are attached for localhost:3000 origin."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_headers_attached_for_localhost_5173(client):
    """Test CORS headers are attached for localhost:5173 origin."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_exposes_request_id_header(client):
    """Test CORS exposes X-Request-ID header for JavaScript access."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    # X-Request-ID should be in expose-headers for JS to read
    assert "access-control-expose-headers" in response.headers
    exposed = response.headers["access-control-expose-headers"].lower()
    assert "x-request-id" in exposed


def test_request_id_header_attached_as_uuid(client):
    """Test X-Request-ID header is attached and is UUID format."""
    response = client.get("/health")
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]
    # Validate UUID format
    try:
        UUID(request_id)
    except ValueError:
        pytest.fail(f"X-Request-ID is not valid UUID: {request_id}")


def test_openapi_json_accessible(client):
    """Test /openapi.json is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "GenGlossary API"


def test_docs_accessible(client):
    """Test /docs is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_accessible(client):
    """Test /redoc is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
