"""Tests for term_repository module."""

import sqlite3

import pytest

from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import (
    backup_user_notes,
    create_term,
    create_terms_batch,
    delete_all_terms,
    delete_term,
    get_term,
    list_all_terms,
    restore_user_notes,
    update_term,
)


@pytest.fixture
def db_with_schema(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Provide an in-memory database with schema initialized."""
    initialize_db(in_memory_db)
    return in_memory_db


class TestCreateTerm:
    """Test create_term function."""

    def test_create_term_returns_term_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_term returns a term ID."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        assert isinstance(term_id, int)
        assert term_id > 0

    def test_create_term_stores_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_term stores data correctly."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        cursor = db_with_schema.cursor()
        cursor.execute("SELECT * FROM terms_extracted WHERE id = ?", (term_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["term_text"] == "量子コンピュータ"
        assert row["category"] == "technical_term"

    def test_create_term_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that term_text must be unique."""
        create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        with pytest.raises(sqlite3.IntegrityError):
            create_term(
                db_with_schema,
                term_text="量子コンピュータ",
                category="technical_term",
            )


class TestGetTerm:
    """Test get_term function."""

    def test_get_term_returns_term_data(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_term returns term data."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        term = get_term(db_with_schema, term_id)

        assert term is not None
        assert term["id"] == term_id
        assert term["term_text"] == "量子コンピュータ"

    def test_get_term_returns_none_for_nonexistent_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_term returns None for non-existent ID."""
        term = get_term(db_with_schema, 999)

        assert term is None


class TestListAllTerms:
    """Test list_all_terms function."""

    def test_list_all_terms_returns_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms returns empty list when no terms."""
        terms = list_all_terms(db_with_schema)

        assert terms == []

    def test_list_all_terms_returns_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms returns all terms."""
        create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )
        create_term(
            db_with_schema,
            term_text="量子ビット",
            category="technical_term",
        )

        terms = list_all_terms(db_with_schema)

        assert len(terms) == 2

    def test_list_all_terms_excludes_terms_in_excluded_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms excludes terms that are in excluded list."""
        from genglossary.db.excluded_term_repository import add_excluded_term

        # Create terms
        create_term(db_with_schema, term_text="量子コンピュータ", category="technical")
        create_term(db_with_schema, term_text="量子ビット", category="technical")
        create_term(db_with_schema, term_text="重ね合わせ", category="concept")

        # Add one term to excluded list
        add_excluded_term(db_with_schema, "量子ビット", "manual")

        # list_all_terms should exclude "量子ビット"
        terms = list_all_terms(db_with_schema)

        assert len(terms) == 2
        term_texts = [t["term_text"] for t in terms]
        assert "量子コンピュータ" in term_texts
        assert "重ね合わせ" in term_texts
        assert "量子ビット" not in term_texts

    def test_list_all_terms_returns_all_when_no_excluded_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms returns all terms when excluded list is empty."""
        # Create terms
        create_term(db_with_schema, term_text="量子コンピュータ", category="technical")
        create_term(db_with_schema, term_text="量子ビット", category="technical")

        # No excluded terms added

        terms = list_all_terms(db_with_schema)

        assert len(terms) == 2

    def test_list_all_terms_only_excludes_exact_match(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms only excludes exact text match, not partial."""
        from genglossary.db.excluded_term_repository import add_excluded_term

        # Create terms
        create_term(db_with_schema, term_text="量子コンピュータ", category="technical")
        create_term(db_with_schema, term_text="量子", category="technical")

        # Exclude only "量子" (not "量子コンピュータ")
        add_excluded_term(db_with_schema, "量子", "manual")

        terms = list_all_terms(db_with_schema)

        # "量子コンピュータ" should still be included
        assert len(terms) == 1
        assert terms[0]["term_text"] == "量子コンピュータ"


class TestUpdateTerm:
    """Test update_term function."""

    def test_update_term_updates_text_and_category(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term updates term_text and category."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="量子計算機",
            category="updated_category",
        )

        term = get_term(db_with_schema, term_id)
        assert term is not None
        assert term["term_text"] == "量子計算機"
        assert term["category"] == "updated_category"

    def test_update_term_with_none_category_sets_null(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term sets category to NULL when None is provided."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="量子コンピュータ",
            category=None,
        )

        term = get_term(db_with_schema, term_id)
        assert term is not None
        assert term["category"] is None

    def test_update_term_with_nonexistent_id_raises_error(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term raises ValueError for non-existent term ID."""
        with pytest.raises(ValueError, match="Term with id 999 not found"):
            update_term(
                db_with_schema,
                term_id=999,
                term_text="存在しない用語",
                category="category",
            )


class TestDeleteTerm:
    """Test delete_term function."""

    def test_delete_term_removes_term(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_term removes the term."""
        term_id = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )

        delete_term(db_with_schema, term_id)

        term = get_term(db_with_schema, term_id)
        assert term is None

    def test_delete_term_with_nonexistent_id_does_nothing(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_term does nothing for non-existent term ID."""
        delete_term(db_with_schema, 999)

        term = get_term(db_with_schema, 999)
        assert term is None

    def test_delete_term_removes_from_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that deleted term is removed from list_all_terms."""
        term_id_1 = create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )
        term_id_2 = create_term(
            db_with_schema,
            term_text="量子ビット",
            category="technical_term",
        )

        delete_term(db_with_schema, term_id_1)

        terms = list_all_terms(db_with_schema)
        assert len(terms) == 1
        assert terms[0]["id"] == term_id_2


class TestDeleteAllTerms:
    """Test delete_all_terms function."""

    def test_delete_all_terms_removes_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_terms removes all terms."""
        create_term(
            db_with_schema,
            term_text="量子コンピュータ",
            category="technical_term",
        )
        create_term(
            db_with_schema,
            term_text="量子ビット",
            category="technical_term",
        )

        assert len(list_all_terms(db_with_schema)) == 2

        delete_all_terms(db_with_schema)

        assert len(list_all_terms(db_with_schema)) == 0

    def test_delete_all_terms_does_not_fail_when_empty(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that delete_all_terms does not fail when table is empty."""
        delete_all_terms(db_with_schema)  # Should not raise

        assert len(list_all_terms(db_with_schema)) == 0


class TestCreateTermsBatch:
    """Test create_terms_batch function."""

    def test_create_terms_batch_inserts_all_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch inserts all terms."""
        terms = [
            ("量子コンピュータ", "technical_term"),
            ("量子ビット", "technical_term"),
            ("重ね合わせ", "concept"),
        ]

        create_terms_batch(db_with_schema, terms)

        all_terms = list_all_terms(db_with_schema)
        assert len(all_terms) == 3
        term_texts = [t["term_text"] for t in all_terms]
        assert "量子コンピュータ" in term_texts
        assert "量子ビット" in term_texts
        assert "重ね合わせ" in term_texts

    def test_create_terms_batch_stores_category(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch stores category correctly."""
        terms = [
            ("量子コンピュータ", "technical_term"),
            ("重ね合わせ", None),
        ]

        create_terms_batch(db_with_schema, terms)

        all_terms = list_all_terms(db_with_schema)
        term_map = {t["term_text"]: t["category"] for t in all_terms}
        assert term_map["量子コンピュータ"] == "technical_term"
        assert term_map["重ね合わせ"] is None

    def test_create_terms_batch_with_empty_list(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch handles empty list."""
        create_terms_batch(db_with_schema, [])

        all_terms = list_all_terms(db_with_schema)
        assert len(all_terms) == 0

    def test_create_terms_batch_unique_constraint(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that create_terms_batch raises error on duplicate term_text."""
        terms = [
            ("量子コンピュータ", "technical_term"),
            ("量子コンピュータ", "concept"),  # Duplicate
        ]

        with pytest.raises(sqlite3.IntegrityError):
            create_terms_batch(db_with_schema, terms)


class TestUserNotes:
    """Test user_notes field in term operations."""

    def test_get_term_returns_user_notes(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that get_term returns user_notes field."""
        term_id = create_term(db_with_schema, "GP", "abbreviation")

        term = get_term(db_with_schema, term_id)
        assert term is not None
        assert term["user_notes"] == ""

    def test_list_all_terms_returns_user_notes(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that list_all_terms includes user_notes."""
        create_term(db_with_schema, "GP", "abbreviation")

        terms = list_all_terms(db_with_schema)
        assert len(terms) == 1
        assert terms[0]["user_notes"] == ""

    def test_update_term_updates_user_notes(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term can update user_notes."""
        term_id = create_term(db_with_schema, "GP", "abbreviation")

        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="GP",
            category="abbreviation",
            user_notes="General Practitioner（一般開業医）の略称",
        )

        term = get_term(db_with_schema, term_id)
        assert term is not None
        assert term["user_notes"] == "General Practitioner（一般開業医）の略称"

    def test_update_term_preserves_user_notes_when_not_provided(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that update_term preserves user_notes when not explicitly provided."""
        term_id = create_term(db_with_schema, "GP", "abbreviation")

        # Set user_notes first
        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="GP",
            category="abbreviation",
            user_notes="General Practitioner",
        )

        # Update without providing user_notes
        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="GP",
            category="medical",
        )

        term = get_term(db_with_schema, term_id)
        assert term is not None
        assert term["user_notes"] == "General Practitioner"


class TestListAllTermsIncludesRequiredTerms:
    """Test that list_all_terms includes required terms not yet extracted."""

    def test_includes_required_terms_not_in_extracted(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Required terms not in terms_extracted appear in list_all_terms."""
        from genglossary.db.required_term_repository import add_required_term

        create_term(db_with_schema, term_text="量子コンピュータ", category="technical")
        add_required_term(db_with_schema, "必須用語A", "manual")

        terms = list_all_terms(db_with_schema)

        term_texts = [t["term_text"] for t in terms]
        assert "量子コンピュータ" in term_texts
        assert "必須用語A" in term_texts
        assert len(terms) == 2

    def test_required_term_has_negative_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Required-only terms should have negative IDs to distinguish them."""
        from genglossary.db.required_term_repository import add_required_term

        add_required_term(db_with_schema, "必須用語A", "manual")

        terms = list_all_terms(db_with_schema)

        assert len(terms) == 1
        assert terms[0]["id"] < 0

    def test_required_term_has_null_category_and_empty_user_notes(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Required-only terms should have NULL category and empty user_notes."""
        from genglossary.db.required_term_repository import add_required_term

        add_required_term(db_with_schema, "必須用語A", "manual")

        terms = list_all_terms(db_with_schema)

        assert len(terms) == 1
        assert terms[0]["category"] is None
        assert terms[0]["user_notes"] == ""

    def test_no_duplicate_when_required_term_already_extracted(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Required term already in terms_extracted should not appear twice."""
        from genglossary.db.required_term_repository import add_required_term

        create_term(db_with_schema, term_text="共通用語", category="technical")
        add_required_term(db_with_schema, "共通用語", "manual")

        terms = list_all_terms(db_with_schema)

        term_texts = [t["term_text"] for t in terms]
        assert term_texts.count("共通用語") == 1
        # The extracted version should be used (positive ID)
        matching = [t for t in terms if t["term_text"] == "共通用語"]
        assert matching[0]["id"] > 0

    def test_required_term_overrides_excluded(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Required terms should appear even if also in excluded list."""
        from genglossary.db.excluded_term_repository import add_excluded_term
        from genglossary.db.required_term_repository import add_required_term

        add_required_term(db_with_schema, "必須かつ除外の用語", "manual")
        add_excluded_term(db_with_schema, "必須かつ除外の用語", "manual")

        terms = list_all_terms(db_with_schema)

        term_texts = [t["term_text"] for t in terms]
        assert "必須かつ除外の用語" in term_texts

    def test_extracted_required_and_excluded_uses_positive_id(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Term in all three tables should appear once with extracted (positive) ID."""
        from genglossary.db.excluded_term_repository import add_excluded_term
        from genglossary.db.required_term_repository import add_required_term

        create_term(db_with_schema, term_text="三重登録用語", category="technical")
        add_required_term(db_with_schema, "三重登録用語", "manual")
        add_excluded_term(db_with_schema, "三重登録用語", "manual")

        terms = list_all_terms(db_with_schema)

        matching = [t for t in terms if t["term_text"] == "三重登録用語"]
        assert len(matching) == 1
        assert matching[0]["id"] > 0  # Should use extracted (positive) ID

    def test_mixed_extracted_and_required_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Comprehensive test with extracted, required, and excluded terms."""
        from genglossary.db.excluded_term_repository import add_excluded_term
        from genglossary.db.required_term_repository import add_required_term

        # Extracted terms
        create_term(db_with_schema, term_text="抽出用語A", category="technical")
        create_term(db_with_schema, term_text="共通用語", category="concept")
        create_term(db_with_schema, term_text="除外される抽出用語", category="technical")

        # Required terms
        add_required_term(db_with_schema, "必須用語のみ", "manual")
        add_required_term(db_with_schema, "共通用語", "manual")  # Also extracted
        add_required_term(db_with_schema, "除外される必須用語", "manual")

        # Excluded terms
        add_excluded_term(db_with_schema, "除外される抽出用語", "manual")
        add_excluded_term(db_with_schema, "除外される必須用語", "manual")

        terms = list_all_terms(db_with_schema)
        term_texts = [t["term_text"] for t in terms]

        assert "抽出用語A" in term_texts
        assert "共通用語" in term_texts
        assert "必須用語のみ" in term_texts
        assert "除外される抽出用語" not in term_texts
        assert "除外される必須用語" in term_texts  # Required overrides excluded
        assert term_texts.count("共通用語") == 1
        assert len(terms) == 4


class TestBackupRestoreUserNotes:
    """Test backup_user_notes and restore_user_notes functions."""

    def test_backup_user_notes_returns_empty_dict_when_no_notes(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that backup returns empty dict when no user_notes are set."""
        create_term(db_with_schema, "量子コンピュータ", "technical")
        create_term(db_with_schema, "量子ビット", "technical")

        notes_map = backup_user_notes(db_with_schema)
        assert notes_map == {}

    def test_backup_user_notes_returns_only_non_empty_notes(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that backup returns only terms with non-empty user_notes."""
        term1_id = create_term(db_with_schema, "GP", "abbreviation")
        create_term(db_with_schema, "量子ビット", "technical")

        update_term(
            db_with_schema,
            term_id=term1_id,
            term_text="GP",
            category="abbreviation",
            user_notes="General Practitioner",
        )

        notes_map = backup_user_notes(db_with_schema)
        assert notes_map == {"GP": "General Practitioner"}

    def test_restore_user_notes_restores_notes_by_term_text(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that restore_user_notes restores notes after re-extract."""
        # Setup: create terms with notes
        term_id = create_term(db_with_schema, "GP", "abbreviation")
        update_term(
            db_with_schema,
            term_id=term_id,
            term_text="GP",
            category="abbreviation",
            user_notes="General Practitioner",
        )

        # Backup
        notes_map = backup_user_notes(db_with_schema)

        # Simulate re-extract
        delete_all_terms(db_with_schema)
        create_terms_batch(db_with_schema, [("GP", "medical"), ("新用語", "technical")])

        # Restore
        restore_user_notes(db_with_schema, notes_map)

        terms = list_all_terms(db_with_schema)
        term_map = {t["term_text"]: t["user_notes"] for t in terms}
        assert term_map["GP"] == "General Practitioner"
        assert term_map["新用語"] == ""

    def test_restore_user_notes_ignores_missing_terms(
        self, db_with_schema: sqlite3.Connection
    ) -> None:
        """Test that restore ignores notes for terms that no longer exist."""
        notes_map = {"削除された用語": "この用語のメモ"}

        create_terms_batch(db_with_schema, [("GP", "abbreviation")])

        # Should not raise
        restore_user_notes(db_with_schema, notes_map)

        terms = list_all_terms(db_with_schema)
        assert len(terms) == 1
        assert terms[0]["user_notes"] == ""
