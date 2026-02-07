"""Tests for synonym group models."""

from genglossary.models.synonym import SynonymGroup, SynonymMember


class TestSynonymMember:
    """Test SynonymMember model."""

    def test_create_synonym_member(self) -> None:
        """Test creating a SynonymMember with valid data."""
        member = SynonymMember(id=1, group_id=1, term_text="田中")

        assert member.id == 1
        assert member.group_id == 1
        assert member.term_text == "田中"

    def test_synonym_member_strips_whitespace(self) -> None:
        """Test that term_text is stripped of whitespace."""
        member = SynonymMember(id=1, group_id=1, term_text="  田中  ")

        assert member.term_text == "田中"


class TestSynonymGroup:
    """Test SynonymGroup model."""

    def test_create_synonym_group_with_members(self) -> None:
        """Test creating a SynonymGroup with members."""
        members = [
            SynonymMember(id=1, group_id=1, term_text="田中太郎"),
            SynonymMember(id=2, group_id=1, term_text="田中"),
            SynonymMember(id=3, group_id=1, term_text="田中部長"),
        ]
        group = SynonymGroup(id=1, primary_term_text="田中太郎", members=members)

        assert group.id == 1
        assert group.primary_term_text == "田中太郎"
        assert len(group.members) == 3

    def test_create_synonym_group_with_empty_members(self) -> None:
        """Test creating a SynonymGroup with no members."""
        group = SynonymGroup(id=1, primary_term_text="田中太郎", members=[])

        assert group.members == []

    def test_synonym_group_strips_primary_term_whitespace(self) -> None:
        """Test that primary_term_text is stripped of whitespace."""
        group = SynonymGroup(id=1, primary_term_text="  田中太郎  ", members=[])

        assert group.primary_term_text == "田中太郎"
