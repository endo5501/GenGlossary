"""Tests for GlossaryReviewer - Step 3: Review glossary for issues."""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.base import BaseLLMClient
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term


class MockReviewResponse(BaseModel):
    """Mock response model for review."""

    issues: list[dict[str, str]]


class TestGlossaryReviewer:
    """Test suite for GlossaryReviewer class."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        return MagicMock(spec=BaseLLMClient)

    @pytest.fixture
    def sample_glossary(self) -> Glossary:
        """Create a sample glossary for testing."""
        glossary = Glossary()

        term1 = Term(
            name="GenGlossary",
            definition="用語集を自動生成するツール",
            confidence=0.9,
        )
        term2 = Term(
            name="LLM",
            definition="大規模言語モデル",
            confidence=0.85,
        )
        term3 = Term(
            name="API",
            definition="アプリケーションプログラミングインターフェース",
            confidence=0.7,
        )

        glossary.add_term(term1)
        glossary.add_term(term2)
        glossary.add_term(term3)

        return glossary

    def test_glossary_reviewer_initialization(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that GlossaryReviewer can be initialized."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        assert reviewer.llm_client == mock_llm_client

    def test_review_returns_list_of_issues(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that review returns a list of GlossaryIssue objects."""
        mock_llm_client.generate_structured.return_value = MockReviewResponse(
            issues=[
                {
                    "term": "API",
                    "issue_type": "unclear",
                    "description": "定義が一般的すぎる",
                }
            ]
        )

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        issues = reviewer.review(sample_glossary)

        assert isinstance(issues, list)
        assert all(isinstance(issue, GlossaryIssue) for issue in issues)

    def test_review_extracts_issues_from_llm_response(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that issues are correctly extracted from LLM response."""
        mock_llm_client.generate_structured.return_value = MockReviewResponse(
            issues=[
                {
                    "term": "API",
                    "issue_type": "unclear",
                    "description": "定義が一般的すぎる",
                },
                {
                    "term": "LLM",
                    "issue_type": "missing_relation",
                    "description": "GenGlossaryとの関係が不明",
                },
            ]
        )

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        issues = reviewer.review(sample_glossary)

        assert len(issues) == 2
        assert issues[0].term_name == "API"
        assert issues[0].issue_type == "unclear"
        assert issues[1].term_name == "LLM"
        assert issues[1].issue_type == "missing_relation"

    def test_review_calls_llm_with_glossary_content(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that LLM is called with glossary content in prompt."""
        mock_llm_client.generate_structured.return_value = MockReviewResponse(
            issues=[]
        )

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        reviewer.review(sample_glossary)

        mock_llm_client.generate_structured.assert_called_once()
        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # Check that prompt contains term information
        assert "GenGlossary" in prompt
        assert "LLM" in prompt
        assert "API" in prompt
        assert "用語集を自動生成するツール" in prompt

    def test_create_review_prompt_includes_all_terms(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that review prompt includes all terms and definitions."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        prompt = reviewer._create_review_prompt(sample_glossary)

        for term_name in sample_glossary.all_term_names:
            assert term_name in prompt
            term = sample_glossary.get_term(term_name)
            assert term is not None
            assert term.definition in prompt

    def test_create_review_prompt_specifies_json_format(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that prompt specifies JSON output format."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        prompt = reviewer._create_review_prompt(sample_glossary)

        assert "JSON" in prompt or "json" in prompt
        assert "issues" in prompt

    def test_create_review_prompt_includes_review_criteria(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that prompt includes review criteria."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        prompt = reviewer._create_review_prompt(sample_glossary)

        # Should mention issue types or review criteria
        assert "曖昧" in prompt or "unclear" in prompt or "不明確" in prompt
        assert "矛盾" in prompt or "contradiction" in prompt

    def test_parse_issues_handles_valid_response(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test parsing of valid issue response."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)

        raw_issues = [
            {
                "term": "TestTerm",
                "issue_type": "unclear",
                "description": "Test description",
            }
        ]

        issues = reviewer._parse_issues(raw_issues)

        assert len(issues) == 1
        assert issues[0].term_name == "TestTerm"
        assert issues[0].issue_type == "unclear"
        assert issues[0].description == "Test description"

    def test_parse_issues_handles_all_issue_types(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test parsing of all valid issue types."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)

        raw_issues = [
            {"term": "Term1", "issue_type": "unclear", "description": "Desc1"},
            {"term": "Term2", "issue_type": "contradiction", "description": "Desc2"},
            {"term": "Term3", "issue_type": "missing_relation", "description": "Desc3"},
        ]

        issues = reviewer._parse_issues(raw_issues)

        assert len(issues) == 3
        assert issues[0].issue_type == "unclear"
        assert issues[1].issue_type == "contradiction"
        assert issues[2].issue_type == "missing_relation"

    def test_parse_issues_skips_invalid_issue_type(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that invalid issue types are skipped."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)

        raw_issues = [
            {"term": "Term1", "issue_type": "unclear", "description": "Valid"},
            {"term": "Term2", "issue_type": "invalid_type", "description": "Invalid"},
            {"term": "Term3", "issue_type": "contradiction", "description": "Valid"},
        ]

        issues = reviewer._parse_issues(raw_issues)

        assert len(issues) == 2
        assert all(issue.issue_type in ["unclear", "contradiction", "missing_relation"] for issue in issues)

    def test_parse_issues_handles_missing_fields(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that issues with missing fields are skipped."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)

        raw_issues = [
            {"term": "Term1", "issue_type": "unclear", "description": "Valid"},
            {"term": "Term2", "description": "Missing issue_type"},  # Missing issue_type
            {"issue_type": "unclear", "description": "Missing term"},  # Missing term
            {"term": "Term4", "issue_type": "unclear"},  # Missing description
        ]

        issues = reviewer._parse_issues(raw_issues)

        assert len(issues) == 1

    def test_review_returns_empty_list_for_no_issues(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that empty list is returned when no issues found."""
        mock_llm_client.generate_structured.return_value = MockReviewResponse(
            issues=[]
        )

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        issues = reviewer.review(sample_glossary)

        assert issues == []

    def test_review_handles_empty_glossary(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that empty glossary returns empty issues list."""
        empty_glossary = Glossary()

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        issues = reviewer.review(empty_glossary)

        assert issues == []
        mock_llm_client.generate_structured.assert_not_called()

    def test_review_includes_low_confidence_in_prompt(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that low confidence terms are highlighted in prompt."""
        glossary = Glossary()
        glossary.add_term(
            Term(name="HighConf", definition="Clear definition", confidence=0.95)
        )
        glossary.add_term(
            Term(name="LowConf", definition="Unclear definition", confidence=0.3)
        )

        mock_llm_client.generate_structured.return_value = MockReviewResponse(
            issues=[]
        )

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        reviewer.review(glossary)

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # Should indicate confidence levels
        assert "0.95" in prompt or "95" in prompt or "0.3" in prompt or "30" in prompt

    def test_parse_issues_handles_should_exclude(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that should_exclude is correctly parsed."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        raw_issues = [
            {
                "term": "一般語",
                "issue_type": "unnecessary",
                "description": "不要な用語",
                "should_exclude": True,
                "exclusion_reason": "一般語彙",
            }
        ]
        issues = reviewer._parse_issues(raw_issues)
        assert len(issues) == 1
        assert issues[0].should_exclude is True
        assert issues[0].exclusion_reason == "一般語彙"

    def test_parse_issues_defaults_should_exclude_to_false(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that should_exclude defaults to False when not provided."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        raw_issues = [
            {"term": "TestTerm", "issue_type": "unclear", "description": "定義が曖昧"}
        ]
        issues = reviewer._parse_issues(raw_issues)
        assert len(issues) == 1
        assert issues[0].should_exclude is False

    def test_create_review_prompt_includes_necessity_judgment(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that prompt includes criteria for term necessity judgment."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        prompt = reviewer._create_review_prompt(sample_glossary)
        # Should mention unnecessary or exclusion criteria
        assert "unnecessary" in prompt or "不要" in prompt
        assert "should_exclude" in prompt

    def test_prompt_uses_strict_exclusion_criteria(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that prompt says 'exclude when in doubt'."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        prompt = reviewer._create_review_prompt(sample_glossary)

        assert "迷った場合は除外" in prompt
        assert "含める方向で判断" not in prompt

    def test_prompt_includes_exclusion_examples(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that prompt includes few-shot examples of terms to exclude."""
        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        prompt = reviewer._create_review_prompt(sample_glossary)

        # Should include exclusion examples
        assert "除外基準" in prompt or "❌" in prompt
