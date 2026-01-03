"""Integration tests for the complete glossary generation pipeline."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.output.markdown_writer import MarkdownWriter
from genglossary.term_extractor import TermExtractor


# --- Mock Response Models ---


class MockTermJudgmentResponse(BaseModel):
    """Mock response for term judgment (new architecture)."""

    approved_terms: list[str]


class MockDefinitionResponse(BaseModel):
    """Mock response for definition generation."""

    definition: str
    confidence: float


class MockReviewResponse(BaseModel):
    """Mock response for glossary review."""

    issues: list[dict[str, str]]


class MockRefinementResponse(BaseModel):
    """Mock response for definition refinement."""

    refined_definition: str
    confidence: float


class TestEndToEndPipeline:
    """Integration tests for the complete glossary generation pipeline."""

    @patch("genglossary.term_extractor.MorphologicalAnalyzer")
    def test_full_pipeline_with_mock_llm(
        self,
        mock_analyzer_class: MagicMock,
        tmp_path_with_docs: Path,
    ) -> None:
        """Test the full pipeline: DocumentLoader -> TermExtractor -> GlossaryGenerator
        -> GlossaryReviewer -> GlossaryRefiner -> MarkdownWriter.
        """
        # Set up MorphologicalAnalyzer mock to return candidates
        mock_analyzer = MagicMock()
        mock_analyzer.extract_proper_nouns.return_value = [
            "マイクロサービス", "APIゲートウェイ", "PostgreSQL"
        ]
        mock_analyzer_class.return_value = mock_analyzer

        # Create mock LLM client
        mock_llm = MagicMock(spec=BaseLLMClient)

        # Set up responses in order of calls
        mock_llm.generate_structured.side_effect = [
            # 1. Term extraction (judgment)
            MockTermJudgmentResponse(
                approved_terms=["マイクロサービス", "APIゲートウェイ", "PostgreSQL"]
            ),
            # 2-4. Definition for each term
            MockDefinitionResponse(
                definition="独立して開発・デプロイ可能な小さなサービスに分割するアーキテクチャ",
                confidence=0.9,
            ),
            MockDefinitionResponse(
                definition="すべてのAPIリクエストの入り口となるコンポーネント",
                confidence=0.85,
            ),
            MockDefinitionResponse(
                definition="オープンソースのリレーショナルデータベース管理システム",
                confidence=0.95,
            ),
            # 5. Review
            MockReviewResponse(
                issues=[
                    {
                        "term": "マイクロサービス",
                        "issue_type": "unclear",
                        "description": "定義がやや曖昧",
                    }
                ]
            ),
            # 6. Refinement for マイクロサービス
            MockRefinementResponse(
                refined_definition="独立してデプロイ可能な小さなサービス群で構成されるアーキテクチャパターン",
                confidence=0.92,
            ),
        ]

        # 1. Load documents
        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path_with_docs))
        assert len(documents) == 2

        # 2. Extract terms
        extractor = TermExtractor(llm_client=mock_llm)
        terms = extractor.extract_terms(documents)
        assert len(terms) == 3
        assert "マイクロサービス" in terms

        # 3. Generate glossary
        generator = GlossaryGenerator(llm_client=mock_llm)
        glossary = generator.generate(terms, documents)
        assert isinstance(glossary, Glossary)
        assert glossary.term_count == 3

        # 4. Review glossary
        reviewer = GlossaryReviewer(llm_client=mock_llm)
        issues = reviewer.review(glossary)
        assert len(issues) == 1
        assert issues[0].term_name == "マイクロサービス"

        # 5. Refine glossary
        refiner = GlossaryRefiner(llm_client=mock_llm)
        refined_glossary = refiner.refine(glossary, issues, documents)
        assert refined_glossary.term_count == 3

        # Check refinement was applied
        refined_term = refined_glossary.get_term("マイクロサービス")
        assert refined_term is not None
        assert "アーキテクチャパターン" in refined_term.definition

        # 6. Write output
        output_path = tmp_path_with_docs / "glossary.md"
        writer = MarkdownWriter()
        writer.write(refined_glossary, str(output_path))

        # Verify output
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# 用語集" in content
        assert "マイクロサービス" in content
        assert "APIゲートウェイ" in content
        assert "PostgreSQL" in content

    def test_pipeline_with_empty_documents(
        self,
        tmp_path: Path,
    ) -> None:
        """Test pipeline behavior with empty documents."""
        # Create empty document
        empty_doc = tmp_path / "empty.md"
        empty_doc.write_text("", encoding="utf-8")

        # Create mock LLM
        mock_llm = MagicMock(spec=BaseLLMClient)

        # Load and process
        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path))

        extractor = TermExtractor(llm_client=mock_llm)
        terms = extractor.extract_terms(documents)

        # Empty documents should return empty terms
        assert terms == []
        # LLM should not be called for empty documents
        mock_llm.generate_structured.assert_not_called()

    @patch("genglossary.term_extractor.MorphologicalAnalyzer")
    def test_pipeline_with_no_issues(
        self,
        mock_analyzer_class: MagicMock,
        tmp_path_with_docs: Path,
    ) -> None:
        """Test pipeline when review finds no issues."""
        # Set up MorphologicalAnalyzer mock
        mock_analyzer = MagicMock()
        mock_analyzer.extract_proper_nouns.return_value = ["テスト用語"]
        mock_analyzer_class.return_value = mock_analyzer

        mock_llm = MagicMock(spec=BaseLLMClient)

        # Note: New architecture uses SudachiPy + LLM judgment
        mock_llm.generate_structured.side_effect = [
            # Term extraction (judgment)
            MockTermJudgmentResponse(approved_terms=["テスト用語"]),
            # Definition (no related terms call since only 1 term)
            MockDefinitionResponse(definition="テスト用の定義", confidence=0.9),
            # Review - no issues
            MockReviewResponse(issues=[]),
        ]

        # Run pipeline
        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path_with_docs))

        extractor = TermExtractor(llm_client=mock_llm)
        terms = extractor.extract_terms(documents)

        generator = GlossaryGenerator(llm_client=mock_llm)
        glossary = generator.generate(terms, documents)

        reviewer = GlossaryReviewer(llm_client=mock_llm)
        issues = reviewer.review(glossary)
        assert len(issues) == 0

        refiner = GlossaryRefiner(llm_client=mock_llm)
        refined_glossary = refiner.refine(glossary, issues, documents)

        # Glossary should remain unchanged
        assert refined_glossary.term_count == glossary.term_count
        term = refined_glossary.get_term("テスト用語")
        assert term is not None
        assert term.definition == "テスト用の定義"

    @patch("genglossary.term_extractor.MorphologicalAnalyzer")
    def test_pipeline_handles_large_document_count(
        self,
        mock_analyzer_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test pipeline with multiple documents."""
        # Create multiple documents
        for i in range(5):
            doc_path = tmp_path / f"doc{i}.md"
            doc_path.write_text(
                f"# Document {i}\n\nThis document contains 用語{i} which is important.\n",
                encoding="utf-8",
            )

        # Set up MorphologicalAnalyzer mock
        terms = [f"用語{i}" for i in range(5)]
        mock_analyzer = MagicMock()
        mock_analyzer.extract_proper_nouns.return_value = terms
        mock_analyzer_class.return_value = mock_analyzer

        mock_llm = MagicMock(spec=BaseLLMClient)

        # Set up responses
        responses = [MockTermJudgmentResponse(approved_terms=terms)]

        # Add responses for each term
        for i in range(5):
            responses.append(
                MockDefinitionResponse(definition=f"用語{i}の定義", confidence=0.8)
            )

        # Add review response
        responses.append(MockReviewResponse(issues=[]))

        mock_llm.generate_structured.side_effect = responses

        # Run pipeline
        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path))
        assert len(documents) == 5

        extractor = TermExtractor(llm_client=mock_llm)
        extracted_terms = extractor.extract_terms(documents)
        assert len(extracted_terms) == 5

        generator = GlossaryGenerator(llm_client=mock_llm)
        glossary = generator.generate(extracted_terms, documents)
        assert glossary.term_count == 5


