"""Tests for MarkdownWriter."""

from datetime import datetime
from pathlib import Path

import pytest

from genglossary.models.glossary import Glossary
from genglossary.models.term import Term, TermOccurrence
from genglossary.output.markdown_writer import MarkdownWriter


class TestMarkdownWriter:
    """Tests for MarkdownWriter class."""

    def test_markdown_writer_initialization(self):
        """Test that MarkdownWriter can be initialized."""
        writer = MarkdownWriter()
        assert writer is not None

    def test_write_empty_glossary(self, tmp_path: Path):
        """Test writing an empty glossary."""
        writer = MarkdownWriter()
        glossary = Glossary()
        output_file = tmp_path / "glossary.md"

        writer.write(glossary, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "# 用語集" in content
        assert "用語一覧" in content

    def test_write_glossary_with_single_term(self, tmp_path: Path):
        """Test writing a glossary with a single term."""
        writer = MarkdownWriter()
        glossary = Glossary()

        term = Term(
            name="アーキテクチャ",
            definition="システム全体の構造設計を指し、コンポーネント間の関係性と責務の分割を定める概念",
            confidence=0.9,
        )
        term.add_occurrence(
            TermOccurrence(
                document_path="design.md",
                line_number=15,
                context="マイクロサービスアーキテクチャを採用する",
            )
        )
        glossary.add_term(term)

        output_file = tmp_path / "glossary.md"
        writer.write(glossary, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "### アーキテクチャ" in content
        assert "**定義**: システム全体の構造設計" in content
        assert "design.md:15" in content

    def test_format_term_heading(self):
        """Test formatting term heading."""
        writer = MarkdownWriter()
        term = Term(name="コンポーネント", definition="再利用可能な部品")

        result = writer._format_term(term)

        assert "### コンポーネント" in result

    def test_format_term_definition(self):
        """Test formatting term definition."""
        writer = MarkdownWriter()
        term = Term(
            name="設計パターン",
            definition="ソフトウェア設計における典型的な問題の解決策",
        )

        result = writer._format_term(term)

        assert "**定義**: ソフトウェア設計における" in result

    def test_format_occurrences_single(self):
        """Test formatting a single occurrence."""
        writer = MarkdownWriter()
        term = Term(name="テスト用語")
        term.add_occurrence(
            TermOccurrence(
                document_path="docs/test.md",
                line_number=42,
                context="これはテスト用語の説明です",
            )
        )

        result = writer._format_occurrences(term.occurrences)

        assert "**出現箇所**:" in result
        assert "- `docs/test.md:42` - \"これはテスト用語の説明です\"" in result

    def test_format_occurrences_multiple(self):
        """Test formatting multiple occurrences."""
        writer = MarkdownWriter()
        term = Term(name="API")
        term.add_occurrence(
            TermOccurrence(
                document_path="api.md", line_number=10, context="REST APIを使用"
            )
        )
        term.add_occurrence(
            TermOccurrence(
                document_path="implementation.md",
                line_number=25,
                context="APIエンドポイントを実装",
            )
        )

        result = writer._format_occurrences(term.occurrences)

        assert "- `api.md:10`" in result
        assert "- `implementation.md:25`" in result

    def test_format_occurrences_empty(self):
        """Test formatting with no occurrences."""
        writer = MarkdownWriter()

        result = writer._format_occurrences([])

        assert result == ""

    def test_format_related_terms_single(self):
        """Test formatting a single related term."""
        writer = MarkdownWriter()
        term = Term(name="アーキテクチャ")
        term.add_related_term("コンポーネント")

        result = writer._format_related_terms(term.related_terms)

        assert "**関連用語**: [コンポーネント](#コンポーネント)" in result

    def test_format_related_terms_multiple(self):
        """Test formatting multiple related terms."""
        writer = MarkdownWriter()
        term = Term(name="設計")
        term.add_related_term("アーキテクチャ")
        term.add_related_term("パターン")
        term.add_related_term("コンポーネント")

        result = writer._format_related_terms(term.related_terms)

        assert "**関連用語**:" in result
        assert "[アーキテクチャ](#アーキテクチャ)" in result
        assert "[パターン](#パターン)" in result
        assert "[コンポーネント](#コンポーネント)" in result

    def test_format_related_terms_empty(self):
        """Test formatting with no related terms."""
        writer = MarkdownWriter()

        result = writer._format_related_terms([])

        assert result == ""

    def test_write_complete_glossary(self, tmp_path: Path):
        """Test writing a complete glossary with multiple terms."""
        writer = MarkdownWriter()
        glossary = Glossary()
        glossary.metadata = {
            "model": "llama3.2",
            "document_count": 5,
            "generated_at": datetime(2025, 12, 31, 21, 30, 0).isoformat(),
        }

        # First term
        term1 = Term(
            name="アーキテクチャ",
            definition="システム全体の構造設計を指し、コンポーネント間の関係性と責務の分割を定める概念",
        )
        term1.add_occurrence(
            TermOccurrence(
                document_path="design.md",
                line_number=15,
                context="マイクロサービスアーキテクチャを採用する",
            )
        )
        term1.add_related_term("コンポーネント")
        term1.add_related_term("設計パターン")
        glossary.add_term(term1)

        # Second term
        term2 = Term(name="コンポーネント", definition="再利用可能なソフトウェアの部品")
        term2.add_occurrence(
            TermOccurrence(
                document_path="components.md",
                line_number=5,
                context="UIコンポーネントを作成する",
            )
        )
        glossary.add_term(term2)

        output_file = tmp_path / "complete_glossary.md"
        writer.write(glossary, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()

        # Check header
        assert "# 用語集" in content
        assert "モデル: llama3.2" in content
        assert "ドキュメント数: 5" in content

        # Check terms
        assert "### アーキテクチャ" in content
        assert "### コンポーネント" in content
        assert "[コンポーネント](#コンポーネント)" in content

        # Check separator
        assert "---" in content

    def test_write_creates_directory_if_not_exists(self, tmp_path: Path):
        """Test that write creates parent directories if they don't exist."""
        writer = MarkdownWriter()
        glossary = Glossary()
        output_file = tmp_path / "nested" / "dir" / "glossary.md"

        writer.write(glossary, str(output_file))

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_write_overwrites_existing_file(self, tmp_path: Path):
        """Test that write overwrites existing files."""
        writer = MarkdownWriter()
        glossary1 = Glossary()
        glossary1.add_term(Term(name="旧用語", definition="古い定義"))

        glossary2 = Glossary()
        glossary2.add_term(Term(name="新用語", definition="新しい定義"))

        output_file = tmp_path / "glossary.md"

        # First write
        writer.write(glossary1, str(output_file))
        content1 = output_file.read_text()
        assert "旧用語" in content1

        # Second write
        writer.write(glossary2, str(output_file))
        content2 = output_file.read_text()
        assert "新用語" in content2
        assert "旧用語" not in content2
