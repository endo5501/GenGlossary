"""Tests for database schema initialization and migration."""

import sqlite3

import pytest

from genglossary.db.schema import get_schema_version, initialize_db


class TestSchemaInitialization:
    """Test database schema initialization."""

    def test_initialize_db_creates_all_tables(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that initialize_db creates all required tables."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "documents",
            "glossary_issues",
            "glossary_provisional",
            "glossary_refined",
            "metadata",
            "runs",
            "schema_version",
            "term_synonym_groups",
            "term_synonym_members",
            "terms_excluded",
            "terms_extracted",
            "terms_required",
        ]
        assert tables == expected_tables

    def test_initialize_db_sets_schema_version(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that initialize_db sets the schema version."""
        initialize_db(in_memory_db)

        version = get_schema_version(in_memory_db)
        assert version == 8  # v8: synonym group tables added

    def test_initialize_db_is_idempotent(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that initialize_db can be called multiple times safely."""
        initialize_db(in_memory_db)
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "documents",
            "glossary_issues",
            "glossary_provisional",
            "glossary_refined",
            "metadata",
            "runs",
            "schema_version",
            "term_synonym_groups",
            "term_synonym_members",
            "terms_excluded",
            "terms_extracted",
            "terms_required",
        ]
        assert tables == expected_tables


