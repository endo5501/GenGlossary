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
            "schema_version",
            "terms_extracted",
        ]
        assert tables == expected_tables

    def test_initialize_db_sets_schema_version(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that initialize_db sets the schema version."""
        initialize_db(in_memory_db)

        version = get_schema_version(in_memory_db)
        assert version == 2

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
            "schema_version",
            "terms_extracted",
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
        assert "llm_provider" in columns
        assert "llm_model" in columns
        assert "created_at" in columns

    def test_metadata_table_only_one_row(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that metadata table can only have id=1."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert with id=1 should succeed
        cursor.execute(
            "INSERT INTO metadata (id, llm_provider, llm_model) VALUES (?, ?, ?)",
            (1, "ollama", "llama3.2"),
        )
        in_memory_db.commit()

        # Try to insert with id=2 should fail (CHECK constraint)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO metadata (id, llm_provider, llm_model) VALUES (?, ?, ?)",
                (2, "openai", "gpt-4"),
            )

    def test_metadata_table_default_created_at(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that metadata table has default created_at."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO metadata (id, llm_provider, llm_model) VALUES (?, ?, ?)",
            (1, "ollama", "llama3.2"),
        )
        cursor.execute("SELECT created_at FROM metadata WHERE id = 1")
        created_at = cursor.fetchone()[0]

        assert created_at is not None


class TestDocumentsTable:
    """Test documents table schema."""

    def test_documents_table_has_required_columns(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that documents table has all required columns including created_at."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(documents)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "file_path" in columns
        assert "content_hash" in columns
        assert "created_at" in columns
        assert "run_id" not in columns  # v2: run_id should be removed

    def test_documents_table_unique_constraint(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that file_path is unique in v2."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert first document
        cursor.execute(
            "INSERT INTO documents (file_path, content_hash) VALUES (?, ?)",
            ("/path/to/doc.txt", "abc123"),
        )

        # Try to insert duplicate file_path
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO documents (file_path, content_hash) VALUES (?, ?)",
                ("/path/to/doc.txt", "def456"),
            )

    def test_documents_table_default_created_at(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that created_at has default value."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO documents (file_path, content_hash) VALUES (?, ?)",
            ("/path/to/doc.txt", "abc123"),
        )
        cursor.execute("SELECT created_at FROM documents WHERE id = 1")
        created_at = cursor.fetchone()[0]

        assert created_at is not None


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
        assert "created_at" in columns
        assert "run_id" not in columns  # v2: run_id should be removed

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
