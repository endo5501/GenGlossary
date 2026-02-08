"""Tests for SynonymGroupCreateRequest schema validation."""

import pytest
from pydantic import ValidationError

from genglossary.api.schemas.synonym_group_schemas import SynonymGroupCreateRequest


class TestSynonymGroupCreateRequestPrimaryInMembers:
    """Test that primary_term_text must be included in member_texts."""

    def test_valid_when_primary_in_members(self) -> None:
        request = SynonymGroupCreateRequest(
            primary_term_text="田中太郎",
            member_texts=["田中太郎", "田中"],
        )
        assert request.primary_term_text == "田中太郎"

    def test_raises_when_primary_not_in_members(self) -> None:
        with pytest.raises(ValidationError, match="primary_term_text must be included in member_texts"):
            SynonymGroupCreateRequest(
                primary_term_text="田中太郎",
                member_texts=["田中", "田中部長"],
            )