class TestMetadataTable:
    """Test metadata table schema."""

    def test_metadata_table_has_correct_columns(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that metadata table has all required columns."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(metadata)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "input_path" in columns
        assert "llm_provider" in columns
        assert "llm_model" in columns
        assert "created_at" in columns

    def test_metadata_table_only_one_row(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that metadata table can only have id=1."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert with id=1 should succeed
        cursor.execute(
            "INSERT INTO metadata (id, input_path, llm_provider, llm_model) VALUES (?, ?, ?, ?)",
            (1, "./docs", "ollama", "llama3.2"),
        )
        in_memory_db.commit()

        # Try to insert with id=2 should fail (CHECK constraint)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO metadata (id, input_path, llm_provider, llm_model) VALUES (?, ?, ?, ?)",
                (2, "./docs", "openai", "gpt-4"),
            )

    def test_metadata_table_default_created_at(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that metadata table has default created_at."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO metadata (id, input_path, llm_provider, llm_model) VALUES (?, ?, ?, ?)",
            (1, "./docs", "ollama", "llama3.2"),
        )
        cursor.execute("SELECT created_at FROM metadata WHERE id = 1")
        created_at = cursor.fetchone()[0]

        assert created_at is not None


class TestDocumentsTable:
    """Test documents table schema."""

    def test_documents_table_has_required_columns(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that documents table has all required columns including content."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(documents)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "file_name" in columns  # v4: file_path → file_name
        assert "content" in columns  # v4: content column added
        assert "content_hash" in columns
        assert "created_at" in columns
        assert "run_id" not in columns  # v2: run_id should be removed
        assert "file_path" not in columns  # v4: file_path should be removed

    def test_documents_table_unique_constraint(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that file_name is unique in v4."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert first document
        cursor.execute(
            "INSERT INTO documents (file_name, content, content_hash) VALUES (?, ?, ?)",
            ("doc.txt", "Hello World", "abc123"),
        )

        # Try to insert duplicate file_name
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO documents (file_name, content, content_hash) VALUES (?, ?, ?)",
                ("doc.txt", "Different content", "def456"),
            )

    def test_documents_table_default_created_at(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that created_at has default value."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO documents (file_name, content, content_hash) VALUES (?, ?, ?)",
            ("doc.txt", "Hello World", "abc123"),
        )
        cursor.execute("SELECT created_at FROM documents WHERE id = 1")
        created_at = cursor.fetchone()[0]

        assert created_at is not None

    def test_documents_table_content_column(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that content column stores file content correctly."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        test_content = "# Test Document\n\nThis is test content."
        cursor.execute(
            "INSERT INTO documents (file_name, content, content_hash) VALUES (?, ?, ?)",
            ("test.md", test_content, "hash123"),
        )
        cursor.execute("SELECT content FROM documents WHERE file_name = ?", ("test.md",))
        stored_content = cursor.fetchone()[0]

        assert stored_content == test_content


class TestTermsExtractedTable:
    """Test terms_extracted table schema."""

    def test_terms_extracted_has_required_columns(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that terms_extracted table has all required columns including created_at."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(terms_extracted)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "term_text" in columns
        assert "category" in columns
        assert "user_notes" in columns  # v7: user_notes column added
        assert "created_at" in columns
        assert "run_id" not in columns  # v2: run_id should be removed

    def test_terms_extracted_user_notes_default_empty(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that user_notes has default value of empty string."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO terms_extracted (term_text, category) VALUES (?, ?)",
            ("量子コンピュータ", "技術用語"),
        )
        cursor.execute("SELECT user_notes FROM terms_extracted WHERE id = 1")
        user_notes = cursor.fetchone()[0]

        assert user_notes == ""

    def test_terms_extracted_user_notes_stores_text(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that user_notes can store supplementary text."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        note = "GPはGeneral Practitioner（一般開業医）の略称"
        cursor.execute(
            "INSERT INTO terms_extracted (term_text, category, user_notes) VALUES (?, ?, ?)",
            ("GP", "略称", note),
        )
        cursor.execute("SELECT user_notes FROM terms_extracted WHERE term_text = ?", ("GP",))
        stored_note = cursor.fetchone()[0]

        assert stored_note == note

    def test_terms_extracted_unique_constraint(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that term_text is unique in v2."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert first term
        cursor.execute(
            "INSERT INTO terms_extracted (term_text, category) VALUES (?, ?)",
            ("量子コンピュータ", "技術用語"),
        )

        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO terms_extracted (term_text, category) VALUES (?, ?)",
                ("量子コンピュータ", "技術用語"),
            )

    def test_terms_extracted_default_created_at(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that created_at has default value."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO terms_extracted (term_text, category) VALUES (?, ?)",
            ("量子コンピュータ", "技術用語"),
        )
        cursor.execute("SELECT created_at FROM terms_extracted WHERE id = 1")
        created_at = cursor.fetchone()[0]

        assert created_at is not None


class TestGlossaryProvisionalTable:
    """Test glossary_provisional table schema."""

    def test_glossary_provisional_has_required_columns(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that glossary_provisional table has all required columns."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(glossary_provisional)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "term_name" in columns
        assert "definition" in columns
        assert "confidence" in columns
        assert "occurrences" in columns
        assert "created_at" in columns
        assert "run_id" not in columns  # v2: run_id should be removed

    def test_glossary_provisional_stores_json_occurrences(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that occurrences can be stored as JSON."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert provisional glossary entry
        occurrences_json = '[{"line_number": 1, "context": "量子コンピュータは..."}]'
        cursor.execute(
            """
            INSERT INTO glossary_provisional
            (term_name, definition, confidence, occurrences)
            VALUES (?, ?, ?, ?)
            """,
            (
                "量子コンピュータ",
                "量子力学の原理を利用したコンピュータ",
                0.95,
                occurrences_json,
            ),
        )

        cursor.execute(
            "SELECT occurrences FROM glossary_provisional WHERE term_name = ?",
            ("量子コンピュータ",),
        )
        stored_json = cursor.fetchone()[0]
        assert stored_json == occurrences_json

    def test_glossary_provisional_default_occurrences(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that occurrences has default value '[]' in v2."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            """
            INSERT INTO glossary_provisional (term_name, definition, confidence)
            VALUES (?, ?, ?)
            """,
            ("量子コンピュータ", "量子力学の原理を利用したコンピュータ", 0.95),
        )
        cursor.execute("SELECT occurrences FROM glossary_provisional WHERE id = 1")
        occurrences = cursor.fetchone()[0]

        assert occurrences == "[]"

    def test_glossary_provisional_unique_constraint(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that term_name is unique in v2."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert first entry
        cursor.execute(
            "INSERT INTO glossary_provisional (term_name, definition, confidence) VALUES (?, ?, ?)",
            ("量子コンピュータ", "定義1", 0.95),
        )

        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO glossary_provisional (term_name, definition, confidence) VALUES (?, ?, ?)",
                ("量子コンピュータ", "定義2", 0.90),
            )


class TestGlossaryIssuesTable:
    """Test glossary_issues table schema."""

    def test_glossary_issues_has_required_columns(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that glossary_issues table has all required columns."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(glossary_issues)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "term_name" in columns
        assert "issue_type" in columns
        assert "description" in columns
        assert "created_at" in columns
        assert "run_id" not in columns  # v2: run_id should be removed
        assert "should_exclude" not in columns  # v2: should_exclude should be removed
        assert "exclusion_reason" not in columns  # v2: exclusion_reason should be removed

    def test_glossary_issues_insert(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that issues can be inserted without run_id."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert issue
        cursor.execute(
            """
            INSERT INTO glossary_issues
            (term_name, issue_type, description)
            VALUES (?, ?, ?)
            """,
            ("量子コンピュータ", "unclear", "定義が曖昧"),
        )

        cursor.execute("SELECT COUNT(*) FROM glossary_issues")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_glossary_issues_default_created_at(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that created_at has default value."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO glossary_issues (term_name, issue_type, description) VALUES (?, ?, ?)",
            ("量子コンピュータ", "unclear", "定義が曖昧"),
        )
        cursor.execute("SELECT created_at FROM glossary_issues WHERE id = 1")
        created_at = cursor.fetchone()[0]

        assert created_at is not None


class TestGlossaryRefinedTable:
    """Test glossary_refined table schema."""

    def test_glossary_refined_has_required_columns(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that glossary_refined table has all required columns."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(glossary_refined)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "term_name" in columns
        assert "definition" in columns
        assert "confidence" in columns
        assert "occurrences" in columns
        assert "created_at" in columns
        assert "run_id" not in columns  # v2: run_id should be removed

    def test_glossary_refined_unique_constraint(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that term_name is unique in v2."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert first refined entry
        occurrences_json = '[{"line_number": 1, "context": "量子コンピュータは..."}]'
        cursor.execute(
            """
            INSERT INTO glossary_refined
            (term_name, definition, confidence, occurrences)
            VALUES (?, ?, ?, ?)
            """,
            (
                "量子コンピュータ",
                "量子力学の原理を利用したコンピュータ",
                0.95,
                occurrences_json,
            ),
        )

        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO glossary_refined
                (term_name, definition, confidence, occurrences)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "量子コンピュータ",
                    "別の定義",
                    0.90,
                    occurrences_json,
                ),
            )

    def test_glossary_refined_default_occurrences(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that occurrences has default value '[]' in v2."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            """
            INSERT INTO glossary_refined (term_name, definition, confidence)
            VALUES (?, ?, ?)
            """,
            ("量子コンピュータ", "量子力学の原理を利用したコンピュータ", 0.95),
        )
        cursor.execute("SELECT occurrences FROM glossary_refined WHERE id = 1")
        occurrences = cursor.fetchone()[0]

        assert occurrences == "[]"

    def test_glossary_refined_default_created_at(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that created_at has default value."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO glossary_refined (term_name, definition, confidence) VALUES (?, ?, ?)",
            ("量子コンピュータ", "量子力学の原理を利用したコンピュータ", 0.95),
        )
        cursor.execute("SELECT created_at FROM glossary_refined WHERE id = 1")
        created_at = cursor.fetchone()[0]

        assert created_at is not None


class TestMigrateTermsUserNotesV7:
    """Test v7 migration: add user_notes column to terms_extracted."""

    def test_migrate_adds_user_notes_column(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that migration adds user_notes to existing terms_extracted table."""
        # Create v6 schema (without user_notes)
        in_memory_db.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS terms_extracted (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_text TEXT NOT NULL UNIQUE,
                category TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        # Insert existing term without user_notes
        in_memory_db.execute(
            "INSERT INTO terms_extracted (term_text, category) VALUES (?, ?)",
            ("量子コンピュータ", "技術用語"),
        )
        in_memory_db.commit()

        # Run initialize_db which should migrate
        initialize_db(in_memory_db)

        # Verify user_notes column exists
        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(terms_extracted)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "user_notes" in columns

        # Verify existing data is preserved with empty default
        cursor.execute("SELECT user_notes FROM terms_extracted WHERE term_text = ?", ("量子コンピュータ",))
        user_notes = cursor.fetchone()[0]
        assert user_notes == ""
