"""Tests for GlossaryRefiner - Step 4: Refine glossary based on issues."""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term, TermOccurrence


class MockRefinementResponse(BaseModel):
    """Mock response model for refinement."""

    refined_definition: str
    confidence: float


class TestGlossaryRefiner:
    """Test suite for GlossaryRefiner class."""

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
            definition="ツール",  # Intentionally vague
            confidence=0.5,
        )
        term2 = Term(
            name="LLM",
            definition="大規模言語モデル",
            confidence=0.85,
        )

        glossary.add_term(term1)
        glossary.add_term(term2)

        return glossary

    @pytest.fixture
    def sample_issues(self) -> list[GlossaryIssue]:
        """Create sample issues for testing."""
        return [
            GlossaryIssue(
                term_name="GenGlossary",
                issue_type="unclear",
                description="定義が曖昧で具体性に欠ける",
            ),
        ]

    @pytest.fixture
    def sample_documents(self) -> list[Document]:
        """Create sample documents for additional context."""
        return [
            Document(
                file_path="/docs/readme.md",
                content="""GenGlossaryは用語集を自動生成するPythonツールです。
LLMを活用してドキュメントから専門用語を抽出し、定義を生成します。
GenGlossaryはCLIとして動作し、Markdownファイルを出力します。
""",
            )
        ]

    def test_glossary_refiner_initialization(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that GlossaryRefiner can be initialized."""
        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        assert refiner.llm_client == mock_llm_client

    def test_refine_returns_glossary(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
    ) -> None:
        """Test that refine returns a Glossary object."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="用語集を自動生成するPythonツール",
            confidence=0.9,
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(sample_glossary, sample_issues, sample_documents)

        assert isinstance(result, Glossary)

    def test_refine_updates_term_definition(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
    ) -> None:
        """Test that term definitions are updated based on issues."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="ドキュメントから用語集を自動生成するPythonベースのCLIツール",
            confidence=0.92,
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(sample_glossary, sample_issues, sample_documents)

        term = result.get_term("GenGlossary")
        assert term is not None
        assert "自動生成" in term.definition
        assert term.confidence == 0.92

    def test_refine_calls_llm_for_each_issue(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test that LLM is called for each issue."""
        issues = [
            GlossaryIssue(
                term_name="GenGlossary",
                issue_type="unclear",
                description="定義が曖昧",
            ),
            GlossaryIssue(
                term_name="LLM",
                issue_type="missing_relation",
                description="関連用語の欠落",
            ),
        ]

        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="改善された定義",
            confidence=0.9,
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        refiner.refine(sample_glossary, issues, sample_documents)

        assert mock_llm_client.generate_structured.call_count == 2

    def test_resolve_issue_creates_correct_prompt(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test that _resolve_issue creates prompt with all necessary info."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="改善された定義",
            confidence=0.9,
        )

        issue = GlossaryIssue(
            term_name="GenGlossary",
            issue_type="unclear",
            description="定義が曖昧",
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        term = sample_glossary.get_term("GenGlossary")
        assert term is not None

        refiner._resolve_issue(term, issue, sample_documents)

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # Check prompt contains required elements
        assert "GenGlossary" in prompt
        assert "ツール" in prompt  # Current definition
        assert "定義が曖昧" in prompt  # Issue description

    def test_create_refinement_prompt_includes_additional_context(
        self,
        mock_llm_client: MagicMock,
        sample_documents: list[Document],
    ) -> None:
        """Test that refinement prompt includes context from documents."""
        term = Term(name="GenGlossary", definition="ツール", confidence=0.5)
        issue = GlossaryIssue(
            term_name="GenGlossary",
            issue_type="unclear",
            description="定義が曖昧",
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        prompt = refiner._create_refinement_prompt(term, issue, sample_documents)

        # Should include document content for additional context
        assert "GenGlossary" in prompt
        assert "用語集を自動生成" in prompt or "追加コンテキスト" in prompt

    def test_create_refinement_prompt_specifies_json_format(
        self,
        mock_llm_client: MagicMock,
        sample_documents: list[Document],
    ) -> None:
        """Test that prompt specifies JSON output format."""
        term = Term(name="TestTerm", definition="Test def", confidence=0.5)
        issue = GlossaryIssue(
            term_name="TestTerm",
            issue_type="unclear",
            description="Test issue",
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        prompt = refiner._create_refinement_prompt(term, issue, sample_documents)

        assert "JSON" in prompt or "json" in prompt
        assert "refined_definition" in prompt

    def test_refine_handles_empty_issues_list(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test that empty issues list returns unchanged glossary."""
        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(sample_glossary, [], sample_documents)

        assert result.term_count == sample_glossary.term_count
        mock_llm_client.generate_structured.assert_not_called()

    def test_refine_handles_issue_for_nonexistent_term(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test that issues for nonexistent terms are skipped."""
        issues = [
            GlossaryIssue(
                term_name="NonExistent",
                issue_type="unclear",
                description="This term doesn't exist",
            ),
        ]

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(sample_glossary, issues, sample_documents)

        assert result.term_count == sample_glossary.term_count
        mock_llm_client.generate_structured.assert_not_called()

    def test_refine_preserves_unchanged_terms(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
    ) -> None:
        """Test that terms without issues are preserved unchanged."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="改善された定義",
            confidence=0.9,
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(sample_glossary, sample_issues, sample_documents)

        # LLM term should be unchanged
        llm_term = result.get_term("LLM")
        assert llm_term is not None
        assert llm_term.definition == "大規模言語モデル"
        assert llm_term.confidence == 0.85

    def test_refine_updates_glossary_issues(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_issues: list[GlossaryIssue],
        sample_documents: list[Document],
    ) -> None:
        """Test that resolved issues are added to glossary metadata."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="改善された定義",
            confidence=0.9,
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(sample_glossary, sample_issues, sample_documents)

        # Glossary should track that issues were resolved
        assert "resolved_issues" in result.metadata or result.issue_count == 0

    def test_refine_handles_multiple_issues_for_same_term(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test handling multiple issues for the same term."""
        issues = [
            GlossaryIssue(
                term_name="GenGlossary",
                issue_type="unclear",
                description="定義が曖昧",
            ),
            GlossaryIssue(
                term_name="GenGlossary",
                issue_type="missing_relation",
                description="関連用語の欠落",
            ),
        ]

        mock_llm_client.generate_structured.side_effect = [
            MockRefinementResponse(
                refined_definition="第一回改善",
                confidence=0.8,
            ),
            MockRefinementResponse(
                refined_definition="第二回改善",
                confidence=0.9,
            ),
        ]

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(sample_glossary, issues, sample_documents)

        term = result.get_term("GenGlossary")
        assert term is not None
        # Should have the latest refinement
        assert term.definition == "第二回改善"
        assert term.confidence == 0.9

    def test_refine_preserves_occurrences(
        self,
        mock_llm_client: MagicMock,
        sample_documents: list[Document],
    ) -> None:
        """Test that term occurrences are preserved during refinement."""
        glossary = Glossary()
        term = Term(
            name="TestTerm",
            definition="Original definition",
            occurrences=[
                TermOccurrence(
                    document_path="/test.md",
                    line_number=1,
                    context="Test context",
                )
            ],
            confidence=0.5,
        )
        glossary.add_term(term)

        issues = [
            GlossaryIssue(
                term_name="TestTerm",
                issue_type="unclear",
                description="Definition unclear",
            ),
        ]

        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="Improved definition",
            confidence=0.9,
        )

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        result = refiner.refine(glossary, issues, sample_documents)

        refined_term = result.get_term("TestTerm")
        assert refined_term is not None
        assert refined_term.occurrence_count == 1
        assert refined_term.occurrences[0].context == "Test context"


class TestGlossaryRefinerProgressCallback:
    """Test suite for GlossaryRefiner progress callback functionality."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        return MagicMock(spec=BaseLLMClient)

    @pytest.fixture
    def sample_glossary(self) -> Glossary:
        """Create a sample glossary for testing."""
        glossary = Glossary()
        glossary.add_term(
            Term(name="Term1", definition="Definition 1", confidence=0.8)
        )
        glossary.add_term(
            Term(name="Term2", definition="Definition 2", confidence=0.7)
        )
        glossary.add_term(
            Term(name="Term3", definition="Definition 3", confidence=0.9)
        )
        return glossary

    @pytest.fixture
    def sample_documents(self) -> list[Document]:
        """Create sample documents for testing."""
        return [
            Document(
                file_path="/test.md",
                content="Term1 and Term2 and Term3 are all here.",
            )
        ]

    def test_refine_calls_progress_callback(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test that refine calls progress callback for each issue."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="Improved definition",
            confidence=0.9,
        )

        issues = [
            GlossaryIssue(term_name="Term1", issue_type="unclear", description="Issue 1"),
            GlossaryIssue(term_name="Term2", issue_type="unclear", description="Issue 2"),
        ]

        callback_calls: list[tuple[int, int]] = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        refiner.refine(sample_glossary, issues, sample_documents, progress_callback=progress_callback)

        assert len(callback_calls) == 2
        assert callback_calls[0] == (1, 2)
        assert callback_calls[1] == (2, 2)

    def test_refine_works_without_callback(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test that refine works without progress callback."""
        mock_llm_client.generate_structured.return_value = MockRefinementResponse(
            refined_definition="Improved definition",
            confidence=0.9,
        )

        issues = [
            GlossaryIssue(term_name="Term1", issue_type="unclear", description="Issue 1"),
        ]

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        # Should not raise even without callback
        result = refiner.refine(sample_glossary, issues, sample_documents)

        assert result is not None
        assert result.has_term("Term1")

    def test_refine_callback_on_empty_issues(
        self,
        mock_llm_client: MagicMock,
        sample_glossary: Glossary,
        sample_documents: list[Document],
    ) -> None:
        """Test that callback is not called when issues list is empty."""
        callback_calls: list[tuple[int, int]] = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        refiner = GlossaryRefiner(llm_client=mock_llm_client)
        refiner.refine(sample_glossary, [], sample_documents, progress_callback=progress_callback)

        assert len(callback_calls) == 0
