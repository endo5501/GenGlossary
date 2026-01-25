"""Fixtures for API tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    """Create TestClient for API testing with test registry database."""
    from genglossary.api.app import create_app

    # Set test registry path
    registry_path = tmp_path / "test_registry.db"
    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(registry_path))

    app = create_app()
    return TestClient(app)
