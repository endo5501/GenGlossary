"""Tests for synonym support in pipeline components."""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.synonym import SynonymGroup, SynonymMember
from genglossary.models.term import Term, TermOccurrence
from genglossary.output.markdown_writer import MarkdownWriter


class MockDefinitionResponse(BaseModel):
    definition: str
    confidence: float


class MockReviewResponse(BaseModel):
    issues: list[dict]


class MockRefinementResponse(BaseModel):
    refined_definition: str
    confidence: float


@pytest.fixture
def mock_llm() -> MagicMock:
    return MagicMock(spec=BaseLLMClient)


@pytest.fixture
def sample_doc() -> Document:
    content = """田中太郎は営業部のリーダーです。
田中は今日も朝早くから出社しました。
田中部長が会議を主導しています。
サーバーの障害が発生しました。
サーバは再起動が必要です。
"""
    return Document(file_path="test.md", content=content)


@pytest.fixture
def synonym_groups() -> list[SynonymGroup]:
    return [
        SynonymGroup(
            id=1,
            primary_term_text="田中太郎",
            members=[
                SynonymMember(id=1, group_id=1, term_text="田中太郎"),
                SynonymMember(id=2, group_id=1, term_text="田中"),
                SynonymMember(id=3, group_id=1, term_text="田中部長"),
            ],
        ),
        SynonymGroup(
            id=2,
            primary_term_text="サーバー",
            members=[
                SynonymMember(id=4, group_id=2, term_text="サーバー"),
                SynonymMember(id=5, group_id=2, term_text="サーバ"),
            ],
        ),
    ]


class TestGeneratorSynonymOccurrences:
    """Test that GlossaryGenerator finds occurrences for synonyms."""

    def test_find_occurrences_with_synonyms(
        self, mock_llm: MagicMock, sample_doc: Document, synonym_groups: list[SynonymGroup]
    ) -> None:
        """Searching for primary term should also find synonym occurrences."""
        generator = GlossaryGenerator(llm_client=mock_llm)

        # Search for "田中太郎" with synonyms ["田中", "田中部長"]
        occurrences = generator._find_term_occurrences(
            "田中太郎", [sample_doc], synonyms=["田中", "田中部長"]
        )

        # Should find occurrences from all three variants
        contexts = [occ.context for occ in occurrences]
        all_text = "\n".join(contexts)
        assert "田中太郎" in all_text
        assert "田中部長" in all_text
        # "田中" appears in all lines containing any of the three
        assert len(occurrences) >= 3

    def test_find_occurrences_without_synonyms(
        self, mock_llm: MagicMock, sample_doc: Document
    ) -> None:
        """Without synonyms, only the exact term is searched."""
        generator = GlossaryGenerator(llm_client=mock_llm)

        occurrences = generator._find_term_occurrences("田中太郎", [sample_doc])

        # Only lines with "田中太郎" exactly
        assert len(occurrences) == 1


class TestGeneratorSynonymPrompt:
    """Test that synonym info is included in definition prompt."""

    def test_prompt_includes_synonym_info(
        self, mock_llm: MagicMock
    ) -> None:
        """Definition prompt should mention synonyms."""
        generator = GlossaryGenerator(llm_client=mock_llm)

        prompt = generator._build_definition_prompt(
            "田中太郎", "(context)", synonyms=["田中", "田中部長"]
        )

        assert "田中" in prompt
        assert "田中部長" in prompt
        assert "同義語" in prompt

    def test_prompt_without_synonyms_has_no_synonym_section(
        self, mock_llm: MagicMock
    ) -> None:
        """Without synonyms, no synonym section in prompt."""
        generator = GlossaryGenerator(llm_client=mock_llm)

        prompt = generator._build_definition_prompt("田中太郎", "(context)")

        assert "同義語" not in prompt


class TestGeneratorSynonymGenerate:
    """Test that generate() uses synonym groups correctly."""

    def test_generate_skips_non_primary_terms(
        self, mock_llm: MagicMock, sample_doc: Document, synonym_groups: list[SynonymGroup]
    ) -> None:
        """Non-primary synonym members should be skipped in generation."""
        mock_llm.generate_structured.return_value = MockDefinitionResponse(
            definition="営業部のリーダー", confidence=0.9
        )

        generator = GlossaryGenerator(llm_client=mock_llm)

        # Terms list includes both primary and non-primary members
        terms = ["田中太郎", "田中", "田中部長", "サーバー", "サーバ"]

        glossary = generator.generate(
            terms, [sample_doc], synonym_groups=synonym_groups
        )

        # Only primary terms should be in the glossary
        assert "田中太郎" in glossary.terms
        assert "田中" not in glossary.terms
        assert "田中部長" not in glossary.terms
        assert "サーバー" in glossary.terms
        assert "サーバ" not in glossary.terms


class TestReviewerSynonymInfo:
    """Test that GlossaryReviewer includes synonym info in review prompt."""

    def test_review_prompt_includes_synonyms(
        self, mock_llm: MagicMock, synonym_groups: list[SynonymGroup]
    ) -> None:
        """Review prompt should include synonym information."""
        reviewer = GlossaryReviewer(llm_client=mock_llm)

        glossary = Glossary()
        glossary.add_term(Term(
            name="田中太郎", definition="営業部のリーダー",
            occurrences=[], confidence=0.9,
        ))

        prompt = reviewer._create_review_prompt(
            glossary, synonym_groups=synonym_groups
        )

        assert "同義語" in prompt
        assert "田中" in prompt
        assert "田中部長" in prompt


class TestRefinerSynonymInfo:
    """Test that GlossaryRefiner includes synonym info in refinement prompt."""

    def test_refinement_prompt_includes_synonyms(
        self, mock_llm: MagicMock, synonym_groups: list[SynonymGroup]
    ) -> None:
        """Refinement prompt should include synonym information."""
        refiner = GlossaryRefiner(llm_client=mock_llm)

        term = Term(
            name="田中太郎", definition="営業部のリーダー",
            occurrences=[], confidence=0.9,
        )
        issue = GlossaryIssue(
            term_name="田中太郎", issue_type="unclear",
            description="定義が曖昧",
        )

        prompt = refiner._create_refinement_prompt(
            term, issue, {}, synonym_groups=synonym_groups
        )

        assert "同義語" in prompt
        assert "田中" in prompt
        assert "田中部長" in prompt


class TestMarkdownWriterSynonyms:
    """Test that MarkdownWriter includes synonym aliases."""

    def test_format_term_includes_aliases(
        self, synonym_groups: list[SynonymGroup]
    ) -> None:
        """Term output should include '別名' section."""
        writer = MarkdownWriter()

        term = Term(
            name="田中太郎", definition="営業部のリーダー",
            occurrences=[], confidence=0.9,
        )

        output = writer._format_term(term, synonym_groups=synonym_groups)

        assert "**別名**" in output
        assert "田中" in output
        assert "田中部長" in output

    def test_format_term_without_synonyms(self) -> None:
        """Term without synonyms should not have '別名' section."""
        writer = MarkdownWriter()

        term = Term(
            name="独立用語", definition="何か",
            occurrences=[], confidence=0.9,
        )

        output = writer._format_term(term)

        assert "別名" not in output
