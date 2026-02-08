"""Tests for synonym_repository module."""

import sqlite3

import pytest

from genglossary.db.schema import initialize_db
from genglossary.db.synonym_repository import (
    add_member,
    create_group,
    delete_group,
    get_synonyms_for_term,
    list_groups,
    remove_member,
    update_primary_term,
)


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateGroup:
    """Test create_group function."""

    def test_create_group_returns_group_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中", "田中部長"]
        )
        assert isinstance(group_id, int)
        assert group_id > 0

    def test_create_group_stores_primary_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中"]
        )

        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT primary_term_text FROM term_synonym_groups WHERE id = ?",
            (group_id,),
        )
        assert cursor.fetchone()[0] == "田中太郎"

    def test_create_group_stores_all_members(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中", "田中部長"]
        )

        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT term_text FROM term_synonym_members WHERE group_id = ? ORDER BY term_text",
            (group_id,),
        )
        texts = [row[0] for row in cursor.fetchall()]
        assert texts == ["田中", "田中太郎", "田中部長"]

    def test_create_group_with_duplicate_member_raises(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """A term already in another group cannot be added."""
        create_group(db_with_schema, "田中太郎", ["田中太郎", "田中"])

        with pytest.raises(sqlite3.IntegrityError):
            create_group(db_with_schema, "鈴木", ["鈴木", "田中"])


class TestDeleteGroup:
    """Test delete_group function."""

    def test_delete_group_removes_group(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中"]
        )

        result = delete_group(db_with_schema, group_id)

        assert result is True
        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM term_synonym_groups WHERE id = ?",
            (group_id,),
        )
        assert cursor.fetchone()[0] == 0

    def test_delete_group_cascades_members(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中"]
        )

        delete_group(db_with_schema, group_id)

        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM term_synonym_members WHERE group_id = ?",
            (group_id,),
        )
        assert cursor.fetchone()[0] == 0

    def test_delete_nonexistent_group_returns_false(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        result = delete_group(db_with_schema, 999)
        assert result is False


class TestAddMember:
    """Test add_member function."""

    def test_add_member_to_existing_group(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎"]
        )

        member_id = add_member(db_with_schema, group_id, "田中")

        assert isinstance(member_id, int)
        assert member_id > 0

    def test_add_member_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎"]
        )

        add_member(db_with_schema, group_id, "田中")

        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT term_text FROM term_synonym_members WHERE group_id = ? ORDER BY term_text",
            (group_id,),
        )
        texts = [row[0] for row in cursor.fetchall()]
        assert "田中" in texts

    def test_add_duplicate_member_raises(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎"]
        )

        with pytest.raises(sqlite3.IntegrityError):
            add_member(db_with_schema, group_id, "田中太郎")


class TestRemoveMember:
    """Test remove_member function."""

    def test_remove_member_from_group(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中"]
        )
        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT id FROM term_synonym_members WHERE term_text = ?",
            ("田中",),
        )
        member_id = cursor.fetchone()[0]

        result = remove_member(db_with_schema, group_id, member_id)

        assert result is True

    def test_remove_nonexistent_member_returns_false(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎"]
        )
        result = remove_member(db_with_schema, group_id, 999)
        assert result is False

    def test_remove_member_with_wrong_group_id_raises(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Removing a member with mismatched group_id raises ValueError."""
        group_a = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中"]
        )
        group_b = create_group(
            db_with_schema, "サーバー", ["サーバー", "サーバ"]
        )
        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT id FROM term_synonym_members WHERE term_text = ?",
            ("田中",),
        )
        member_id = cursor.fetchone()[0]

        with pytest.raises(ValueError, match="does not belong to group"):
            remove_member(db_with_schema, group_b, member_id)


class TestUpdatePrimaryTerm:
    """Test update_primary_term function."""

    def test_update_primary_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中"]
        )

        result = update_primary_term(db_with_schema, group_id, "田中")

        assert result is True
        cursor = db_with_schema.cursor()
        cursor.execute(
            "SELECT primary_term_text FROM term_synonym_groups WHERE id = ?",
            (group_id,),
        )
        assert cursor.fetchone()[0] == "田中"

    def test_update_nonexistent_group_returns_false(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        result = update_primary_term(db_with_schema, 999, "田中")
        assert result is False

    def test_update_primary_term_to_non_member_raises(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Changing primary_term_text to a non-member value raises ValueError."""
        group_id = create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中"]
        )

        with pytest.raises(ValueError, match="is not a member"):
            update_primary_term(db_with_schema, group_id, "鈴木")


class TestListGroups:
    """Test list_groups function."""

    def test_list_groups_returns_empty_when_no_groups(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        groups = list_groups(db_with_schema)
        assert groups == []

    def test_list_groups_returns_all_groups(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        create_group(db_with_schema, "田中太郎", ["田中太郎", "田中"])
        create_group(db_with_schema, "サーバー", ["サーバー", "サーバ"])

        groups = list_groups(db_with_schema)

        assert len(groups) == 2

    def test_list_groups_returns_synonym_group_models(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中", "田中部長"]
        )

        groups = list_groups(db_with_schema)

        assert len(groups) == 1
        group = groups[0]
        assert group.primary_term_text == "田中太郎"
        assert len(group.members) == 3
        member_texts = [m.term_text for m in group.members]
        assert "田中太郎" in member_texts
        assert "田中" in member_texts
        assert "田中部長" in member_texts


class TestGetSynonymsForTerm:
    """Test get_synonyms_for_term function."""

    def test_returns_empty_when_term_not_in_group(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        synonyms = get_synonyms_for_term(db_with_schema, "存在しない用語")
        assert synonyms == []

    def test_returns_other_members_for_term_in_group(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中", "田中部長"]
        )

        synonyms = get_synonyms_for_term(db_with_schema, "田中太郎")

        assert set(synonyms) == {"田中", "田中部長"}

    def test_returns_other_members_for_non_primary_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        create_group(
            db_with_schema, "田中太郎", ["田中太郎", "田中", "田中部長"]
        )

        synonyms = get_synonyms_for_term(db_with_schema, "田中")

        assert set(synonyms) == {"田中太郎", "田中部長"}
