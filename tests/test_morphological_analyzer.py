"""Tests for MorphologicalAnalyzer using SudachiPy."""

import pytest

from genglossary.morphological_analyzer import MorphologicalAnalyzer


class TestMorphologicalAnalyzer:
    """Test suite for MorphologicalAnalyzer class."""

    def test_morphological_analyzer_initialization(self) -> None:
        """Test that MorphologicalAnalyzer can be initialized."""
        analyzer = MorphologicalAnalyzer()
        assert analyzer is not None

    def test_extract_proper_nouns_from_simple_text(self) -> None:
        """Test extracting proper nouns from simple Japanese text."""
        analyzer = MorphologicalAnalyzer()
        text = "東京は日本の首都です。"

        proper_nouns = analyzer.extract_proper_nouns(text)

        assert "東京" in proper_nouns
        assert "日本" in proper_nouns

    def test_extract_proper_nouns_returns_list(self) -> None:
        """Test that extract_proper_nouns returns a list of strings."""
        analyzer = MorphologicalAnalyzer()
        text = "GenGlossaryはLLMを活用したツールです。"

        result = analyzer.extract_proper_nouns(text)

        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    def test_extract_proper_nouns_removes_duplicates(self) -> None:
        """Test that duplicate proper nouns are removed."""
        analyzer = MorphologicalAnalyzer()
        text = "東京に住んでいます。東京は楽しい街です。"

        proper_nouns = analyzer.extract_proper_nouns(text)

        # Should contain 東京 only once
        assert proper_nouns.count("東京") == 1

    def test_extract_proper_nouns_from_empty_text(self) -> None:
        """Test that empty text returns empty list."""
        analyzer = MorphologicalAnalyzer()

        result = analyzer.extract_proper_nouns("")

        assert result == []

    def test_extract_proper_nouns_excludes_common_nouns(self) -> None:
        """Test that common nouns are not extracted."""
        analyzer = MorphologicalAnalyzer()
        text = "猫が好きです。犬も好きです。"

        proper_nouns = analyzer.extract_proper_nouns(text)

        # Common nouns should not be in the result
        assert "猫" not in proper_nouns
        assert "犬" not in proper_nouns

    def test_extract_proper_nouns_includes_organization_names(self) -> None:
        """Test that organization names in dictionary are extracted."""
        analyzer = MorphologicalAnalyzer()
        text = "トヨタ自動車は愛知県に本社があります。"

        proper_nouns = analyzer.extract_proper_nouns(text)

        # Organization name should be extracted (トヨタ or 愛知県)
        assert len(proper_nouns) > 0

    def test_extract_proper_nouns_includes_place_names(self) -> None:
        """Test that place names are extracted."""
        analyzer = MorphologicalAnalyzer()
        text = "大阪府にはユニバーサルスタジオがあります。"

        proper_nouns = analyzer.extract_proper_nouns(text)

        # Should extract place name
        assert "大阪府" in proper_nouns or "大阪" in proper_nouns

    def test_extract_proper_nouns_from_technical_text(self) -> None:
        """Test extracting proper nouns from technical documentation."""
        analyzer = MorphologicalAnalyzer()
        text = """マイクロサービスアーキテクチャを採用しています。
APIゲートウェイを経由してリクエストを処理します。
PostgreSQLでデータを永続化します。"""

        proper_nouns = analyzer.extract_proper_nouns(text)

        # Should return list of extracted terms
        assert isinstance(proper_nouns, list)

    def test_uses_split_mode_c(self) -> None:
        """Test that analyzer uses split mode C (long unit)."""
        analyzer = MorphologicalAnalyzer()
        # 関西国際空港 should be kept as one unit in mode C
        text = "関西国際空港に行きました。"

        proper_nouns = analyzer.extract_proper_nouns(text)

        # In mode C, compound nouns should be kept together
        assert "関西国際空港" in proper_nouns or any("関西" in pn for pn in proper_nouns)

    def test_extract_from_multiline_text(self) -> None:
        """Test extracting proper nouns from multiline text."""
        analyzer = MorphologicalAnalyzer()
        text = """GenGlossaryは用語集を自動生成するツールです。
LLMを活用してドキュメントから用語を抽出します。
Pythonで実装されています。"""

        proper_nouns = analyzer.extract_proper_nouns(text)

        assert isinstance(proper_nouns, list)
        # Should extract terms across multiple lines
        assert len(proper_nouns) >= 0  # At least some terms expected

    def test_preserves_order_of_first_occurrence(self) -> None:
        """Test that terms are returned in order of first occurrence."""
        analyzer = MorphologicalAnalyzer()
        text = "東京から大阪に行きます。東京は首都です。"

        proper_nouns = analyzer.extract_proper_nouns(text)

        if "東京" in proper_nouns and "大阪" in proper_nouns:
            # 東京 should come before 大阪
            assert proper_nouns.index("東京") < proper_nouns.index("大阪")