class TestErrorHandling:
    """Test error handling in the integration pipeline."""

    def test_document_loader_handles_missing_directory(self) -> None:
        """Test that DocumentLoader raises appropriate error for missing directory."""
        loader = DocumentLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_directory("/nonexistent/path")

    def test_document_loader_handles_unsupported_extension(
        self, tmp_path: Path
    ) -> None:
        """Test that DocumentLoader raises error for unsupported file types."""
        # Create file with unsupported extension
        unsupported_file = tmp_path / "file.xyz"
        unsupported_file.write_text("content", encoding="utf-8")

        loader = DocumentLoader()

        with pytest.raises(ValueError, match="Unsupported file extension"):
            loader.load_file(str(unsupported_file))

    def test_pipeline_handles_empty_glossary(self, tmp_path: Path) -> None:
        """Test pipeline behavior when no terms are extracted."""
        # Create document with no extractable terms
        doc_path = tmp_path / "empty_terms.md"
        doc_path.write_text("Simple text without special terms.", encoding="utf-8")

        mock_llm = MagicMock(spec=BaseLLMClient)
        mock_llm.generate_structured.return_value = MockTermJudgmentResponse(approved_terms=[])

        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path))

        extractor = TermExtractor(llm_client=mock_llm)
        terms = extractor.extract_terms(documents)
        assert terms == []

        generator = GlossaryGenerator(llm_client=mock_llm)
        glossary = generator.generate(terms, documents)

        assert glossary.term_count == 0

        # Review empty glossary
        reviewer = GlossaryReviewer(llm_client=mock_llm)
        issues = reviewer.review(glossary)
        assert issues == []

    def test_markdown_writer_creates_parent_directories(
        self, tmp_path: Path, sample_glossary: Glossary
    ) -> None:
        """Test that MarkdownWriter creates parent directories as needed."""
        output_path = tmp_path / "nested" / "deep" / "glossary.md"

        writer = MarkdownWriter()
        writer.write(sample_glossary, str(output_path))

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# 用語集" in content


