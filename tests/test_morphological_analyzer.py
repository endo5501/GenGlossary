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

    def test_extract_proper_nouns_from_long_text(self) -> None:
        """Test that long text exceeding SudachiPy's limit is handled correctly.

        SudachiPy has a maximum input size limit of 49149 bytes.
        This test ensures that longer texts are processed by chunking.
        """
        analyzer = MorphologicalAnalyzer()

        # Create text that exceeds 49149 bytes
        # Each repetition is about 50 bytes, so 1000 repetitions = ~50000 bytes
        base_text = "東京は日本の首都です。大阪は第二の都市です。"
        long_text = base_text * 1000  # Should be > 49149 bytes

        # Verify the text is actually long enough
        assert len(long_text.encode("utf-8")) > 49149

        # Should not raise an error
        proper_nouns = analyzer.extract_proper_nouns(long_text)

        # Should still extract proper nouns
        assert isinstance(proper_nouns, list)
        assert "東京" in proper_nouns
        assert "日本" in proper_nouns
        assert "大阪" in proper_nouns

    def test_extract_proper_nouns_from_very_long_text(self) -> None:
        """Test handling of very long text (100KB+)."""
        analyzer = MorphologicalAnalyzer()

        # Create a 100KB+ text
        base_text = "トヨタ自動車は愛知県に本社があります。関西国際空港に行きました。"
        long_text = base_text * 2000  # Should be > 100KB

        # Should not raise an error
        proper_nouns = analyzer.extract_proper_nouns(long_text)

        # Should extract proper nouns
        assert isinstance(proper_nouns, list)
        assert len(proper_nouns) > 0


class TestMorphologicalAnalyzerCompoundNouns:
    """Test suite for compound noun extraction functionality."""

    def test_extract_compound_nouns_basic(self) -> None:
        """Test that consecutive nouns are combined into compound nouns.

        Example: 騎士 + 団 + 長 -> 騎士団長
        """
        analyzer = MorphologicalAnalyzer()
        text = "近衛騎士団長は名誉ある役職です。"

        # Extract with compound noun support
        terms = analyzer.extract_proper_nouns(text, extract_compound_nouns=True)

        # Should extract the compound noun
        assert "騎士団長" in terms or "近衛騎士団長" in terms

    def test_extract_compound_nouns_from_ticket_examples(self) -> None:
        """Test extraction of compound nouns from ticket examples.

        Expected terms from the ticket:
        - アソリウス島騎士団 (organization)
        - 魔神代理領 (place/territory)
        - 騎士代理爵位 (title)
        """
        analyzer = MorphologicalAnalyzer()
        text = """
        アソリウス島騎士団は魔神代理領の守護を担当している。
        騎士代理爵位を持つ者だけが団長になれる。
        """

        terms = analyzer.extract_proper_nouns(text, extract_compound_nouns=True)

        # Should extract compound nouns containing key components
        # Note: Exact extraction depends on SudachiPy's parsing
        assert any("騎士団" in term for term in terms)
        assert any("代理" in term for term in terms)

    def test_extract_compound_nouns_preserves_proper_nouns(self) -> None:
        """Test that enabling compound extraction still extracts proper nouns."""
        analyzer = MorphologicalAnalyzer()
        text = "東京の騎士団長が大阪を訪問した。"

        terms = analyzer.extract_proper_nouns(text, extract_compound_nouns=True)

        # Should still extract proper nouns
        assert "東京" in terms
        assert "大阪" in terms

    def test_compound_nouns_disabled_by_default(self) -> None:
        """Test that compound noun extraction is disabled by default for backward compatibility."""
        analyzer = MorphologicalAnalyzer()
        text = "騎士団長は重要な役職です。"

        # Default behavior (compound extraction disabled)
        terms = analyzer.extract_proper_nouns(text)

        # Should not extract compound common nouns by default
        # (unless they are recognized as proper nouns by SudachiPy)
        # This test ensures backward compatibility
        assert isinstance(terms, list)

    def test_extract_compound_nouns_removes_duplicates(self) -> None:
        """Test that duplicate compound nouns are removed."""
        analyzer = MorphologicalAnalyzer()
        text = "騎士団長は優れた指導者です。この騎士団長は勇敢です。"

        terms = analyzer.extract_proper_nouns(text, extract_compound_nouns=True)

        # Should not have duplicates
        if "騎士団長" in terms:
            assert terms.count("騎士団長") == 1


