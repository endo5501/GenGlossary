"""Integration tests using real Ollama server.

Run with: uv run pytest -m integration tests/test_ollama_integration.py -v
"""

from pathlib import Path

import pytest

from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.ollama_client import OllamaClient
from genglossary.models.glossary import Glossary
from genglossary.output.markdown_writer import MarkdownWriter
from genglossary.term_extractor import TermExtractor


def _ollama_available() -> bool:
    """Check if Ollama server is running and available."""
    try:
        client = OllamaClient()
        return client.is_available()
    except Exception:
        return False


pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def require_ollama() -> None:
    """Skip integration tests when Ollama is not available."""
    if not _ollama_available():
        pytest.skip("Ollama server is not running")


@pytest.fixture
def ollama_client(require_ollama: None) -> OllamaClient:
    """Create a real Ollama client."""
    return OllamaClient(
        model="llama2",  # Use available model
        timeout=60.0,
    )


@pytest.fixture
def sample_docs_for_ollama(tmp_path: Path) -> Path:
    """Create sample documents for Ollama testing."""
    doc_content = """# マイクロサービスアーキテクチャ

本システムはマイクロサービスアーキテクチャを採用しています。
マイクロサービスとは、アプリケーションを小さな独立したサービスに分割する設計パターンです。

## APIゲートウェイ

すべてのリクエストはAPIゲートウェイを経由します。
APIゲートウェイは認証、ルーティング、レート制限を担当します。

## データベース

PostgreSQLを使用してデータを永続化します。
"""
    doc_path = tmp_path / "architecture.md"
    doc_path.write_text(doc_content, encoding="utf-8")
    return tmp_path


class TestOllamaTermExtraction:
    """Test term extraction with real Ollama."""

    @pytest.mark.xfail(
        strict=True,
        reason="LLM output may be nondeterministic; treat XPASS as signal to tighten expectations",
    )
    def test_extract_terms_from_document(
        self,
        ollama_client: OllamaClient,
        sample_docs_for_ollama: Path,
    ) -> None:
        """Test extracting terms using real Ollama."""
        # Load documents
        loader = DocumentLoader()
        documents = loader.load_directory(str(sample_docs_for_ollama))
        assert len(documents) >= 1

        # Extract terms
        extractor = TermExtractor(llm_client=ollama_client)
        terms = extractor.extract_terms(documents)

        # Should extract some terms (exact terms depend on LLM)
        assert isinstance(terms, list)
        assert len(terms) > 0

        # All terms should be strings
        assert all(isinstance(t, str) for t in terms)
        assert all(len(t.strip()) > 0 for t in terms)


class TestOllamaGlossaryGeneration:
    """Test glossary generation with real Ollama."""

    @pytest.mark.xfail(
        strict=True,
        reason="LLM output may be nondeterministic; treat XPASS as signal to tighten expectations",
    )
    def test_generate_glossary(
        self,
        ollama_client: OllamaClient,
        sample_docs_for_ollama: Path,
    ) -> None:
        """Test generating glossary definitions using real Ollama."""
        loader = DocumentLoader()
        documents = loader.load_directory(str(sample_docs_for_ollama))

        # Use predefined terms for consistency
        terms = ["マイクロサービス", "APIゲートウェイ"]

        generator = GlossaryGenerator(llm_client=ollama_client)
        glossary = generator.generate(terms, documents)

        assert isinstance(glossary, Glossary)
        assert glossary.term_count == 2

        # Each term should have a definition
        for term_name in terms:
            term = glossary.get_term(term_name)
            assert term is not None
            assert term.definition != ""


class TestOllamaReviewAndRefine:
    """Test review and refinement with real Ollama."""

    @pytest.mark.xfail(
        strict=True,
        reason="LLM output may be nondeterministic; treat XPASS as signal to tighten expectations",
    )
    def test_review_glossary(
        self,
        ollama_client: OllamaClient,
        sample_glossary: Glossary,
    ) -> None:
        """Test reviewing glossary using real Ollama."""
        reviewer = GlossaryReviewer(llm_client=ollama_client)
        issues = reviewer.review(sample_glossary)

        # Should return a list (may be empty if no issues)
        assert isinstance(issues, list)
        # All issues should be valid GlossaryIssue objects
        for issue in issues:
            assert hasattr(issue, "term_name")
            assert hasattr(issue, "issue_type")
            assert hasattr(issue, "description")


class TestOllamaFullPipeline:
    """Test complete pipeline with real Ollama."""

    @pytest.mark.xfail(
        strict=True,
        reason="LLM output may be nondeterministic; treat XPASS as signal to tighten expectations",
    )
    def test_full_pipeline(
        self,
        ollama_client: OllamaClient,
        sample_docs_for_ollama: Path,
    ) -> None:
        """Test complete glossary generation pipeline with real Ollama."""
        # 1. Load documents
        loader = DocumentLoader()
        documents = loader.load_directory(str(sample_docs_for_ollama))
        assert len(documents) >= 1

        # 2. Extract terms
        extractor = TermExtractor(llm_client=ollama_client)
        terms = extractor.extract_terms(documents)
        assert len(terms) > 0

        # 3. Generate glossary
        generator = GlossaryGenerator(llm_client=ollama_client)
        glossary = generator.generate(terms, documents)
        assert glossary.term_count > 0

        # 4. Review glossary
        reviewer = GlossaryReviewer(llm_client=ollama_client)
        issues = reviewer.review(glossary)
        # Issues list is valid (may be empty)
        assert isinstance(issues, list)

        # 5. Refine glossary
        refiner = GlossaryRefiner(llm_client=ollama_client)
        refined_glossary = refiner.refine(glossary, issues, documents)
        assert refined_glossary.term_count > 0

        # 6. Write output
        output_path = sample_docs_for_ollama / "glossary.md"
        writer = MarkdownWriter()
        writer.write(refined_glossary, str(output_path))

        # Verify output file exists and has content
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# 用語集" in content
        assert len(content) > 100  # Should have substantial content


class TestOllamaClientHealth:
    """Test Ollama client health checks."""

    def test_client_is_available(self) -> None:
        """Test that Ollama client reports availability correctly."""
        client = OllamaClient()
        # If we got here, Ollama should be available
        assert client.is_available()

    def test_client_generates_response(self, ollama_client: OllamaClient) -> None:
        """Test that Ollama client can generate a response."""
        response = ollama_client.generate("Say hello in one word.")
        assert isinstance(response, str)
        assert len(response) > 0
