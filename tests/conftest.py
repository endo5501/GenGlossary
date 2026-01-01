"""Pytest fixtures shared across all tests."""

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.models.term import Term, TermOccurrence


# --- Mock Response Models ---


class MockExtractedTerms(BaseModel):
    """Mock response for term extraction."""

    terms: list[str]


class MockDefinitionResponse(BaseModel):
    """Mock response for definition generation."""

    definition: str
    confidence: float


class MockRelatedTermsResponse(BaseModel):
    """Mock response for related terms extraction."""

    related_terms: list[str]


class MockReviewResponse(BaseModel):
    """Mock response for glossary review."""

    issues: list[dict[str, str]]


class MockRefinedDefinitionResponse(BaseModel):
    """Mock response for definition refinement."""

    refined_definition: str
    related_terms: list[str]


# --- Document Fixtures ---


@pytest.fixture
def sample_documents() -> list[Document]:
    """Create a list of sample documents for testing.

    Returns:
        List of Document objects with technical content.
    """
    doc1_content = """# システムアーキテクチャ

本システムはマイクロサービスアーキテクチャを採用しています。
各コンポーネントは独立してデプロイ可能です。

## APIゲートウェイ

すべてのリクエストはAPIゲートウェイを経由します。
認証とルーティングを担当するコンポーネントです。
"""

    doc2_content = """# データベース設計

PostgreSQLを使用してデータを永続化します。
トランザクション整合性を保証するため、
適切なインデックスを設定しています。

APIゲートウェイからのリクエストを処理します。
"""

    return [
        Document(file_path="/docs/architecture.md", content=doc1_content),
        Document(file_path="/docs/database.md", content=doc2_content),
    ]


@pytest.fixture
def sample_document() -> Document:
    """Create a single sample document for testing.

    Returns:
        A Document object with technical content.
    """
    content = """GenGlossaryは用語集を自動生成するツールです。
LLMを活用して、ドキュメントから用語を抽出します。
抽出された用語は、コンテキストに基づいて定義されます。
GenGlossaryはPythonで実装されています。
"""
    return Document(file_path="/path/to/doc.md", content=content)


# --- LLM Client Fixtures ---


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client for testing.

    Returns:
        A MagicMock object that follows BaseLLMClient spec.
    """
    client = MagicMock(spec=BaseLLMClient)
    return client


@pytest.fixture
def mock_llm_client_for_pipeline() -> MagicMock:
    """Create a mock LLM client configured for full pipeline testing.

    This client is pre-configured to return appropriate responses for:
    - Term extraction
    - Definition generation
    - Related terms extraction
    - Glossary review
    - Definition refinement

    Returns:
        A MagicMock object with pipeline-appropriate side effects.
    """
    client = MagicMock(spec=BaseLLMClient)

    # Responses will be set up in the order they're called
    responses = [
        # 1. Term extraction
        MockExtractedTerms(terms=["マイクロサービス", "APIゲートウェイ", "PostgreSQL"]),
        # 2. Definition for マイクロサービス
        MockDefinitionResponse(
            definition="独立して開発・デプロイ可能な小さなサービスに分割するアーキテクチャ",
            confidence=0.9,
        ),
        # 3. Related terms for マイクロサービス
        MockRelatedTermsResponse(related_terms=["APIゲートウェイ"]),
        # 4. Definition for APIゲートウェイ
        MockDefinitionResponse(
            definition="すべてのAPIリクエストの入り口となるコンポーネント",
            confidence=0.85,
        ),
        # 5. Related terms for APIゲートウェイ
        MockRelatedTermsResponse(related_terms=["マイクロサービス"]),
        # 6. Definition for PostgreSQL
        MockDefinitionResponse(
            definition="オープンソースのリレーショナルデータベース管理システム",
            confidence=0.95,
        ),
        # 7. Related terms for PostgreSQL
        MockRelatedTermsResponse(related_terms=[]),
        # 8. Review response
        MockReviewResponse(
            issues=[
                {
                    "term_name": "マイクロサービス",
                    "issue_type": "missing_relation",
                    "description": "PostgreSQLとの関連性が記載されていない",
                }
            ]
        ),
        # 9. Refined definition for マイクロサービス
        MockRefinedDefinitionResponse(
            refined_definition="独立してデプロイ可能な小さなサービス群で構成されるアーキテクチャパターン",
            related_terms=["APIゲートウェイ", "PostgreSQL"],
        ),
    ]

    client.generate_structured.side_effect = responses
    return client


# --- Glossary Fixtures ---


@pytest.fixture
def sample_glossary() -> Glossary:
    """Create a sample glossary for testing.

    Returns:
        A Glossary object with pre-populated terms.
    """
    glossary = Glossary()

    # Add term with occurrences
    term1 = Term(
        name="マイクロサービス",
        definition="独立して開発・デプロイ可能な小さなサービスに分割するアーキテクチャ",
        occurrences=[
            TermOccurrence(
                document_path="/docs/architecture.md",
                line_number=3,
                context="本システムはマイクロサービスアーキテクチャを採用しています。",
            )
        ],
        related_terms=["APIゲートウェイ"],
        confidence=0.9,
    )
    glossary.add_term(term1)

    term2 = Term(
        name="APIゲートウェイ",
        definition="すべてのAPIリクエストの入り口となるコンポーネント",
        occurrences=[
            TermOccurrence(
                document_path="/docs/architecture.md",
                line_number=6,
                context="すべてのリクエストはAPIゲートウェイを経由します。",
            ),
            TermOccurrence(
                document_path="/docs/database.md",
                line_number=6,
                context="APIゲートウェイからのリクエストを処理します。",
            ),
        ],
        related_terms=["マイクロサービス"],
        confidence=0.85,
    )
    glossary.add_term(term2)

    term3 = Term(
        name="PostgreSQL",
        definition="オープンソースのリレーショナルデータベース管理システム",
        occurrences=[
            TermOccurrence(
                document_path="/docs/database.md",
                line_number=3,
                context="PostgreSQLを使用してデータを永続化します。",
            )
        ],
        related_terms=[],
        confidence=0.95,
    )
    glossary.add_term(term3)

    # Add metadata
    glossary.metadata = {
        "generated_at": "2024-01-01T00:00:00",
        "document_count": 2,
        "model": "test-model",
    }

    return glossary


# --- Temporary Directory Fixtures ---


@pytest.fixture
def tmp_path_with_docs(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory with sample documents.

    Args:
        tmp_path: Pytest's built-in tmp_path fixture.

    Yields:
        Path to the temporary directory containing sample documents.
    """
    # Create sample documents
    doc1_content = """# システムアーキテクチャ

本システムはマイクロサービスアーキテクチャを採用しています。
各コンポーネントは独立してデプロイ可能です。

## APIゲートウェイ

すべてのリクエストはAPIゲートウェイを経由します。
認証とルーティングを担当するコンポーネントです。
"""

    doc2_content = """# データベース設計

PostgreSQLを使用してデータを永続化します。
トランザクション整合性を保証するため、
適切なインデックスを設定しています。

APIゲートウェイからのリクエストを処理します。
"""

    # Write documents
    (tmp_path / "architecture.md").write_text(doc1_content, encoding="utf-8")
    (tmp_path / "database.md").write_text(doc2_content, encoding="utf-8")

    yield tmp_path
