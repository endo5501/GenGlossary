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
            "runs",
            "schema_version",
            "terms_extracted",
        ]
        assert tables == expected_tables

    def test_initialize_db_sets_schema_version(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that initialize_db sets the schema version."""
        initialize_db(in_memory_db)

        version = get_schema_version(in_memory_db)
        assert version == 1

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
            "runs",
            "schema_version",
            "terms_extracted",
        ]
        assert tables == expected_tables


class TestRunsTable:
    """Test runs table schema."""

    def test_runs_table_has_correct_columns(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that runs table has all required columns."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("PRAGMA table_info(runs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "input_path" in columns
        assert "llm_provider" in columns
        assert "llm_model" in columns
        assert "status" in columns
        assert "started_at" in columns
        assert "completed_at" in columns
        assert "error_message" in columns

    def test_runs_table_default_status(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that runs table has default status 'running'."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute(
            "INSERT INTO runs (input_path, llm_provider, llm_model) VALUES (?, ?, ?)",
            ("/path/to/doc.txt", "ollama", "llama3.2"),
        )
        cursor.execute("SELECT status FROM runs WHERE id = 1")
        status = cursor.fetchone()[0]

        assert status == "running"


class TestDocumentsTable:
    """Test documents table schema."""

    def test_documents_table_has_foreign_key_to_runs(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that documents table references runs table."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert a run
        cursor.execute(
            "INSERT INTO runs (input_path, llm_provider, llm_model) VALUES (?, ?, ?)",
            ("/path/to/doc.txt", "ollama", "llama3.2"),
        )
        run_id = cursor.lastrowid

        # Insert a document
        cursor.execute(
            "INSERT INTO documents (run_id, file_path, content_hash) VALUES (?, ?, ?)",
            (run_id, "/path/to/doc.txt", "abc123"),
        )

        cursor.execute("SELECT COUNT(*) FROM documents WHERE run_id = ?", (run_id,))
        count = cursor.fetchone()[0]
        assert count == 1

    def test_documents_table_cascade_delete(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that deleting a run deletes associated documents."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert a run
        cursor.execute(
            "INSERT INTO runs (input_path, llm_provider, llm_model) VALUES (?, ?, ?)",
            ("/path/to/doc.txt", "ollama", "llama3.2"),
        )
        run_id = cursor.lastrowid

        # Insert a document
        cursor.execute(
            "INSERT INTO documents (run_id, file_path, content_hash) VALUES (?, ?, ?)",
            (run_id, "/path/to/doc.txt", "abc123"),
        )

        # Delete the run
        cursor.execute("DELETE FROM runs WHERE id = ?", (run_id,))

        # Check that document was deleted
        cursor.execute("SELECT COUNT(*) FROM documents WHERE run_id = ?", (run_id,))
        count = cursor.fetchone()[0]
        assert count == 0


class TestTermsExtractedTable:
    """Test terms_extracted table schema."""

    def test_terms_extracted_unique_constraint(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that (run_id, term_text) is unique."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert a run
        cursor.execute(
            "INSERT INTO runs (input_path, llm_provider, llm_model) VALUES (?, ?, ?)",
            ("/path/to/doc.txt", "ollama", "llama3.2"),
        )
        run_id = cursor.lastrowid

        # Insert first term
        cursor.execute(
            "INSERT INTO terms_extracted (run_id, term_text, category) VALUES (?, ?, ?)",
            (run_id, "量子コンピュータ", "技術用語"),
        )

        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO terms_extracted (run_id, term_text, category) VALUES (?, ?, ?)",
                (run_id, "量子コンピュータ", "技術用語"),
            )


class TestGlossaryProvisionalTable:
    """Test glossary_provisional table schema."""

    def test_glossary_provisional_stores_json_occurrences(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that occurrences can be stored as JSON."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert a run
        cursor.execute(
            "INSERT INTO runs (input_path, llm_provider, llm_model) VALUES (?, ?, ?)",
            ("/path/to/doc.txt", "ollama", "llama3.2"),
        )
        run_id = cursor.lastrowid

        # Insert provisional glossary entry
        occurrences_json = '[{"line_number": 1, "context": "量子コンピュータは..."}]'
        cursor.execute(
            """
            INSERT INTO glossary_provisional
            (run_id, term_name, definition, confidence, occurrences)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
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


class TestGlossaryIssuesTable:
    """Test glossary_issues table schema."""

    def test_glossary_issues_default_should_exclude(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that should_exclude defaults to 0."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert a run
        cursor.execute(
            "INSERT INTO runs (input_path, llm_provider, llm_model) VALUES (?, ?, ?)",
            ("/path/to/doc.txt", "ollama", "llama3.2"),
        )
        run_id = cursor.lastrowid

        # Insert issue without should_exclude
        cursor.execute(
            """
            INSERT INTO glossary_issues
            (run_id, term_name, issue_type, description)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, "量子コンピュータ", "unclear", "定義が曖昧"),
        )

        cursor.execute("SELECT should_exclude FROM glossary_issues WHERE id = 1")
        should_exclude = cursor.fetchone()[0]
        assert should_exclude == 0


class TestGlossaryRefinedTable:
    """Test glossary_refined table schema."""

    def test_glossary_refined_unique_constraint(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that (run_id, term_name) is unique."""
        initialize_db(in_memory_db)

        cursor = in_memory_db.cursor()

        # Insert a run
        cursor.execute(
            "INSERT INTO runs (input_path, llm_provider, llm_model) VALUES (?, ?, ?)",
            ("/path/to/doc.txt", "ollama", "llama3.2"),
        )
        run_id = cursor.lastrowid

        # Insert first refined entry
        occurrences_json = '[{"line_number": 1, "context": "量子コンピュータは..."}]'
        cursor.execute(
            """
            INSERT INTO glossary_refined
            (run_id, term_name, definition, confidence, occurrences)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
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
                (run_id, term_name, definition, confidence, occurrences)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    "量子コンピュータ",
                    "別の定義",
                    0.90,
                    occurrences_json,
                ),
            )
