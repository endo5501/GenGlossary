"""Tests for synonym group API schema validation."""

import pytest
from pydantic import ValidationError

from genglossary.api.schemas.synonym_group_schemas import (
    SynonymGroupCreateRequest,
    SynonymGroupUpdateRequest,
    SynonymMemberCreateRequest,
)


class TestSynonymGroupCreateRequestValidation:
    """Test whitespace-only validation for SynonymGroupCreateRequest."""

    def test_whitespace_only_primary_term_raises(self) -> None:
        with pytest.raises(ValidationError, match="Term text cannot be empty"):
            SynonymGroupCreateRequest(
                primary_term_text="   ", member_texts=["田中"]
            )

    def test_whitespace_only_member_text_raises(self) -> None:
        with pytest.raises(ValidationError, match="Term text cannot be empty"):
            SynonymGroupCreateRequest(
                primary_term_text="田中太郎", member_texts=["  "]
            )

    def test_strips_whitespace_from_primary_term(self) -> None:
        req = SynonymGroupCreateRequest(
            primary_term_text="  田中太郎  ", member_texts=["田中太郎", "田中"]
        )
        assert req.primary_term_text == "田中太郎"

    def test_strips_whitespace_from_member_texts(self) -> None:
        req = SynonymGroupCreateRequest(
            primary_term_text="田中太郎", member_texts=["  田中太郎  ", "  田中  "]
        )
        assert req.member_texts == ["田中太郎", "田中"]


class TestSynonymGroupUpdateRequestValidation:
    """Test whitespace-only validation for SynonymGroupUpdateRequest."""

    def test_whitespace_only_primary_term_raises(self) -> None:
        with pytest.raises(ValidationError, match="Term text cannot be empty"):
            SynonymGroupUpdateRequest(primary_term_text="   ")

    def test_strips_whitespace(self) -> None:
        req = SynonymGroupUpdateRequest(primary_term_text="  田中  ")
        assert req.primary_term_text == "田中"


class TestSynonymMemberCreateRequestValidation:
    """Test whitespace-only validation for SynonymMemberCreateRequest."""

    def test_whitespace_only_term_raises(self) -> None:
        with pytest.raises(ValidationError, match="Term text cannot be empty"):
            SynonymMemberCreateRequest(term_text="   ")

    def test_strips_whitespace(self) -> None:
        req = SynonymMemberCreateRequest(term_text="  田中  ")
        assert req.term_text == "田中"
