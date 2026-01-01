"""Tests for TermExtractor - Step 1: Term extraction from documents."""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.term_extractor import TermExtractor


class MockExtractedTerms(BaseModel):
    """Mock response model for extracted terms."""
    terms: list[str]


class TestTermExtractor:
    """Test suite for TermExtractor class."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock(spec=BaseLLMClient)
        return client

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        content = """GenGlossaryは用語集を自動生成するツールです。
LLMを活用して、ドキュメントから用語を抽出します。
抽出された用語は、コンテキストに基づいて定義されます。
GenGlossaryはPythonで実装されています。
"""
        return Document(file_path="/path/to/doc.md", content=content)

    @pytest.fixture
    def empty_document(self) -> Document:
        """Create an empty document for testing."""
        return Document(file_path="/path/to/empty.md", content="")

    def test_term_extractor_initialization(self, mock_llm_client: MagicMock) -> None:
        """Test that TermExtractor can be initialized with an LLM client."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        assert extractor.llm_client == mock_llm_client

    def test_extract_terms_returns_list_of_strings(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that extract_terms returns a list of strings."""
        mock_response = MockExtractedTerms(terms=["GenGlossary", "LLM", "用語集"])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert isinstance(result, list)
        assert all(isinstance(term, str) for term in result)
        assert "GenGlossary" in result
        assert "LLM" in result
        assert "用語集" in result

    def test_extract_terms_calls_llm_with_correct_prompt_format(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that LLM is called with prompt containing expected elements."""
        mock_response = MockExtractedTerms(terms=["GenGlossary"])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        extractor.extract_terms([sample_document])

        # Verify LLM was called
        mock_llm_client.generate_structured.assert_called_once()
        call_args = mock_llm_client.generate_structured.call_args

        # Check prompt contains key elements
        prompt = call_args[0][0]  # First positional argument
        assert "専門用語" in prompt or "用語" in prompt
        assert sample_document.content in prompt or "GenGlossary" in prompt

    def test_extract_terms_removes_duplicates(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that duplicate terms are removed from the result."""
        # LLM returns duplicates
        mock_response = MockExtractedTerms(
            terms=["GenGlossary", "LLM", "GenGlossary", "LLM", "用語集"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        # Count occurrences - each term should appear only once
        assert result.count("GenGlossary") == 1
        assert result.count("LLM") == 1
        assert result.count("用語集") == 1

    def test_extract_terms_handles_empty_document(
        self, mock_llm_client: MagicMock, empty_document: Document
    ) -> None:
        """Test that empty documents return an empty list."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([empty_document])

        assert result == []
        # LLM should not be called for empty documents
        mock_llm_client.generate_structured.assert_not_called()

    def test_extract_terms_handles_multiple_documents(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test extraction from multiple documents."""
        doc1 = Document(file_path="/doc1.md", content="Document about Python and LLM.")
        doc2 = Document(file_path="/doc2.md", content="Document about API and LLM.")

        mock_response = MockExtractedTerms(terms=["Python", "LLM", "API"])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([doc1, doc2])

        assert "Python" in result
        assert "LLM" in result
        assert "API" in result

    def test_extract_terms_preserves_order_while_removing_duplicates(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that term order is preserved (first occurrence kept)."""
        mock_response = MockExtractedTerms(
            terms=["第一用語", "第二用語", "第一用語", "第三用語"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert result == ["第一用語", "第二用語", "第三用語"]

    def test_create_extraction_prompt_includes_document_content(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that _create_extraction_prompt includes document content."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        prompt = extractor._create_extraction_prompt([sample_document])

        assert sample_document.content in prompt

    def test_create_extraction_prompt_specifies_json_format(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that prompt specifies JSON output format."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        prompt = extractor._create_extraction_prompt([sample_document])

        assert "JSON" in prompt or "json" in prompt
        assert "terms" in prompt

    def test_extract_terms_handles_whitespace_only_document(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that whitespace-only documents are handled like empty documents."""
        whitespace_doc = Document(file_path="/whitespace.md", content="   \n\n  \t  ")

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([whitespace_doc])

        assert result == []
        mock_llm_client.generate_structured.assert_not_called()

    def test_extract_terms_strips_whitespace_from_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that whitespace is stripped from extracted terms."""
        mock_response = MockExtractedTerms(
            terms=["  GenGlossary  ", " LLM", "用語集 "]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "GenGlossary" in result
        assert "LLM" in result
        assert "用語集" in result
        # No whitespace-padded versions
        assert "  GenGlossary  " not in result

    def test_extract_terms_filters_empty_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that empty strings are filtered out from results."""
        mock_response = MockExtractedTerms(
            terms=["GenGlossary", "", "LLM", "  ", "用語集"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "" not in result
        assert len(result) == 3


class TestTermFiltering:
    """Test suite for term filtering functionality."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock(spec=BaseLLMClient)
        return client

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        content = """小説の登場人物について。
主人公のシルシルは魔法使いです。
彼は法則の発見に成功しました。
"""
        return Document(file_path="/path/to/novel.md", content=content)

    def test_filter_verb_phrases(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that verb phrases are filtered out."""
        mock_response = MockExtractedTerms(
            terms=["法則の発見", "理性の崩壊", "死戦を潜り抜ける", "魔法使い"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        # Verb phrases should be filtered
        assert "法則の発見" not in result
        assert "死戦を潜り抜ける" not in result
        # Valid terms should remain
        assert "魔法使い" in result

    def test_filter_adjective_phrases(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that adjective phrases are filtered out."""
        mock_response = MockExtractedTerms(
            terms=["顔が良い", "銀色の髪", "アルケミスト"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "顔が良い" not in result
        assert "銀色の髪" not in result
        assert "アルケミスト" in result

    def test_preserve_proper_nouns(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that proper nouns are preserved."""
        mock_response = MockExtractedTerms(
            terms=["東京", "田中太郎", "エルディア", "進撃の巨人"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "東京" in result
        assert "田中太郎" in result
        assert "エルディア" in result
        assert "進撃の巨人" in result

    def test_filter_short_hiragana_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that short hiragana-only terms are filtered."""
        mock_response = MockExtractedTerms(
            terms=["しかし", "ただ", "マイクロサービス"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "しかし" not in result
        assert "ただ" not in result
        assert "マイクロサービス" in result

    def test_filter_single_character_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that single character terms are filtered."""
        mock_response = MockExtractedTerms(
            terms=["A", "魔", "API"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "A" not in result
        assert "魔" not in result
        assert "API" in result

    def test_filter_verb_ending_patterns(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test various verb ending patterns are filtered."""
        mock_response = MockExtractedTerms(
            terms=[
                "実行する",
                "実施された",
                "運用している",
                "変換される",
                "発見となる",
                "システム",
            ]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        # Verb patterns should be filtered
        assert "実行する" not in result
        assert "実施された" not in result
        assert "運用している" not in result
        assert "変換される" not in result
        assert "発見となる" not in result
        # Valid term should remain
        assert "システム" in result


class TestPromptGeneration:
    """Test suite for prompt generation."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock(spec=BaseLLMClient)
        return client

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        content = "Sample content for prompt testing."
        return Document(file_path="/path/to/doc.md", content=content)

    def test_prompt_includes_proper_noun_guidance(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that prompt includes guidance for proper nouns."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        prompt = extractor._create_extraction_prompt([sample_document])

        # Check for proper noun guidance
        assert "固有名詞" in prompt

    def test_prompt_specifies_exclusion_criteria(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that prompt specifies what should be excluded."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        prompt = extractor._create_extraction_prompt([sample_document])

        # Check exclusion criteria are mentioned
        assert "除外" in prompt or "抽出しない" in prompt
        assert "動詞" in prompt
        assert "形容詞" in prompt or "描写" in prompt

    def test_prompt_includes_judgment_criteria(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that prompt includes judgment criteria."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        prompt = extractor._create_extraction_prompt([sample_document])

        # Check for judgment criteria
        assert "判断基準" in prompt or "基準" in prompt
