"""Fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create TestClient for API testing.

    Note: Tests should set GENGLOSSARY_REGISTRY_PATH via monkeypatch
    before using this fixture if they need a specific registry path.
    """
    from genglossary.api.app import create_app

    app = create_app()
    return TestClient(app)
