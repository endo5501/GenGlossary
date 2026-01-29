"""Tests for GlossaryGenerator - Step 2: Generate provisional glossary."""

import re
from unittest.mock import MagicMock, call

import pytest
from pydantic import BaseModel

from genglossary.glossary_generator import GlossaryGenerator
from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.models.term import ClassifiedTerm, Term, TermCategory, TermOccurrence


class MockDefinitionResponse(BaseModel):
    """Mock response model for definition generation."""

    definition: str
    confidence: float


class TestGlossaryGenerator:
    """Test suite for GlossaryGenerator class."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        return MagicMock(spec=BaseLLMClient)

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        content = """GenGlossaryは用語集を自動生成するツールです。
LLMを活用して、ドキュメントから用語を抽出します。
GenGlossaryはPythonで実装されています。
LLMは大規模言語モデルの略称です。
"""
        return Document(file_path="/path/to/doc.md", content=content)

    @pytest.fixture
    def sample_terms(self) -> list[str]:
        """Create sample terms for testing."""
        return ["GenGlossary", "LLM"]

    def test_glossary_generator_initialization(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that GlossaryGenerator can be initialized."""
        generator = GlossaryGenerator(llm_client=mock_llm_client)
        assert generator.llm_client == mock_llm_client

    def test_generate_returns_glossary(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        sample_terms: list[str],
    ) -> None:
        """Test that generate returns a Glossary object."""
        mock_llm_client.generate_structured.side_effect = [
            MockDefinitionResponse(
                definition="用語集を自動生成するツール", confidence=0.9
            ),
            MockDefinitionResponse(
                definition="大規模言語モデルの略称", confidence=0.85
            ),
        ]

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        result = generator.generate(sample_terms, [sample_document])

        assert isinstance(result, Glossary)

    def test_generate_creates_terms_with_definitions(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
        sample_terms: list[str],
    ) -> None:
        """Test that generated glossary contains terms with definitions."""
        mock_llm_client.generate_structured.side_effect = [
            MockDefinitionResponse(
                definition="用語集を自動生成するツール", confidence=0.9
            ),
            MockDefinitionResponse(
                definition="大規模言語モデルの略称", confidence=0.85
            ),
        ]

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        result = generator.generate(sample_terms, [sample_document])

        assert result.has_term("GenGlossary")
        assert result.has_term("LLM")

        genglossary_term = result.get_term("GenGlossary")
        assert genglossary_term is not None
        assert genglossary_term.definition == "用語集を自動生成するツール"
        assert genglossary_term.confidence == 0.9

    def test_find_term_occurrences_basic(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test finding term occurrences in a document."""
        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = generator._find_term_occurrences(
            "GenGlossary", [sample_document]
        )

        assert len(occurrences) == 2  # GenGlossary appears twice
        assert all(isinstance(occ, TermOccurrence) for occ in occurrences)
        assert occurrences[0].line_number == 1
        assert occurrences[1].line_number == 3

    def test_find_term_occurrences_with_context(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that occurrences include surrounding context."""
        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = generator._find_term_occurrences("LLM", [sample_document])

        assert len(occurrences) == 2
        # Each occurrence should have context
        for occ in occurrences:
            assert "LLM" in occ.context
            assert occ.context.strip() != ""

    def test_find_term_occurrences_case_sensitive(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that term search is case-sensitive by default."""
        doc = Document(
            file_path="/test.md",
            content="LLM is great.\nllm is lowercase.\nLLM again.",
        )
        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = generator._find_term_occurrences("LLM", [doc])

        # Should only find exact case matches
        assert len(occurrences) == 2
        assert occurrences[0].line_number == 1
        assert occurrences[1].line_number == 3

    def test_find_term_occurrences_word_boundary(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that term search respects word boundaries."""
        doc = Document(
            file_path="/test.md",
            content="API is an interface.\nAPIKey is different.\nThe API works.",
        )
        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = generator._find_term_occurrences("API", [doc])

        # Should find standalone API, not APIKey
        assert len(occurrences) == 2
        assert occurrences[0].line_number == 1
        assert occurrences[1].line_number == 3

    def test_find_term_occurrences_multiple_documents(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test finding occurrences across multiple documents."""
        doc1 = Document(file_path="/doc1.md", content="First LLM mention.")
        doc2 = Document(file_path="/doc2.md", content="Second LLM mention.")

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = generator._find_term_occurrences("LLM", [doc1, doc2])

        assert len(occurrences) == 2
        assert occurrences[0].document_path == "/doc1.md"
        assert occurrences[1].document_path == "/doc2.md"

    def test_generate_definition_calls_llm(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
    ) -> None:
        """Test that _generate_definition calls LLM with correct prompt."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.8
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = [
            TermOccurrence(
                document_path="/test.md",
                line_number=1,
                context="Test context for term.",
            )
        ]

        definition, confidence = generator._generate_definition(
            "TestTerm", occurrences
        )

        assert definition == "Test definition"
        assert confidence == 0.8
        mock_llm_client.generate_structured.assert_called_once()

    def test_generate_definition_prompt_contains_term_and_context(
        self,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test that definition prompt includes term and context."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.8
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = [
            TermOccurrence(
                document_path="/test.md",
                line_number=1,
                context="Context with MyTerm usage.",
            )
        ]

        generator._generate_definition("MyTerm", occurrences)

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        assert "MyTerm" in prompt
        assert "Context with MyTerm usage" in prompt

    def test_generate_sets_occurrences(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
    ) -> None:
        """Test that generated terms have occurrences populated."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Definition", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        result = generator.generate(["GenGlossary"], [sample_document])

        term = result.get_term("GenGlossary")
        assert term is not None
        assert term.occurrence_count == 2
        assert term.occurrences[0].document_path == "/path/to/doc.md"

    def test_generate_handles_empty_terms_list(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
    ) -> None:
        """Test that empty terms list returns empty glossary."""
        generator = GlossaryGenerator(llm_client=mock_llm_client)
        result = generator.generate([], [sample_document])

        assert isinstance(result, Glossary)
        assert result.term_count == 0
        mock_llm_client.generate_structured.assert_not_called()

    def test_generate_handles_term_not_found_in_documents(
        self,
        mock_llm_client: MagicMock,
        sample_document: Document,
    ) -> None:
        """Test handling of terms not found in any document."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Unknown term definition", confidence=0.5
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        result = generator.generate(["NonExistentTerm"], [sample_document])

        term = result.get_term("NonExistentTerm")
        assert term is not None
        assert term.occurrence_count == 0

    def test_generate_handles_japanese_terms(
        self,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test that Japanese terms are handled correctly."""
        doc = Document(
            file_path="/test.md",
            content="用語集は便利です。\n用語集を自動生成します。",
        )
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="単語とその定義のリスト", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        result = generator.generate(["用語集"], [doc])

        term = result.get_term("用語集")
        assert term is not None
        assert term.occurrence_count == 2
        assert term.definition == "単語とその定義のリスト"


class TestGlossaryGeneratorProgressCallback:
    """Test suite for GlossaryGenerator progress callback functionality."""

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
"""
        return Document(file_path="/path/to/doc.md", content=content)

    def test_generate_calls_progress_callback(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate calls progress callback for each term."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.9
        )

        callback_calls: list[tuple[int, int]] = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        terms = ["GenGlossary", "LLM", "API"]
        generator.generate(terms, [sample_document], progress_callback=progress_callback)

        assert len(callback_calls) == 3
        assert callback_calls[0] == (1, 3)
        assert callback_calls[1] == (2, 3)
        assert callback_calls[2] == (3, 3)

    def test_generate_works_without_callback(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate works without progress callback."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        # Should not raise even without callback
        result = generator.generate(["GenGlossary"], [sample_document])

        assert result.has_term("GenGlossary")

    def test_generate_callback_on_empty_terms(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that callback is not called when terms list is empty."""
        callback_calls: list[tuple[int, int]] = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        generator.generate([], [sample_document], progress_callback=progress_callback)

        assert len(callback_calls) == 0

    def test_definition_prompt_separates_example_from_task(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that definition prompt clearly separates few-shot example from actual task.

        The prompt must structure examples as Input/Output pairs and clearly mark
        the actual task section to prevent LLM from confusing examples with real output.
        """
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.8
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = [
            TermOccurrence(
                document_path="/test.md",
                line_number=1,
                context="Context with MyTerm usage.",
            )
        ]

        generator._generate_definition("MyTerm", occurrences)

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # Prompt should clearly mark examples as examples
        assert "## Example" in prompt or "<example>" in prompt or "例:" in prompt

        # Prompt should have a clear task section after examples
        assert "## Your Task" in prompt or "## 実際のタスク" in prompt or "今回の用語:" in prompt

        # The actual term should appear in task section, not just anywhere
        # Find position of task marker and verify term appears after it
        task_markers = ["## Your Task", "## 実際のタスク", "今回の用語:"]
        task_position = -1
        for marker in task_markers:
            pos = prompt.find(marker)
            if pos != -1:
                task_position = pos
                break

        assert task_position != -1, "No task section marker found in prompt"

        # The actual term should appear after the task marker
        task_section = prompt[task_position:]
        assert "MyTerm" in task_section, "Term should be in task section"

    def test_definition_prompt_example_does_not_appear_in_task_section(
        self, mock_llm_client: MagicMock
    ) -> None:
        """Test that few-shot example content doesn't leak into task section.

        This prevents the LLM from confusing example content with actual task.
        """
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="Test definition", confidence=0.8
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        occurrences = [
            TermOccurrence(
                document_path="/test.md",
                line_number=1,
                context="GenGlossary is a tool.",
            )
        ]

        generator._generate_definition("GenGlossary", occurrences)

        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[0][0]

        # Find task section
        task_markers = ["## Your Task", "## 実際のタスク", "今回の用語:"]
        task_position = -1
        for marker in task_markers:
            pos = prompt.find(marker)
            if pos != -1:
                task_position = pos
                break

        assert task_position != -1, "No task section marker found"

        # Task section should not contain example-specific content
        task_section = prompt[task_position:]

        # The example uses "アソリウス島騎士団" - this should NOT appear in task section
        assert "アソリウス島騎士団" not in task_section, \
            "Example content should not appear in task section"


class TestGlossaryGeneratorClassifiedTerm:
    """Test suite for GlossaryGenerator with ClassifiedTerm support."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create a mock LLM client."""
        return MagicMock(spec=BaseLLMClient)

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        content = """量子コンピュータは計算機です。
量子ビットは量子コンピュータの基本単位です。
普通の計算機とは異なります。"""
        return Document(file_path="/test/doc.txt", content=content)

    def test_generate_accepts_list_of_str(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate() accepts list[str] (existing behavior)."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="量子力学を利用した計算機", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        glossary = generator.generate(["量子コンピュータ"], [sample_document])

        # Should generate glossary with one term
        assert len(glossary.terms) == 1
        assert "量子コンピュータ" in glossary.terms
        assert glossary.terms["量子コンピュータ"].name == "量子コンピュータ"

    def test_generate_accepts_list_of_classified_term(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate() accepts list[ClassifiedTerm]."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="量子力学を利用した計算機", confidence=0.9
        )

        classified_terms = [
            ClassifiedTerm(term="量子コンピュータ", category=TermCategory.TECHNICAL_TERM),
            ClassifiedTerm(term="量子ビット", category=TermCategory.TECHNICAL_TERM),
        ]

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        glossary = generator.generate(classified_terms, [sample_document])

        # Should generate glossary with two terms
        assert len(glossary.terms) == 2
        assert "量子コンピュータ" in glossary.terms
        assert "量子ビット" in glossary.terms
        assert glossary.terms["量子コンピュータ"].name == "量子コンピュータ"
        assert glossary.terms["量子ビット"].name == "量子ビット"

    def test_generate_skip_common_nouns_true_by_default(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate() skips common_noun by default."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="量子力学を利用した計算機", confidence=0.9
        )

        classified_terms = [
            ClassifiedTerm(term="量子コンピュータ", category=TermCategory.TECHNICAL_TERM),
            ClassifiedTerm(term="計算機", category=TermCategory.COMMON_NOUN),
        ]

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        glossary = generator.generate(classified_terms, [sample_document])

        # Should skip common_noun by default
        assert len(glossary.terms) == 1
        assert "量子コンピュータ" in glossary.terms
        assert "計算機" not in glossary.terms
        assert glossary.terms["量子コンピュータ"].name == "量子コンピュータ"

    def test_generate_skip_common_nouns_false_includes_all(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate() includes common_noun when skip_common_nouns=False."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="テスト定義", confidence=0.9
        )

        classified_terms = [
            ClassifiedTerm(term="量子コンピュータ", category=TermCategory.TECHNICAL_TERM),
            ClassifiedTerm(term="計算機", category=TermCategory.COMMON_NOUN),
        ]

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        glossary = generator.generate(
            classified_terms, [sample_document], skip_common_nouns=False
        )

        # Should include all terms when skip_common_nouns=False
        assert len(glossary.terms) == 2
        assert "量子コンピュータ" in glossary.terms
        assert "計算機" in glossary.terms
        assert glossary.terms["量子コンピュータ"].name == "量子コンピュータ"
        assert glossary.terms["計算機"].name == "計算機"

    def test_generate_skip_common_nouns_explicit_true(
        self, mock_llm_client: MagicMock, sample_document: Document
    ) -> None:
        """Test that generate() skips common_noun when skip_common_nouns=True."""
        mock_llm_client.generate_structured.return_value = MockDefinitionResponse(
            definition="量子力学を利用した計算機", confidence=0.9
        )

        classified_terms = [
            ClassifiedTerm(term="量子コンピュータ", category=TermCategory.TECHNICAL_TERM),
            ClassifiedTerm(term="計算機", category=TermCategory.COMMON_NOUN),
        ]

        generator = GlossaryGenerator(llm_client=mock_llm_client)
        glossary = generator.generate(
            classified_terms, [sample_document], skip_common_nouns=True
        )

        # Should skip common_noun
        assert len(glossary.terms) == 1
        assert "量子コンピュータ" in glossary.terms
        assert "計算機" not in glossary.terms
        assert glossary.terms["量子コンピュータ"].name == "量子コンピュータ"
