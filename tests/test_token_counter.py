"""Tests for token counter utility."""

import pytest

from genglossary.utils.token_counter import TokenCounter


class TestTokenCounter:
    """Test TokenCounter class."""

    def test_count_characters(self) -> None:
        """Test character counting."""
        counter = TokenCounter()
        text = "This is a test prompt."
        result = counter.count(text)

        assert result["characters"] == len(text)
        assert result["characters"] == 22

    def test_count_words(self) -> None:
        """Test word counting."""
        counter = TokenCounter()
        text = "This is a test prompt."
        result = counter.count(text)

        assert result["words"] == 5

    def test_count_lines(self) -> None:
        """Test line counting."""
        counter = TokenCounter()
        text = "Line 1\nLine 2\nLine 3"
        result = counter.count(text)

        assert result["lines"] == 3

    def test_count_empty_string(self) -> None:
        """Test counting empty string."""
        counter = TokenCounter()
        result = counter.count("")

        assert result["characters"] == 0
        assert result["words"] == 0
        assert result["lines"] == 0

    def test_count_multiline_text(self) -> None:
        """Test counting multiline text with various content."""
        counter = TokenCounter()
        text = """You are a term extractor.
Extract important terms from the document.

Example:
- quantum computer
- machine learning"""

        result = counter.count(text)

        assert result["characters"] > 0
        assert result["words"] > 0
        assert result["lines"] == 6

    def test_estimate_tokens(self) -> None:
        """Test token estimation (rough approximation)."""
        counter = TokenCounter()
        # Rough estimation: ~4 characters per token for English text
        text = "This is a simple test prompt for token counting."
        result = counter.count(text)

        # Estimate tokens as characters / 4
        assert "estimated_tokens" in result
        assert result["estimated_tokens"] > 0
        assert result["estimated_tokens"] == result["characters"] // 4