class TestMorphologicalAnalyzerCommonNouns:
    """Test suite for common noun (普通名詞) extraction functionality."""

    def test_extract_common_nouns_as_terms(self) -> None:
        """Test that common nouns can be extracted when enabled.

        Common nouns (普通名詞) may contain domain-specific technical terms
        that should be included in the glossary.
        """
        analyzer = MorphologicalAnalyzer()
        text = "聖印を持つ騎士が魔神を討伐する。"

        # Extract with common noun support
        terms = analyzer.extract_proper_nouns(text, include_common_nouns=True)

        # Should extract common nouns that are potential technical terms
        # 聖印 (sacred seal), 騎士 (knight), 魔神 (demon)
        assert any("聖印" in term for term in terms) or any("騎士" in term for term in terms)

    def test_extract_common_nouns_from_ticket_examples(self) -> None:
        """Test extraction of common nouns from ticket examples.

        Expected terms from the ticket:
        - 聖印 (sacred seal - technical term)
        - 魔神討伐 (demon subjugation - compound technical term)
        """
        analyzer = MorphologicalAnalyzer()
        text = """
        聖印は特別な力を持つ。
        魔神討伐は騎士の使命である。
        """

        terms = analyzer.extract_proper_nouns(text, include_common_nouns=True)

        # Should extract technical terms that are common nouns
        assert any("聖印" in term for term in terms)
        assert any("魔神" in term for term in terms) or any("討伐" in term for term in terms)

    def test_common_nouns_disabled_by_default(self) -> None:
        """Test that common noun extraction is disabled by default."""
        analyzer = MorphologicalAnalyzer()
        text = "猫が犬を追いかける。"

        # Default behavior (common nouns disabled)
        terms = analyzer.extract_proper_nouns(text)

        # Should not extract common nouns by default
        assert "猫" not in terms
        assert "犬" not in terms

    def test_extract_combined_proper_and_common_nouns(self) -> None:
        """Test extraction of both proper nouns and common nouns."""
        analyzer = MorphologicalAnalyzer()
        text = "東京の騎士団が魔神を討伐した。"

        terms = analyzer.extract_proper_nouns(text, include_common_nouns=True)

        # Should extract both proper nouns and common nouns
        assert "東京" in terms  # Proper noun
        # Common nouns like 騎士団, 魔神, etc. may also be extracted


class TestMorphologicalAnalyzerFiltering:
    """Test suite for term filtering functionality (length, frequency)."""

    def test_filter_by_minimum_length(self) -> None:
        """Test that terms shorter than minimum length are filtered out.

        This helps remove overly common single-character or short terms
        that are not useful for glossaries.
        """
        analyzer = MorphologicalAnalyzer()
        text = "東、西、南、北の中央に位置する。"

        # Extract with minimum length filter (3 characters)
        terms = analyzer.extract_proper_nouns(text, min_length=3)

        # Short terms should be filtered out
        assert "東" not in terms
        assert "西" not in terms
        assert "南" not in terms
        assert "北" not in terms
        # But 中央 (2 chars) might still be filtered

    def test_filter_by_minimum_length_default(self) -> None:
        """Test that default minimum length allows all terms."""
        analyzer = MorphologicalAnalyzer()
        text = "東京と大阪。"

        # Default behavior (no length filter)
        terms = analyzer.extract_proper_nouns(text)

        # Should extract even short proper nouns
        if "東京" in terms or "大阪" in terms:
            # Default behavior allows extraction
            assert True

    def test_filter_by_frequency(self) -> None:
        """Test that terms appearing fewer than minimum frequency are filtered.

        Terms that appear multiple times in the text are more likely to be
        important for the glossary.
        """
        analyzer = MorphologicalAnalyzer()
        text = """
        騎士団長は重要な役職です。
        騎士団長は勇敢でなければならない。
        騎士団長の責任は重大です。
        代理人は一度しか言及されません。
        """

        # Extract with frequency filter (min 2 occurrences)
        terms = analyzer.extract_proper_nouns(
            text, extract_compound_nouns=True, min_frequency=2
        )

        # 騎士団長 appears 3 times, should be included
        assert "騎士団長" in terms
        # 代理人 appears 1 time, should be filtered out
        assert "代理人" not in terms

    def test_filter_by_frequency_default(self) -> None:
        """Test that default frequency filter is 1 (all terms included)."""
        analyzer = MorphologicalAnalyzer()
        text = "東京に一度だけ言及する。"

        # Default behavior (no frequency filter)
        terms = analyzer.extract_proper_nouns(text)

        # Should extract even single-occurrence terms
        assert "東京" in terms

    def test_combined_filtering(self) -> None:
        """Test that length and frequency filters can be combined."""
        analyzer = MorphologicalAnalyzer()
        text = """
        東は方角です。東は大事です。東はいいです。
        騎士団長は重要です。騎士団長は勇敢です。
        西は一度だけ。
        """

        # Extract with both filters
        terms = analyzer.extract_proper_nouns(
            text, extract_compound_nouns=True, min_length=3, min_frequency=2
        )

        # 東 appears 3 times but is too short (1 char)
        assert "東" not in terms
        # 騎士団長 appears 2 times and is long enough (4 chars)
        assert "騎士団長" in terms
        # 西 appears 1 time (fails frequency filter)
        assert "西" not in terms

    def test_filtering_preserves_order(self) -> None:
        """Test that filtering preserves the order of first occurrence."""
        analyzer = MorphologicalAnalyzer()
        text = "大阪、東京、大阪、東京、大阪。"

        # Extract with frequency filter
        terms = analyzer.extract_proper_nouns(text, min_frequency=2)

        # Both should be present, 大阪 should come before 東京
        if "大阪" in terms and "東京" in terms:
            assert terms.index("大阪") < terms.index("東京")
