"""Tests for cancellation responsiveness in GlossaryGenerator, GlossaryRefiner, and GlossaryReviewer.

These tests verify that:
1. cancel_event parameter is accepted by all LLM processing classes
2. Cancellation checks occur between LLM calls (inside loops)
3. Early return happens when cancellation is detected
"""

from threading import Event
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term


class MockDefinitionResponse(BaseModel):
    """Mock response model for definition generation."""

    definition: str
    confidence: float


class MockRefinementResponse(BaseModel):
    """Mock response model for refinement."""

    refined_definition: str
    confidence: float


class MockReviewResponse(BaseModel):
    """Mock response model for review."""

    issues: list[dict]


class TestGlossaryGeneratorCancellation:
    """Test suite for GlossaryGenerator cancellation responsiveness."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        return MagicMock(spec=BaseLLMClient)

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        content = """GenGlossary is a tool.
LLM is a language model.
API is an interface.
SDK is a software kit.
"""
        return Document(file_path="/path/to/doc.md", content=content)

    @pytest.fixture
    def cancel_event(self) -> Event:
        """Create a cancel event."""
        return Event()

    def test_generate_accepts_cancel_event_parameter(
        self, mock_llm_client: MagicMock, sample_document: Document, cancel_event: Event
    ) -> None:
        """Test that generate() accepts cancel_event as a parameter."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)

        # Should not raise TypeError
        result = generator.generate(
            ["GenGlossary"], [sample_document], cancel_event=cancel_event
        )

        assert isinstance(result, Glossary)

    def test_generate_returns_early_when_cancelled_before_start(
        self, mock_llm_client: MagicMock, sample_document: Document, cancel_event: Event
    ) -> None:
        """Test that generate() returns empty glossary when cancelled before start."""
        cancel_event.set()  # Cancel before calling generate

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        result = generator.generate(
            ["GenGlossary", "LLM"], [sample_document], cancel_event=cancel_event
        )

        # Should return empty glossary
        assert result.term_count == 0
        # LLM should not be called
        mock_llm_client.generate_structured.assert_not_called()

    def test_generate_stops_processing_when_cancelled_between_terms(
        self, mock_llm_client: MagicMock, sample_document: Document, cancel_event: Event
    ) -> None:
        """Test that generate() stops processing when cancelled between terms."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Cancel after first term is processed
            if call_count == 1:
                cancel_event.set()
            return MockDefinitionResponse(definition="Test definition", confidence=0.9)

        mock_llm_client.generate_structured.side_effect = side_effect

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        terms = ["GenGlossary", "LLM", "API", "SDK"]  # 4 terms
        result = generator.generate(terms, [sample_document], cancel_event=cancel_event)

        # Should have processed only 1 term (stopped after first)
        assert result.term_count == 1
        assert result.has_term("GenGlossary")
        assert not result.has_term("LLM")
        # LLM should be called only once
        assert mock_llm_client.generate_structured.call_count == 1

    def test_generate_processes_all_terms_when_not_cancelled(
        self, mock_llm_client: MagicMock, sample_document: Document, cancel_event: Event
    ) -> None:
        """Test that generate() processes all terms when not cancelled."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        terms = ["GenGlossary", "LLM", "API"]
        result = generator.generate(terms, [sample_document], cancel_event=cancel_event)

        # All terms should be processed
        assert result.term_count == 3
        assert mock_llm_client.generate_structured.call_count == 3

    def test_generate_works_without_cancel_event_backward_compatible(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate() works without cancel_event (backward compatibility)."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        # Call without cancel_event parameter
        result = generator.generate(["GenGlossary"], [sample_document])

        assert result.term_count == 1


class TestGlossaryRefinerCancellation:
    """Test suite for GlossaryRefiner cancellation responsiveness."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        return MagicMock(spec=BaseLLMClient)

    @pytest.fixture
    def sample_glossary(self) -> Glossary:
        """Create a sample glossary with multiple terms."""
        glossary = Glossary()
        for i in range(4):
            glossary.add_term(
                Term(name=f"Term{i+1}", definition=f"Definition {i+1}", confidence=0.7)
            )
        return glossary

    @pytest.fixture
    def sample_issues(self) -> list[GlossaryIssue]:
        """Create sample issues for multiple terms."""
        return [
            GlossaryIssue(term_name=f"Term{i+1}", issue_type="unclear", description=f"Issue {i+1}")
            for i in range(4)
        ]

    @pytest.fixture
    def sample_documents(self) -> list[Document]:
        """Create sample documents."""
        return [
            Document(
                file_path="/test.md",
                content="Term1 Term2 Term3 Term4 content here.",
            )
        ]

    @pytest.fixture
    def cancel_event(self) -> Event:
        """Create a cancel event."""
        return Event()

    def test_refine_accepts_cancel_event_parameter(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
        cancel_event: Event,
    ) -> None:
        """Test that refine() accepts cancel_event as a parameter."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="Improved definition", confidence=0.9
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)

        # Should not raise TypeError
        result = refiner.refine(
            sample_glossary, sample_issues[:1], sample_documents, cancel_event=cancel_event
        )

        assert isinstance(result, Glossary)

    def test_refine_returns_early_when_cancelled_before_start(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
        cancel_event: Event,
    ) -> None:
        """Test that refine() returns unchanged glossary when cancelled before start."""
        cancel_event.set()  # Cancel before calling refine

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(
            sample_glossary, sample_issues, sample_documents, cancel_event=cancel_event
        )

        # Should return glossary without refinement
        assert result.term_count == sample_glossary.term_count
        # LLM should not be called
        mock_llm_client.generate_structured.assert_not_called()

    def test_refine_stops_processing_when_cancelled_between_issues(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
        cancel_event: Event,
    ) -> None:
        """Test that refine() stops processing when cancelled between issues."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Cancel after first issue is processed
            if call_count == 1:
                cancel_event.set()
            return MockRefinementResponse(
                refined_definition="Improved definition", confidence=0.9
            )

        mock_llm_client.generate_structured.side_effect = side_effect

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(
            sample_glossary, sample_issues, sample_documents, cancel_event=cancel_event
        )

        # Should have processed only 1 issue
        # LLM should be called only once
        assert mock_llm_client.generate_structured.call_count == 1
        # Only Term1 should be refined
        term1 = result.get_term("Term1")
        assert term1 is not None
        assert term1.definition == "Improved definition"
        # Term2 should NOT be refined
        term2 = result.get_term("Term2")
        assert term2 is not None
        assert term2.definition == "Definition 2"  # Original

    def test_refine_processes_all_issues_when_not_cancelled(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
        cancel_event: Event,
    ) -> None:
        """Test that refine() processes all issues when not cancelled."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="Improved definition", confidence=0.9
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        refiner.refine(
            sample_glossary, sample_issues, sample_documents, cancel_event=cancel_event
        )

        # All issues should be processed
        assert mock_llm_client.generate_structured.call_count == 4

    def test_refine_works_without_cancel_event_backward_compatible(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
    ) -> None:
        """Test that refine() works without cancel_event (backward compatibility)."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="Improved definition", confidence=0.9
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        # Call without cancel_event parameter
        result = refiner.refine(sample_glossary, sample_issues[:1], sample_documents)

        assert result.term_count == sample_glossary.term_count


class TestGlossaryReviewerCancellation:
    """Test suite for GlossaryReviewer cancellation responsiveness."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        return MagicMock(spec=BaseLLMClient)

    @pytest.fixture
    def sample_glossary(self) -> Glossary:
        """Create a sample glossary for testing."""
        glossary = Glossary()
        glossary.add_term(Term(name="GenGlossary", definition="A tool", confidence=0.9))
        glossary.add_term(Term(name="LLM", definition="Language model", confidence=0.85))
        return glossary

    @pytest.fixture
    def cancel_event(self) -> Event:
        """Create a cancel event."""
        return Event()

    def test_review_accepts_cancel_event_parameter(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary, cancel_event: Event
    ) -> None:
        """Test that review() accepts cancel_event as a parameter."""
        mock_llm_client.generate_structured.return_value = MockReviewResponse(issues=[])

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)

        # Should not raise TypeError
        result = reviewer.review(sample_glossary, cancel_event=cancel_event)

        assert isinstance(result, list)

    def test_review_returns_early_when_cancelled_before_start(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary, cancel_event: Event
    ) -> None:
        """Test that review() returns empty list when cancelled before start."""
        cancel_event.set()  # Cancel before calling review

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        result = reviewer.review(sample_glossary, cancel_event=cancel_event)

        # Should return empty list
        assert result == []
        # LLM should not be called
        mock_llm_client.generate_structured.assert_not_called()

    def test_review_calls_llm_when_not_cancelled(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary, cancel_event: Event
    ) -> None:
        """Test that review() calls LLM when not cancelled."""
        mock_llm_client.generate_structured.return_value = MockReviewResponse(
            issues=[{"term": "GenGlossary", "issue_type": "unclear", "description": "Issue"}]
        )

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        result = reviewer.review(sample_glossary, cancel_event=cancel_event)

        # LLM should be called
        mock_llm_client.generate_structured.assert_called_once()
        assert len(result) == 1

    def test_review_works_without_cancel_event_backward_compatible(
        self, mock_llm_client: MagicMock, sample_glossary: Glossary
    ) -> None:
        """Test that review() works without cancel_event (backward compatibility)."""
        mock_llm_client.generate_structured.return_value = MockReviewResponse(issues=[])

        reviewer = GlossaryReviewer(llm_client=mock_llm_client)
        # Call without cancel_event parameter
        result = reviewer.review(sample_glossary)

        assert isinstance(result, list)
