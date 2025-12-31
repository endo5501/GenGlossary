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
