"""Fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create TestClient for API testing."""
    from genglossary.api.app import create_app

    app = create_app()
    return TestClient(app)
