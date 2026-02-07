"""Tests for TermExtractor required terms functionality."""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from genglossary.db.required_term_repository import add_required_term
from genglossary.db.excluded_term_repository import add_excluded_term
from genglossary.db.schema import initialize_db
from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.term_extractor import (
    BatchTermClassificationResponse,
    TermExtractor,
)


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    return MagicMock(spec=BaseLLMClient)


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    content = """東京は日本の首都です。
トヨタ自動車は愛知県に本社があります。
量子コンピュータは革新的な技術です。
"""
    return Document(file_path="/path/to/doc.md", content=content)


@pytest.fixture
def db_connection() -> sqlite3.Connection:
    """Create an in-memory database with schema initialized."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    initialize_db(conn)
    return conn


class TestTermExtractorWithRequiredRepo:
    """Test suite for TermExtractor with required_term_repo."""

    def test_initialization_with_required_term_repo(
        self, mock_llm_client: MagicMock, db_connection: sqlite3.Connection
    ) -> None:
        """Test that TermExtractor can be initialized with required_term_repo."""
        extractor = TermExtractor(
            llm_client=mock_llm_client,
            required_term_repo=db_connection,
        )

        assert extractor._required_term_repo is db_connection

    def test_initialization_without_required_term_repo(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that TermExtractor works without required_term_repo (backward compatible)."""
        extractor = TermExtractor(llm_client=mock_llm_client)

        assert extractor._required_term_repo is None


class TestRequiredTermsMerge:
    """Test suite for merging required terms into candidates."""

    def test_required_terms_merged_into_candidates(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        db_connection: sqlite3.Connection,
    ) -> None:
        """Test that required terms are merged into candidates before LLM classification."""
        add_required_term(db_connection, "量子コンピュータ", "manual")

        mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
            classifications=[
                {"term": "東京", "category": "place_name"},
                {"term": "量子コンピュータ", "category": "technical_term"},
            ]
        )

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            # SudachiPy only returns 東京 (量子コンピュータ was not detected)
            mock_analyzer.extract_proper_nouns.return_value = ["東京"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(
                llm_client=mock_llm_client,
                required_term_repo=db_connection,
            )
            result = extractor.extract_terms([sample_document])

            # Required term should be in the final result even if SudachiPy missed it
            assert "量子コンピュータ" in result
            assert "東京" in result

    def test_required_terms_sent_to_llm(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        db_connection: sqlite3.Connection,
    ) -> None:
        """Test that required terms are included in LLM classification prompt."""
        add_required_term(db_connection, "必須用語テスト", "manual")

        mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
            classifications=[
                {"term": "東京", "category": "place_name"},
                {"term": "必須用語テスト", "category": "technical_term"},
            ]
        )

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = ["東京"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(
                llm_client=mock_llm_client,
                required_term_repo=db_connection,
            )
            extractor.extract_terms([sample_document])

            # Required term should be in the LLM prompt
            call_args = mock_llm_client.generate_structured.call_args
            prompt = call_args[0][0]
            assert "必須用語テスト" in prompt

    def test_required_terms_not_duplicated_if_already_candidate(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        db_connection: sqlite3.Connection,
    ) -> None:
        """Test that required terms already in candidates are not duplicated."""
        add_required_term(db_connection, "東京", "manual")

        mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
            classifications=[
                {"term": "東京", "category": "place_name"},
            ]
        )

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = ["東京"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(
                llm_client=mock_llm_client,
                required_term_repo=db_connection,
            )
            result = extractor.extract_terms([sample_document])

            # Should appear only once
            assert result.count("東京") == 1


class TestRequiredTermsGuardAgainstCommonNoun:
    """Test suite for required terms being protected from common_noun exclusion."""

    def test_required_term_not_excluded_even_if_common_noun(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        db_connection: sqlite3.Connection,
    ) -> None:
        """Test that required terms are kept even when LLM classifies as common_noun."""
        add_required_term(db_connection, "量子コンピュータ", "manual")

        mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
            classifications=[
                {"term": "東京", "category": "place_name"},
                {"term": "量子コンピュータ", "category": "common_noun"},
            ]
        )

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = ["東京", "量子コンピュータ"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(
                llm_client=mock_llm_client,
                required_term_repo=db_connection,
            )
            result = extractor.extract_terms([sample_document])

            # Required term should be in result even though classified as common_noun
            assert "量子コンピュータ" in result
            assert "東京" in result

    def test_required_term_not_added_to_exclusion_list(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        db_connection: sqlite3.Connection,
    ) -> None:
        """Test that required terms classified as common_noun are NOT added to exclusion list."""
        from genglossary.db.excluded_term_repository import get_excluded_term_texts

        add_required_term(db_connection, "量子コンピュータ", "manual")

        mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
            classifications=[
                {"term": "量子コンピュータ", "category": "common_noun"},
                {"term": "未亡人", "category": "common_noun"},
            ]
        )

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = ["量子コンピュータ", "未亡人"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(
                llm_client=mock_llm_client,
                excluded_term_repo=db_connection,
                required_term_repo=db_connection,
            )
            extractor.extract_terms([sample_document])

            excluded_texts = get_excluded_term_texts(db_connection)
            # Required term should NOT be in exclusion list
            assert "量子コンピュータ" not in excluded_texts
            # Non-required common_noun should still be auto-excluded
            assert "未亡人" in excluded_texts


class TestRequiredTermsOverrideExcluded:
    """Test that required terms take priority over excluded terms."""

    def test_required_overrides_excluded(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        db_connection: sqlite3.Connection,
    ) -> None:
        """Test that a term in both required and excluded lists is included (required wins)."""
        add_excluded_term(db_connection, "量子コンピュータ", "auto")
        add_required_term(db_connection, "量子コンピュータ", "manual")

        mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
            classifications=[
                {"term": "量子コンピュータ", "category": "technical_term"},
            ]
        )

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = ["量子コンピュータ"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(
                llm_client=mock_llm_client,
                excluded_term_repo=db_connection,
                required_term_repo=db_connection,
            )
            result = extractor.extract_terms([sample_document])

            # Required term should override exclusion
            assert "量子コンピュータ" in result


class TestRequiredTermsWithNoRepo:
    """Test that TermExtractor works when required_term_repo is None."""

    def test_no_merge_without_repo(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
    ) -> None:
        """Test that no required terms merge happens when repo is None."""
        mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
            classifications=[
                {"term": "東京", "category": "place_name"},
            ]
        )

        with patch(
            "genglossary.term_extractor.MorphologicalAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.extract_proper_nouns.return_value = ["東京"]
            mock_analyzer_class.return_value = mock_analyzer

            extractor = TermExtractor(llm_client=mock_llm_client)
            result = extractor.extract_terms([sample_document])

            assert result == ["東京"]
