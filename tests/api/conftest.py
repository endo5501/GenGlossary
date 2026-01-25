"""Fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolate_registry(tmp_path, monkeypatch):
    """Ensure tests don't touch user's registry.

    This fixture automatically sets GENGLOSSARY_REGISTRY_PATH to a temporary
    path for all tests in this directory.
    """
    test_registry = tmp_path / "test_registry.db"
    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(test_registry))


@pytest.fixture
def client():
    """Create TestClient for API testing.

    Note: Tests should set GENGLOSSARY_REGISTRY_PATH via monkeypatch
    before using this fixture if they need a specific registry path.
    """
    from genglossary.api.app import create_app

    app = create_app()
    return TestClient(app)
