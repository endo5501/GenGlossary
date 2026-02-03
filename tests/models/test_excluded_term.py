"""Tests for ExcludedTerm model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from genglossary.models.excluded_term import ExcludedTerm


class TestExcludedTerm:
    """Test ExcludedTerm model."""

    def test_create_with_auto_source(self) -> None:
        """Test creating ExcludedTerm with auto source."""
        term = ExcludedTerm(
            id=1,
            term_text="量子コンピュータ",
            source="auto",
            created_at=datetime(2026, 2, 3, 12, 0, 0),
        )

        assert term.id == 1
        assert term.term_text == "量子コンピュータ"
        assert term.source == "auto"
        assert term.created_at == datetime(2026, 2, 3, 12, 0, 0)

    def test_create_with_manual_source(self) -> None:
        """Test creating ExcludedTerm with manual source."""
        term = ExcludedTerm(
            id=2,
            term_text="一般名詞",
            source="manual",
            created_at=datetime(2026, 2, 3, 12, 0, 0),
        )

        assert term.source == "manual"

    def test_invalid_source_raises_error(self) -> None:
        """Test that invalid source value raises ValidationError."""
        with pytest.raises(ValidationError):
            ExcludedTerm(
                id=1,
                term_text="用語",
                source="invalid",  # type: ignore[arg-type]
                created_at=datetime(2026, 2, 3, 12, 0, 0),
            )

    def test_empty_term_text_raises_error(self) -> None:
        """Test that empty term_text raises ValidationError."""
        with pytest.raises(ValidationError):
            ExcludedTerm(
                id=1,
                term_text="",
                source="auto",
                created_at=datetime(2026, 2, 3, 12, 0, 0),
            )

    def test_whitespace_only_term_text_raises_error(self) -> None:
        """Test that whitespace-only term_text raises ValidationError."""
        with pytest.raises(ValidationError):
            ExcludedTerm(
                id=1,
                term_text="   ",
                source="auto",
                created_at=datetime(2026, 2, 3, 12, 0, 0),
            )

    def test_term_text_is_stripped(self) -> None:
        """Test that term_text is stripped of leading/trailing whitespace."""
        term = ExcludedTerm(
            id=1,
            term_text="  用語  ",
            source="auto",
            created_at=datetime(2026, 2, 3, 12, 0, 0),
        )

        assert term.term_text == "用語"
