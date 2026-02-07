"""Tests for shared term_text validator."""

import pytest

from genglossary.models.term_validator import validate_term_text


class TestValidateTermText:
    """Test validate_term_text shared validator function."""

    def test_returns_stripped_text(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        assert validate_term_text("  用語  ") == "用語"

    def test_returns_text_unchanged_when_no_whitespace(self) -> None:
        """Test that text without extra whitespace is returned as-is."""
        assert validate_term_text("量子コンピュータ") == "量子コンピュータ"

    def test_raises_error_for_empty_string(self) -> None:
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Term text cannot be empty"):
            validate_term_text("")

    def test_raises_error_for_whitespace_only(self) -> None:
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Term text cannot be empty"):
            validate_term_text("   ")
