"""Tests for synonym_utils module."""

from genglossary.models.synonym import SynonymGroup, SynonymMember
from genglossary.synonym_utils import (
    build_non_primary_set,
    build_synonym_lookup,
    get_synonyms_for_primary,
)


def _make_group(
    group_id: int, primary: str, members: list[str]
) -> SynonymGroup:
    """Helper to create a SynonymGroup for testing."""
    return SynonymGroup(
        id=group_id,
        primary_term_text=primary,
        members=[
            SynonymMember(id=i + 1, group_id=group_id, term_text=t)
            for i, t in enumerate(members)
        ],
    )


class TestBuildSynonymLookup:
    """Test build_synonym_lookup function."""

    def test_returns_empty_dict_for_none(self) -> None:
        assert build_synonym_lookup(None) == {}

    def test_returns_empty_dict_for_empty_list(self) -> None:
        assert build_synonym_lookup([]) == {}

    def test_maps_primary_to_others(self) -> None:
        groups = [_make_group(1, "田中太郎", ["田中太郎", "田中", "田中部長"])]

        result = build_synonym_lookup(groups)

        assert result == {"田中太郎": ["田中", "田中部長"]}

    def test_skips_groups_with_only_primary(self) -> None:
        groups = [_make_group(1, "田中太郎", ["田中太郎"])]

        result = build_synonym_lookup(groups)

        assert result == {}

    def test_handles_multiple_groups(self) -> None:
        groups = [
            _make_group(1, "田中太郎", ["田中太郎", "田中"]),
            _make_group(2, "サーバー", ["サーバー", "サーバ"]),
        ]

        result = build_synonym_lookup(groups)

        assert result == {
            "田中太郎": ["田中"],
            "サーバー": ["サーバ"],
        }


class TestBuildNonPrimarySet:
    """Test build_non_primary_set function."""

    def test_returns_empty_set_for_none(self) -> None:
        assert build_non_primary_set(None) == set()

    def test_returns_empty_set_for_empty_list(self) -> None:
        assert build_non_primary_set([]) == set()

    def test_returns_non_primary_members(self) -> None:
        groups = [_make_group(1, "田中太郎", ["田中太郎", "田中", "田中部長"])]

        result = build_non_primary_set(groups)

        assert result == {"田中", "田中部長"}

    def test_excludes_primary_terms(self) -> None:
        groups = [_make_group(1, "田中太郎", ["田中太郎", "田中"])]

        result = build_non_primary_set(groups)

        assert "田中太郎" not in result


class TestGetSynonymsForPrimary:
    """Test get_synonyms_for_primary function."""

    def test_returns_empty_list_for_none(self) -> None:
        assert get_synonyms_for_primary(None, "田中太郎") == []

    def test_returns_empty_list_for_unknown_term(self) -> None:
        groups = [_make_group(1, "田中太郎", ["田中太郎", "田中"])]

        assert get_synonyms_for_primary(groups, "鈴木") == []

    def test_returns_other_members(self) -> None:
        groups = [_make_group(1, "田中太郎", ["田中太郎", "田中", "田中部長"])]

        result = get_synonyms_for_primary(groups, "田中太郎")

        assert result == ["田中", "田中部長"]

    def test_returns_empty_for_primary_only_group(self) -> None:
        groups = [_make_group(1, "田中太郎", ["田中太郎"])]

        assert get_synonyms_for_primary(groups, "田中太郎") == []
