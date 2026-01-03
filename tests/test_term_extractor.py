"""Tests for TermExtractor - New architecture with SudachiPy + LLM judgment."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.term import TermCategory
from genglossary.term_extractor import (
    TermClassificationResponse,
    TermExtractor,
)


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


class TestTermExtractionAnalysis:
    """Test suite for term extraction analysis functionality."""

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
"""
        return Document(file_path="/path/to/doc.md", content=content)

    def test_analyze_extraction_returns_analysis_model(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that analyze_extraction returns TermExtractionAnalysis."""
        from genglossary.term_extractor import TermExtractionAnalysis

        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "トヨタ自動車"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.analyze_extraction([sample_document])

        assert isinstance(result, TermExtractionAnalysis)

    def test_analyze_extraction_contains_sudachi_candidates(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that analysis contains SudachiPy candidates."""
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "トヨタ自動車"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = [
                "東京", "日本", "トヨタ自動車", "愛知県"
            ]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            result = extractor.analyze_extraction([sample_document])

            assert result.sudachi_candidates == [
                "東京", "日本", "トヨタ自動車", "愛知県"
            ]

    def test_analyze_extraction_contains_llm_approved(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that analysis contains LLM-approved terms."""
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "トヨタ自動車"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = [
                "東京", "日本", "トヨタ自動車", "愛知県"
            ]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            result = extractor.analyze_extraction([sample_document])

            assert "東京" in result.llm_approved
            assert "トヨタ自動車" in result.llm_approved

    def test_analyze_extraction_contains_llm_rejected(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that analysis contains LLM-rejected terms."""
        mock_response = MockTermJudgmentResponse(
            approved_terms=["東京", "トヨタ自動車"]
        )
        mock_llm_client.generate_structured.return_value = mock_response

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = [
                "東京", "日本", "トヨタ自動車", "愛知県"
            ]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            result = extractor.analyze_extraction([sample_document])

            # 日本 and 愛知県 should be rejected
            assert "日本" in result.llm_rejected
            assert "愛知県" in result.llm_rejected
            assert "東京" not in result.llm_rejected

    def test_analyze_extraction_handles_empty_documents(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that analyze_extraction handles empty documents."""
        from genglossary.term_extractor import TermExtractionAnalysis

        empty_doc = Document(file_path="/empty.md", content="")

        extractor = TermExtractor(llm_client=mock_llm_client)
        result = extractor.analyze_extraction([empty_doc])

        assert isinstance(result, TermExtractionAnalysis)
        assert result.sudachi_candidates == []
        assert result.llm_approved == []
        assert result.llm_rejected == []
        mock_llm_client.generate_structured.assert_not_called()

    def test_analyze_extraction_handles_no_candidates(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test analyze_extraction when SudachiPy finds no candidates."""
        from genglossary.term_extractor import TermExtractionAnalysis

        doc = Document(file_path="/doc.md", content="普通の文章です。")

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = []
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            result = extractor.analyze_extraction([doc])

            assert isinstance(result, TermExtractionAnalysis)
            assert result.sudachi_candidates == []
            assert result.llm_approved == []
            assert result.llm_rejected == []
            mock_llm_client.generate_structured.assert_not_called()


class TestTermCategory:
    """Test suite for TermCategory enum."""

    def test_term_category_values(self) -> None:
        """Test that TermCategory has the expected 6 categories."""
        assert TermCategory.PERSON_NAME.value == "person_name"
        assert TermCategory.PLACE_NAME.value == "place_name"
        assert TermCategory.ORGANIZATION.value == "organization"
        assert TermCategory.TITLE.value == "title"
        assert TermCategory.TECHNICAL_TERM.value == "technical_term"
        assert TermCategory.COMMON_NOUN.value == "common_noun"

    def test_term_category_count(self) -> None:
        """Test that there are exactly 6 categories."""
        assert len(TermCategory) == 6

    def test_common_noun_is_excluded_category(self) -> None:
        """Test that common noun is identified as the excluded category."""
        # COMMON_NOUN should be the category that gets filtered out
        assert TermCategory.COMMON_NOUN.value == "common_noun"


class TestTermClassificationResponse:
    """Test suite for TermClassificationResponse model."""

    def test_classification_response_structure(self) -> None:
        """Test that classification response has correct structure."""
        response = TermClassificationResponse(
            classified_terms={
                "person_name": ["田中太郎", "山田花子"],
                "place_name": ["東京", "大阪"],
                "organization": ["アソリウス島騎士団"],
                "title": ["騎士団長", "将軍"],
                "technical_term": ["聖印"],
                "common_noun": ["未亡人", "行方不明"],
            }
        )

        assert "person_name" in response.classified_terms
        assert response.classified_terms["person_name"] == ["田中太郎", "山田花子"]

    def test_classification_response_partial_categories(self) -> None:
        """Test that classification response works with partial categories."""
        response = TermClassificationResponse(
            classified_terms={
                "organization": ["エデルト軍"],
                "common_noun": ["未亡人"],
            }
        )

        assert len(response.classified_terms) == 2
        assert "organization" in response.classified_terms

    def test_classification_response_empty_categories(self) -> None:
        """Test that classification response works with empty dict."""
        response = TermClassificationResponse(classified_terms={})

        assert response.classified_terms == {}


class TestTermExtractorClassification:
    """Test suite for term classification phase."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock(spec=BaseLLMClient)
        return client

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document with various term types."""
        content = """アソリウス島騎士団の団長であるガウス卿は、
エデルト軍との戦いに備えていた。
聖印の力を持つ騎士だけが、魔神討伐に参加できる。
未亡人となったアリスは行方不明になった。"""
        return Document(file_path="/story.md", content=content)

    def test_classify_terms_returns_classification_response(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that _classify_terms returns TermClassificationResponse."""
        mock_response = TermClassificationResponse(
            classified_terms={
                "organization": ["アソリウス島騎士団", "エデルト軍"],
                "title": ["団長", "騎士"],
                "person_name": ["ガウス卿", "アリス"],
                "technical_term": ["聖印", "魔神討伐"],
                "common_noun": ["未亡人", "行方不明"],
            }
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        candidates = ["アソリウス島騎士団", "エデルト軍", "団長", "未亡人"]
        result = extractor._classify_terms(candidates, [sample_document])

        assert isinstance(result, TermClassificationResponse)

    def test_classify_terms_calls_llm_with_classification_prompt(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that _classify_terms sends correct prompt to LLM."""
        mock_response = TermClassificationResponse(
            classified_terms={"organization": ["アソリウス島騎士団"]}
        )
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        candidates = ["アソリウス島騎士団"]
        extractor._classify_terms(candidates, [sample_document])

        # Verify LLM was called with TermClassificationResponse
        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]
        response_model = call_args[0][1]

        # Check prompt contains classification instructions
        assert "分類" in prompt or "カテゴリ" in prompt
        assert response_model == TermClassificationResponse

    def test_classify_terms_includes_all_categories_in_prompt(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that classification prompt includes all 6 categories."""
        mock_response = TermClassificationResponse(classified_terms={})
        mock_llm_client.generate_structured.return_value = mock_response

        extractor = TermExtractor(llm_client=mock_llm_client)
        extractor._classify_terms(["テスト用語"], [sample_document])

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # All categories should be mentioned in the prompt
        assert "人名" in prompt
        assert "地名" in prompt
        assert "組織" in prompt or "団体" in prompt
        assert "役職" in prompt or "称号" in prompt
        assert "技術用語" in prompt or "専門用語" in prompt
        assert "一般名詞" in prompt


class TestTermExtractorTwoPhase:
    """Test suite for two-phase LLM processing."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock(spec=BaseLLMClient)
        return client

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document."""
        content = """アソリウス島騎士団の団長は勇敢だった。
エデルト軍との戦いが始まった。
未亡人は行方不明になった。"""
        return Document(file_path="/story.md", content=content)

    def test_extract_terms_uses_filter_contained(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that extract_terms uses filter_contained for SudachiPy extraction."""
        mock_classification = TermClassificationResponse(
            classified_terms={
                "organization": ["アソリウス島騎士団", "エデルト軍"],
                "title": ["団長"],
            }
        )
        mock_judgment = MockTermJudgmentResponse(
            approved_terms=["アソリウス島騎士団", "エデルト軍", "団長"]
        )
        mock_llm_client.generate_structured.side_effect = [
            mock_classification,
            mock_judgment,
        ]

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = [
                "アソリウス島騎士団",
                "エデルト軍",
            ]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            extractor.extract_terms([sample_document])

            # Verify filter_contained=True was passed
            call_kwargs = mock_analyzer.extract_proper_nouns.call_args[1]
            assert call_kwargs.get("filter_contained") is True

    def test_extract_terms_excludes_common_nouns(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that common nouns are excluded from final results."""
        mock_classification = TermClassificationResponse(
            classified_terms={
                "organization": ["アソリウス島騎士団"],
                "common_noun": ["未亡人", "行方不明"],
            }
        )
        # Note: Second phase should not include common nouns
        mock_judgment = MockTermJudgmentResponse(
            approved_terms=["アソリウス島騎士団"]
        )
        mock_llm_client.generate_structured.side_effect = [
            mock_classification,
            mock_judgment,
        ]

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = [
                "アソリウス島騎士団",
                "未亡人",
                "行方不明",
            ]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            result = extractor.extract_terms([sample_document])

            # Common nouns should not be in the result
            assert "未亡人" not in result
            assert "行方不明" not in result
            # Organization should be included
            assert "アソリウス島騎士団" in result

    def test_extract_terms_two_phase_calls_llm_twice(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that extract_terms makes two LLM calls (classify + select)."""
        mock_classification = TermClassificationResponse(
            classified_terms={
                "organization": ["アソリウス島騎士団"],
                "title": ["団長"],
            }
        )
        mock_judgment = MockTermJudgmentResponse(
            approved_terms=["アソリウス島騎士団", "団長"]
        )
        mock_llm_client.generate_structured.side_effect = [
            mock_classification,
            mock_judgment,
        ]

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = [
                "アソリウス島騎士団",
                "団長",
            ]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            extractor.extract_terms([sample_document])

            # Should call LLM twice: once for classification, once for selection
            assert mock_llm_client.generate_structured.call_count == 2
