"""Tests for text utility functions."""

import pytest

from genglossary.utils.text import CJK_RANGES, contains_cjk, is_cjk_char


class TestIsCjkChar:
    """Test suite for is_cjk_char function."""

    @pytest.mark.parametrize(
        "char,expected",
        [
            # CJK Unified Ideographs
            ("漢", True),
            ("字", True),
            ("中", True),
            # Hiragana
            ("あ", True),
            ("ん", True),
            ("を", True),
            # Katakana
            ("ア", True),
            ("ン", True),
            ("ヲ", True),
            # Korean Hangul
            ("가", True),
            ("한", True),
            # ASCII characters (not CJK)
            ("a", False),
            ("Z", False),
            ("0", False),
            # Punctuation (not CJK)
            (".", False),
            ("!", False),
            # Space (not CJK)
            (" ", False),
        ],
    )
    def test_is_cjk_char(self, char: str, expected: bool) -> None:
        """Test is_cjk_char correctly identifies CJK characters."""
        assert is_cjk_char(char) == expected


class TestContainsCjk:
    """Test suite for contains_cjk function."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            # Pure CJK text
            ("日本語", True),
            ("中文", True),
            ("한국어", True),
            # Mixed text (CJK + ASCII)
            ("Hello世界", True),
            ("テスト123", True),
            # ASCII only
            ("Hello World", False),
            ("GenGlossary", False),
            ("12345", False),
            # Empty string
            ("", False),
            # Whitespace only
            ("   ", False),
            # Punctuation only
            ("...", False),
        ],
    )
    def test_contains_cjk(self, text: str, expected: bool) -> None:
        """Test contains_cjk correctly detects CJK text."""
        assert contains_cjk(text) == expected


class TestCjkRanges:
    """Test suite for CJK_RANGES constant."""

    def test_cjk_ranges_has_expected_categories(self) -> None:
        """Test CJK_RANGES contains expected Unicode ranges."""
        assert len(CJK_RANGES) == 4  # CJK Unified, Hiragana, Katakana, Hangul

    def test_cjk_ranges_are_tuples(self) -> None:
        """Test CJK_RANGES elements are tuples of start/end characters."""
        for range_tuple in CJK_RANGES:
            assert isinstance(range_tuple, tuple)
            assert len(range_tuple) == 2
            start, end = range_tuple
            assert isinstance(start, str)
            assert isinstance(end, str)
            assert len(start) == 1
            assert len(end) == 1
            assert start <= end
