"""Tests for Provisional API endpoints."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from genglossary.db.connection import get_connection
from genglossary.db.project_repository import create_project
from genglossary.db.provisional_repository import create_provisional_term
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.term import TermOccurrence


@pytest.fixture
def test_project_setup(tmp_path: Path, monkeypatch):
    """Setup test project with registry and project database."""
    registry_path = tmp_path / "registry.db"
    project_db_path = tmp_path / "project.db"
    doc_root = tmp_path / "docs"
    doc_root.mkdir()

    # Create test document
    test_doc = doc_root / "test.md"
    test_doc.write_text("これは用語に関するテストドキュメントです。\n用語は重要な概念です。")

    # Set registry path for client fixture
    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(registry_path))

    # Initialize registry
    registry_conn = get_connection(str(registry_path))
    initialize_registry(registry_conn)

    # Create project with LLM provider
    project_id = create_project(
        registry_conn,
        name="Test Project",
        doc_root=str(doc_root),
        db_path=str(project_db_path),
        llm_provider="ollama",
    )

    registry_conn.close()

    return {
        "project_id": project_id,
        "registry_path": str(registry_path),
        "project_db_path": str(project_db_path),
        "doc_root": str(doc_root),
    }


def test_list_provisional_returns_empty_list(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/provisional returns empty list when no terms exist."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/provisional")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_provisional_returns_all_terms(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/provisional returns all provisional terms."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Add some provisional terms
    conn = get_connection(project_db_path)
    occ1 = TermOccurrence(document_path="doc1.txt", line_number=1, context="context1")
    occ2 = TermOccurrence(document_path="doc2.txt", line_number=5, context="context2")

    term1_id = create_provisional_term(
        conn, "量子コンピュータ", "量子力学を利用したコンピュータ", 0.9, [occ1]
    )
    term2_id = create_provisional_term(
        conn, "量子ビット", "量子情報の基本単位", 0.85, [occ2]
    )
    conn.close()

    response = client.get(f"/api/projects/{project_id}/provisional")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == term1_id
    assert data[0]["term_name"] == "量子コンピュータ"
    assert data[0]["definition"] == "量子力学を利用したコンピュータ"
    assert data[0]["confidence"] == 0.9
    assert len(data[0]["occurrences"]) == 1
    assert data[1]["id"] == term2_id
    assert data[1]["term_name"] == "量子ビット"


def test_get_provisional_by_id_returns_term(test_project_setup, client: TestClient):
    """Test GET /api/projects/{id}/provisional/{entry_id} returns specific term."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=3, context="context")
    term_id = create_provisional_term(
        conn, "量子もつれ", "量子力学の現象", 0.95, [occ]
    )
    conn.close()

    response = client.get(f"/api/projects/{project_id}/provisional/{term_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == term_id
    assert data["term_name"] == "量子もつれ"
    assert data["definition"] == "量子力学の現象"
    assert data["confidence"] == 0.95
    assert len(data["occurrences"]) == 1
    assert data["occurrences"][0]["document_path"] == "doc.txt"
    assert data["occurrences"][0]["line_number"] == 3


def test_get_provisional_by_id_returns_404_for_missing_term(
    test_project_setup, client: TestClient
):
    """Test GET /api/projects/{id}/provisional/{entry_id} returns 404 for missing term."""
    project_id = test_project_setup["project_id"]

    response = client.get(f"/api/projects/{project_id}/provisional/999")

    assert response.status_code == 404


def test_update_provisional_modifies_term(test_project_setup, client: TestClient):
    """Test PATCH /api/projects/{id}/provisional/{entry_id} updates term."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=1, context="context")
    term_id = create_provisional_term(conn, "用語", "旧定義", 0.5, [occ])
    conn.close()

    payload = {"definition": "新定義", "confidence": 0.95}

    response = client.patch(
        f"/api/projects/{project_id}/provisional/{term_id}", json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == term_id
    assert data["term_name"] == "用語"
    assert data["definition"] == "新定義"
    assert data["confidence"] == 0.95


def test_update_provisional_returns_404_for_missing_term(
    test_project_setup, client: TestClient
):
    """Test PATCH /api/projects/{id}/provisional/{entry_id} returns 404 for missing term."""
    project_id = test_project_setup["project_id"]

    payload = {"definition": "新定義", "confidence": 0.95}

    response = client.patch(f"/api/projects/{project_id}/provisional/999", json=payload)

    assert response.status_code == 404


@patch("genglossary.api.routers.provisional.GlossaryGenerator")
def test_regenerate_provisional_updates_definition(
    mock_generator_class, test_project_setup, client: TestClient
):
    """Test POST /api/projects/{id}/provisional/{entry_id}/regenerate regenerates definition."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=1, context="context")
    term_id = create_provisional_term(conn, "用語", "旧定義", 0.5, [occ])
    conn.close()

    # Mock GlossaryGenerator
    mock_generator = MagicMock()
    mock_generator._generate_definition.return_value = ("再生成された定義", 0.85)
    mock_generator._find_term_occurrences.return_value = [occ]
    mock_generator_class.return_value = mock_generator

    response = client.post(f"/api/projects/{project_id}/provisional/{term_id}/regenerate")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == term_id
    assert data["term_name"] == "用語"
    # Definition should be regenerated (different from "旧定義")
    assert data["definition"] != "旧定義"
    # Confidence should be updated
    assert data["confidence"] == 0.85


def test_regenerate_provisional_returns_404_for_missing_term(
    test_project_setup, client: TestClient
):
    """Test POST /api/projects/{id}/provisional/{entry_id}/regenerate returns 404 for missing term."""
    project_id = test_project_setup["project_id"]

    response = client.post(f"/api/projects/{project_id}/provisional/999/regenerate")

    assert response.status_code == 404


def test_get_provisional_returns_404_for_missing_project(client: TestClient):
    """Test GET /api/projects/{id}/provisional returns 404 for missing project."""
    response = client.get("/api/projects/999/provisional")

    assert response.status_code == 404


@patch("genglossary.api.routers.provisional.GlossaryGenerator")
def test_regenerate_provisional_changes_definition_with_mock(
    mock_generator_class, test_project_setup, client: TestClient
):
    """Test regenerate endpoint changes definition using mocked LLM."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Setup provisional term
    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=1, context="context")
    term_id = create_provisional_term(conn, "用語", "旧定義", 0.5, [occ])
    conn.close()

    # Mock GlossaryGenerator
    mock_generator = MagicMock()
    mock_generator._generate_definition.return_value = ("新しい定義", 0.85)
    mock_generator._find_term_occurrences.return_value = [occ]
    mock_generator_class.return_value = mock_generator

    # Call regenerate endpoint
    response = client.post(f"/api/projects/{project_id}/provisional/{term_id}/regenerate")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == term_id
    assert data["term_name"] == "用語"
    assert data["definition"] == "新しい定義"
    assert data["definition"] != "旧定義"


@patch("genglossary.api.routers.provisional.GlossaryGenerator")
def test_regenerate_provisional_updates_confidence_with_mock(
    mock_generator_class, test_project_setup, client: TestClient
):
    """Test regenerate endpoint updates confidence using mocked LLM."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Setup provisional term
    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=1, context="context")
    term_id = create_provisional_term(conn, "用語", "定義", 0.5, [occ])
    conn.close()

    # Mock GlossaryGenerator
    mock_generator = MagicMock()
    mock_generator._generate_definition.return_value = ("更新された定義", 0.92)
    mock_generator._find_term_occurrences.return_value = [occ]
    mock_generator_class.return_value = mock_generator

    # Call regenerate endpoint
    response = client.post(f"/api/projects/{project_id}/provisional/{term_id}/regenerate")

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == 0.92
    assert data["confidence"] != 0.5


