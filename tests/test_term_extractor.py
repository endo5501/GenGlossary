"""Tests for TermExtractor - New architecture with SudachiPy + LLM judgment."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.term_extractor import TermExtractor


class MockTermJudgmentResponse(BaseModel):
    """Mock response model for term judgment."""

    approved_terms: list[str]


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
        content = """東京は日本の首都です。
トヨタ自動車は愛知県に本社があります。
大阪府にはユニバーサルスタジオがあります。
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
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "日本", "トヨタ自動車"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert isinstance(result, list)
        assert all(isinstance(term, str) for term in result)

    def test_extract_terms_uses_morphological_analyzer(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that extract_terms uses MorphologicalAnalyzer for proper noun extraction."""
        mock_response = MockTermJudgmentResponse(approved_terms=["東京"])
        mock_llm_client.generate_structured.return_value = mock_response

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = ["東京", "日本"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            extractor.extract_terms([sample_document])

            # Verify MorphologicalAnalyzer was used
            mock_analyzer.extract_proper_nouns.assert_called()

    def test_extract_terms_sends_candidates_to_llm(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that extracted proper nouns are sent to LLM for judgment."""
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "トヨタ自動車"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        extractor.extract_terms([sample_document])

        # Verify LLM was called
        mock_llm_client.generate_structured.assert_called_once()

    def test_extract_terms_removes_duplicates(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that duplicate terms are removed from the result."""
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "東京", "日本"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert result.count("東京") == 1
        assert result.count("日本") == 1

    def test_extract_terms_handles_empty_document(
        self, mock_llm_client: MagicMock, empty_document: Document
    ) -> None:
        """Test that empty documents return an empty list."""
        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([empty_document])

        assert result == []
        mock_llm_client.generate_structured.assert_not_called()

    def test_extract_terms_handles_multiple_documents(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test extraction from multiple documents."""
        doc1 = Document(
            file_path="/doc1.md", content="東京に住んでいます。"
        )
        doc2 = Document(
            file_path="/doc2.md", content="大阪に行きました。"
        )

        mock_response = MockTermJudgmentResponse(approved_terms=["東京", "大阪"])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([doc1, doc2])

        assert isinstance(result, list)

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
        mock_response = MockTermJudgmentResponse(
            approved_terms=["  東京  ", " 日本", "大阪 "]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "東京" in result
        assert "日本" in result
        assert "大阪" in result
        assert "  東京  " not in result

    def test_extract_terms_filters_empty_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that empty strings are filtered out from results."""
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "", "日本", "  "]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "" not in result
        assert len(result) == 2

    def test_extract_terms_returns_only_approved_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that only LLM-approved terms are returned."""
        # LLM approves only some of the candidates
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "トヨタ自動車"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert "東京" in result
        assert "トヨタ自動車" in result

    def test_extract_terms_handles_no_approved_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test handling when LLM approves no terms."""
        mock_response = MockTermJudgmentResponse(approved_terms=[])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.extract_terms([sample_document])

        assert result == []


class TestTermJudgmentPrompt:
    """Test suite for LLM judgment prompt generation."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock(spec=BaseLLMClient)
        return client

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        content = "東京は日本の首都です。"
        return Document(file_path="/path/to/doc.md", content=content)

    def test_judgment_prompt_includes_candidates(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that judgment prompt includes candidate terms."""
        mock_response = MockTermJudgmentResponse(approved_terms=[])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        extractor.extract_terms([sample_document])

        # Check that prompt contains candidate terms
        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # Should contain guidance for judgment
        assert "用語" in prompt or "候補" in prompt

    def test_judgment_prompt_includes_context(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that judgment prompt includes document context."""
        mock_response = MockTermJudgmentResponse(approved_terms=[])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        extractor.extract_terms([sample_document])

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # Should include document content for context
        assert "東京" in prompt or "日本" in prompt

    def test_judgment_prompt_specifies_json_format(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that judgment prompt specifies JSON output format."""
        mock_response = MockTermJudgmentResponse(approved_terms=[])
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        extractor.extract_terms([sample_document])

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        assert "JSON" in prompt or "json" in prompt
        assert "approved_terms" in prompt