class TestDocumentLoaderIntegration:
    """Integration tests for DocumentLoader with the pipeline."""

    def test_loads_markdown_files(self, tmp_path: Path) -> None:
        """Test that DocumentLoader correctly loads Markdown files."""
        doc_content = "# Test Document\n\nThis is test content."
        doc_path = tmp_path / "test.md"
        doc_path.write_text(doc_content, encoding="utf-8")

        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path))

        assert len(documents) == 1
        assert documents[0].content == doc_content

    def test_loads_txt_files(self, tmp_path: Path) -> None:
        """Test that DocumentLoader correctly loads text files."""
        doc_content = "This is plain text content."
        doc_path = tmp_path / "test.txt"
        doc_path.write_text(doc_content, encoding="utf-8")

        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path))

        assert len(documents) == 1
        assert documents[0].content == doc_content

    def test_recursive_loading(self, tmp_path: Path) -> None:
        """Test that DocumentLoader recursively loads files from subdirectories."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.md").write_text("Root document", encoding="utf-8")
        (subdir / "nested.md").write_text("Nested document", encoding="utf-8")

        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path), recursive=True)

        assert len(documents) == 2

    def test_non_recursive_loading(self, tmp_path: Path) -> None:
        """Test that DocumentLoader respects recursive=False."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.md").write_text("Root document", encoding="utf-8")
        (subdir / "nested.md").write_text("Nested document", encoding="utf-8")

        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path), recursive=False)

        assert len(documents) == 1


class TestMarkdownWriterIntegration:
    """Integration tests for MarkdownWriter with the pipeline."""

    def test_output_contains_all_sections(
        self, tmp_path: Path, sample_glossary: Glossary
    ) -> None:
        """Test that generated Markdown contains all expected sections."""
        output_path = tmp_path / "glossary.md"

        writer = MarkdownWriter()
        writer.write(sample_glossary, str(output_path))

        content = output_path.read_text(encoding="utf-8")

        # Check header
        assert "# 用語集" in content
        assert "生成日時:" in content

        # Check terms
        assert "### マイクロサービス" in content
        assert "### APIゲートウェイ" in content
        assert "### PostgreSQL" in content

        # Check definitions
        assert "**定義**:" in content

        # Check occurrences
        assert "**出現箇所**:" in content


class TestPipelineWithVariousInputs:
    """Test the pipeline with various input scenarios."""

    @patch("genglossary.term_extractor.MorphologicalAnalyzer")
    def test_japanese_content_handling(
        self, mock_analyzer_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test that Japanese content is properly handled throughout the pipeline."""
        doc_content = """# 日本語ドキュメント

これはテストドキュメントです。
マイクロサービスアーキテクチャについて説明します。
APIゲートウェイは重要なコンポーネントです。
"""
        doc_path = tmp_path / "japanese.md"
        doc_path.write_text(doc_content, encoding="utf-8")

        # Set up MorphologicalAnalyzer mock
        mock_analyzer = MagicMock()
        mock_analyzer.extract_proper_nouns.return_value = [
            "マイクロサービス", "APIゲートウェイ"
        ]
        mock_analyzer_class.return_value = mock_analyzer

        mock_llm = MagicMock(spec=BaseLLMClient)
        mock_llm.generate_structured.side_effect = [
            MockTermJudgmentResponse(approved_terms=["マイクロサービス", "APIゲートウェイ"]),
            MockDefinitionResponse(definition="日本語の定義1", confidence=0.9),
            MockDefinitionResponse(definition="日本語の定義2", confidence=0.85),
            MockReviewResponse(issues=[]),
        ]

        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path))

        extractor = TermExtractor(llm_client=mock_llm)
        terms = extractor.extract_terms(documents)

        generator = GlossaryGenerator(llm_client=mock_llm)
        glossary = generator.generate(terms, documents)

        # Write and verify Japanese content
        output_path = tmp_path / "glossary.md"
        writer = MarkdownWriter()
        writer.write(glossary, str(output_path))

        content = output_path.read_text(encoding="utf-8")
        assert "日本語の定義1" in content
        assert "マイクロサービス" in content

    def test_mixed_content_types(self, tmp_path: Path) -> None:
        """Test pipeline with both .md and .txt files."""
        (tmp_path / "doc1.md").write_text("# Markdown doc\n\nWith terms.", encoding="utf-8")
        (tmp_path / "doc2.txt").write_text("Plain text doc with terms.", encoding="utf-8")

        mock_llm = MagicMock(spec=BaseLLMClient)
        mock_llm.generate_structured.return_value = MockTermJudgmentResponse(approved_terms=["term1"])

        loader = DocumentLoader()
        documents = loader.load_directory(str(tmp_path))

        assert len(documents) == 2
        assert any(d.file_path.endswith(".md") for d in documents)
        assert any(d.file_path.endswith(".txt") for d in documents)