@patch("genglossary.api.routers.provisional.GlossaryGenerator")
def test_regenerate_provisional_persists_to_db(
    mock_generator_class, test_project_setup, client: TestClient
):
    """Test regenerate endpoint persists changes to database."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Setup provisional term
    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=1, context="context")
    term_id = create_provisional_term(conn, "用語", "旧定義", 0.5, [occ])
    conn.close()

    # Mock GlossaryGenerator
    mock_generator = MagicMock()
    mock_generator._generate_definition.return_value = ("永続化された定義", 0.88)
    mock_generator._find_term_occurrences.return_value = [occ]
    mock_generator_class.return_value = mock_generator

    # Call regenerate endpoint
    client.post(f"/api/projects/{project_id}/provisional/{term_id}/regenerate")

    # Verify persistence with GET
    response = client.get(f"/api/projects/{project_id}/provisional/{term_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["definition"] == "永続化された定義"
    assert data["confidence"] == 0.88


@patch("genglossary.api.routers.provisional.GlossaryGenerator")
def test_regenerate_provisional_llm_timeout_returns_503(
    mock_generator_class, test_project_setup, client: TestClient
):
    """Test regenerate endpoint returns 503 when LLM times out."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Setup provisional term
    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=1, context="context")
    term_id = create_provisional_term(conn, "用語", "定義", 0.5, [occ])
    conn.close()

    # Mock GlossaryGenerator to raise TimeoutException
    mock_generator = MagicMock()
    mock_generator._generate_definition.side_effect = httpx.TimeoutException("Timeout")
    mock_generator._find_term_occurrences.return_value = [occ]
    mock_generator_class.return_value = mock_generator

    # Call regenerate endpoint
    response = client.post(f"/api/projects/{project_id}/provisional/{term_id}/regenerate")

    assert response.status_code == 503
    assert "timeout" in response.json()["detail"].lower()


@patch("genglossary.api.routers.provisional.GlossaryGenerator")
def test_regenerate_provisional_llm_unavailable_returns_503(
    mock_generator_class, test_project_setup, client: TestClient
):
    """Test regenerate endpoint returns 503 when LLM is unavailable."""
    project_id = test_project_setup["project_id"]
    project_db_path = test_project_setup["project_db_path"]

    # Setup provisional term
    conn = get_connection(project_db_path)
    occ = TermOccurrence(document_path="doc.txt", line_number=1, context="context")
    term_id = create_provisional_term(conn, "用語", "定義", 0.5, [occ])
    conn.close()

    # Mock GlossaryGenerator to raise HTTPError
    mock_generator = MagicMock()
    mock_generator._generate_definition.side_effect = httpx.HTTPError("Connection failed")
    mock_generator._find_term_occurrences.return_value = [occ]
    mock_generator_class.return_value = mock_generator

    # Call regenerate endpoint
    response = client.post(f"/api/projects/{project_id}/provisional/{term_id}/regenerate")

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()
