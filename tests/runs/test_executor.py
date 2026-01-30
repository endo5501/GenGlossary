"""Tests for PipelineExecutor."""

import sqlite3
import time
from pathlib import Path
from threading import Event
from unittest.mock import MagicMock, patch

import pytest

from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import ClassifiedTerm, Term, TermCategory, TermOccurrence
from genglossary.runs.executor import PipelineExecutor


@pytest.fixture
def project_db_path(tmp_path: Path) -> str:
    """Create a test project database."""
    db_path = tmp_path / "test_project.db"
    connection = get_connection(str(db_path))
    initialize_db(connection)
    connection.close()
    return str(db_path)


@pytest.fixture
def project_db(project_db_path: str) -> sqlite3.Connection:
    """Get a connection to the test project database."""
    connection = get_connection(project_db_path)
    yield connection
    connection.close()


@pytest.fixture
def executor() -> PipelineExecutor:
    """Create a PipelineExecutor instance."""
    return PipelineExecutor()


@pytest.fixture
def cancel_event() -> Event:
    """Create a cancellation event."""
    return Event()


@pytest.fixture
def log_callback():
    """Create a log callback that captures messages."""
    logs = []

    def callback(msg: dict) -> None:
        logs.append(msg)

    callback.logs = logs  # type: ignore
    return callback


class TestPipelineExecutorFull:
    """Tests for full scope execution."""

    def test_full_scope_raises_error_when_no_documents_cli_mode(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """CLIモード: ドキュメントが見つからない場合はRuntimeErrorを発生させる"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader:
            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock document loading to return empty list
            mock_loader.return_value.load_directory.return_value = []

            # Execute should raise RuntimeError (CLI mode with explicit doc_root)
            with pytest.raises(RuntimeError, match="Cannot execute pipeline without documents"):
                executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/some/path", run_id=1)

    def test_full_scope_raises_error_when_no_documents_gui_mode(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """GUIモード: DBにドキュメントがない場合はRuntimeErrorを発生させる"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:
            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock empty DB
            mock_list_docs.return_value = []

            # Execute should raise RuntimeError (GUI mode with default doc_root=".")
            with pytest.raises(RuntimeError, match="Cannot execute pipeline without documents"):
                executor.execute(project_db, "full", cancel_event, log_callback, doc_root=".", run_id=1)

    def test_full_scope_executes_all_steps(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """full scopeは全ステップを実行する（CLIモード）"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner, \
             patch("genglossary.runs.executor.delete_all_documents") as mock_delete_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock document loading
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="test.txt", content="test content")
            ]

            # Mock term extraction
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM),
                ClassifiedTerm(term="term2", category=TermCategory.TECHNICAL_TERM),
            ]

            # Mock glossary generation
            mock_glossary = Glossary(terms={
                "term1": Term(
                    name="term1",
                    definition="test definition",
                    confidence=0.9,
                    occurrences=[
                        TermOccurrence(
                            document_path="test.txt",
                            line_number=1,
                            context="test context"
                        )
                    ]
                )
            })
            mock_generator.return_value.generate.return_value = mock_glossary

            # Mock review
            mock_reviewer.return_value.review.return_value = []

            # Execute (CLI mode with explicit doc_root)
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path", run_id=1)

            # Verify all components were called
            mock_loader.return_value.load_directory.assert_called_once_with("/test/path")
            mock_extractor.return_value.extract_terms.assert_called_once()
            mock_generator.return_value.generate.assert_called_once()
            mock_reviewer.return_value.review.assert_called_once()

    def test_full_scope_respects_cancellation(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """キャンセル時は途中で停止する"""
        # Set cancellation before execution
        cancel_event.set()

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader:
            executor.execute(project_db, "full", cancel_event, log_callback, run_id=1)

            # DocumentLoader should not be called when cancelled
            mock_loader.return_value.load_directory.assert_not_called()


class TestPipelineExecutorFromTerms:
    """Tests for from_terms scope execution."""

    def test_from_terms_skips_document_loading_from_filesystem(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """from_termsはファイルシステムからの読み込みをスキップし、DBから取得する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data loading (v4: file_name and content from DB)
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test content"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Mock glossary generation
            mock_glossary = Glossary(terms={})
            mock_generator.return_value.generate.return_value = mock_glossary
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "from_terms", cancel_event, log_callback, run_id=1)

            # DocumentLoader.load_directory should not be called (we load from DB instead)
            mock_loader.return_value.load_directory.assert_not_called()
            # DocumentLoader.load_file should not be called (content comes from DB)
            mock_loader.return_value.load_file.assert_not_called()
            # TermExtractor should not be called
            mock_extractor.return_value.extract_terms.assert_not_called()


class TestPipelineExecutorProvisionalToRefined:
    """Tests for provisional_to_refined scope execution."""

    def test_provisional_to_refined_starts_from_review(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """provisional_to_refinedは精査から開始する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_provisional, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data loading (v4: file_name and content from DB)
            from genglossary.models.term import TermOccurrence
            mock_list_provisional.return_value = [
                {
                    "term_name": "term1",
                    "definition": "def1",
                    "confidence": 0.9,
                    "occurrences": [TermOccurrence(document_path="test.txt", line_number=1, context="ctx")]
                }
            ]
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test content"}]

            # Mock review
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "provisional_to_refined", cancel_event, log_callback, run_id=1)

            # Earlier stages should not be called
            mock_loader.return_value.load_directory.assert_not_called()
            # DocumentLoader.load_file should not be called (content comes from DB)
            mock_loader.return_value.load_file.assert_not_called()
            mock_extractor.return_value.extract_terms.assert_not_called()
            mock_generator.return_value.generate.assert_not_called()

            # Reviewer should be called
            mock_reviewer.return_value.review.assert_called_once()


class TestPipelineExecutorProgress:
    """Tests for progress reporting."""

    def test_progress_updates_are_logged(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """進捗がlog_callbackに送信される"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.delete_all_documents"):

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock components
            mock_loader.return_value.load_directory.return_value = [MagicMock(file_path="test.txt", content="test")]
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM)
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute (CLI mode with explicit doc_root)
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path", run_id=1)

            # Check that log messages were captured
            logs = log_callback.logs  # type: ignore

            # Should have at least start and completion messages
            assert len(logs) >= 2
            assert any("Starting pipeline execution" in log.get("message", "") for log in logs)
            assert any("completed" in log.get("message", "").lower() for log in logs)


class TestPipelineExecutorLogCallback:
    """Tests for log callback functionality."""

    def test_executor_uses_log_callback(
        self,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """executorがlog_callbackを使ってログを出力する"""
        logs = []
        callback = lambda msg: logs.append(msg)

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.delete_all_documents"):

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock components
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="test.txt", content="test")
            ]
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM)
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            executor = PipelineExecutor()
            # Execute (CLI mode with explicit doc_root)
            executor.execute(project_db, "full", cancel_event, callback, doc_root="/test/path", run_id=1)

            assert len(logs) > 0
            assert all(log.get("run_id") == 1 for log in logs)


class TestPipelineExecutorConfiguration:
    """Tests for executor configuration (doc_root, LLM settings)."""

    def test_executor_uses_doc_root(
        self,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """executorがdoc_rootパラメータを使用することを確認"""
        executor = PipelineExecutor(provider="ollama")

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock components
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="test.txt", content="test")
            ]
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM)
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with custom doc_root
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/custom/path", run_id=1)

            # Verify load_directory was called with the custom doc_root
            mock_loader.return_value.load_directory.assert_called_once_with("/custom/path")

    def test_executor_uses_llm_settings(
        self,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """executorがllm_provider/llm_modelを使用することを確認"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.delete_all_documents"):

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Create executor with custom provider and model
            executor = PipelineExecutor(provider="openai", model="gpt-4")

            # Mock components
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="test.txt", content="test")
            ]
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM)
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute (CLI mode with explicit doc_root)
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path", run_id=1)

            # Verify LLM client was created with custom settings
            mock_llm_factory.assert_called_once_with(provider="openai", model="gpt-4")

    def test_re_execution_clears_tables(
        self,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """再実行時にテーブルがクリアされることを確認"""
        executor = PipelineExecutor(provider="ollama")

        # Create mock clear functions
        mock_delete_terms = MagicMock()
        mock_delete_prov = MagicMock()
        mock_delete_issues = MagicMock()
        mock_delete_refined = MagicMock()

        # Patch _SCOPE_CLEAR_FUNCTIONS to use our mocks
        mock_scope_clear_functions = {
            "full": [mock_delete_terms, mock_delete_prov, mock_delete_issues, mock_delete_refined],
            "from_terms": [mock_delete_prov, mock_delete_issues, mock_delete_refined],
            "provisional_to_refined": [mock_delete_issues, mock_delete_refined],
        }

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor._SCOPE_CLEAR_FUNCTIONS", mock_scope_clear_functions), \
             patch("genglossary.runs.executor.delete_all_documents"):

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock components
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="test.txt", content="test")
            ]
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM)
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with full scope (CLI mode with explicit doc_root)
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path", run_id=1)

            # Verify tables were cleared before execution (documents are NOT cleared in _clear_tables_for_scope)
            mock_delete_terms.assert_called_once()
            mock_delete_prov.assert_called_once()
            mock_delete_issues.assert_called_once()
            mock_delete_refined.assert_called_once()


class TestPipelineExecutorDBFirstApproach:
    """Tests for DB-first document loading approach.

    The executor should:
    1. First try to load documents from DB
    2. If DB is empty and doc_root is specified, try filesystem
    3. If both are empty, raise error
    """

    def test_gui_mode_uses_db_documents_even_with_custom_doc_root(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """GUIモード: doc_rootが自動生成パスでもDBにドキュメントがあればDBを使用する

        これがバグ修正の核心テスト。GUIで作成したプロジェクトは
        doc_root = ~/.genglossary/projects/ProjectName のような値を持つが、
        ドキュメントはDBに保存されている。
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB documents (simulating GUI-uploaded files)
            mock_list_docs.return_value = [
                {"file_name": "uploaded.txt", "content": "uploaded content from GUI"}
            ]

            # Mock term extraction
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM),
            ]

            # Mock glossary generation
            mock_glossary = Glossary(terms={
                "term1": Term(
                    name="term1",
                    definition="test definition",
                    confidence=0.9,
                    occurrences=[
                        TermOccurrence(
                            document_path="uploaded.txt",
                            line_number=1,
                            context="uploaded content from GUI"
                        )
                    ]
                )
            })
            mock_generator.return_value.generate.return_value = mock_glossary
            mock_reviewer.return_value.review.return_value = []

            # Execute with a custom doc_root (simulating GUI project)
            # This is the key: doc_root is NOT "." but DB has documents
            executor.execute(
                project_db, "full", cancel_event, log_callback,
                doc_root="/Users/user/.genglossary/projects/MyProject",
                run_id=1,
            )

            # DocumentLoader.load_directory should NOT be called (DB has documents)
            mock_loader.return_value.load_directory.assert_not_called()

            # TermExtractor should be called with DB documents
            mock_extractor.return_value.extract_terms.assert_called_once()
            call_args = mock_extractor.return_value.extract_terms.call_args
            documents_arg = call_args[0][0]
            assert len(documents_arg) == 1
            assert documents_arg[0].file_path == "uploaded.txt"
            assert documents_arg[0].content == "uploaded content from GUI"

    def test_cli_mode_uses_filesystem_when_db_is_empty(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """CLIモード: DBが空でdoc_rootにファイルがある場合はファイルシステムを使用"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.delete_all_documents") as mock_delete_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock empty DB
            mock_list_docs.return_value = []

            # Mock filesystem loading
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="cli_file.txt", content="cli content")
            ]

            # Mock term extraction
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM),
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with explicit doc_root (CLI mode, empty DB)
            executor.execute(
                project_db, "full", cancel_event, log_callback,
                doc_root="/custom/cli/path",
                run_id=1,
            )

            # list_all_documents should be called first to check DB
            mock_list_docs.assert_called_once()

            # DocumentLoader.load_directory SHOULD be called (DB was empty)
            mock_loader.return_value.load_directory.assert_called_once_with("/custom/cli/path")

            # Documents from FS should be saved to DB
            mock_delete_docs.assert_called_once()

    def test_raises_error_when_both_db_and_filesystem_are_empty(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """DBもファイルシステムも空の場合はエラーを発生"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock empty DB
            mock_list_docs.return_value = []

            # Mock empty filesystem
            mock_loader.return_value.load_directory.return_value = []

            # Execute should raise RuntimeError
            with pytest.raises(RuntimeError, match="Cannot execute pipeline without documents"):
                executor.execute(
                    project_db, "full", cancel_event, log_callback,
                    doc_root="/empty/path",
                    run_id=1,
                )

    def test_db_documents_take_priority_over_filesystem(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """DBにドキュメントがある場合はファイルシステムをチェックしない（DB優先）"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB with documents
            mock_list_docs.return_value = [
                {"file_name": "db_file.txt", "content": "db content"}
            ]

            # Mock term extraction
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM),
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with doc_root
            executor.execute(
                project_db, "full", cancel_event, log_callback,
                doc_root="/some/path",
                run_id=1,
            )

            # DocumentLoader should NOT be called at all (DB has documents)
            mock_loader.return_value.load_directory.assert_not_called()


class TestPipelineExecutorProgressCallback:
    """Tests for _create_progress_callback method."""

    def test_create_progress_callback_logs_with_extended_fields(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """_create_progress_callback は拡張フィールド付きでログを出力する"""
        logs = []
        callback = lambda msg: logs.append(msg)

        # Set up executor context
        executor._run_id = 1
        executor._log_callback = callback

        # Create progress callback
        progress_cb = executor._create_progress_callback(project_db, "provisional")

        # Call the progress callback
        progress_cb(5, 20, "量子コンピュータ")

        # Verify log message
        assert len(logs) == 1
        log = logs[0]
        assert log["run_id"] == 1
        assert log["level"] == "info"
        assert log["step"] == "provisional"
        assert log["progress_current"] == 5
        assert log["progress_total"] == 20
        assert log["current_term"] == "量子コンピュータ"
        assert "25%" in log["message"]

    def test_create_progress_callback_calculates_percentage(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """進捗パーセントが正しく計算される"""
        logs = []
        executor._run_id = 1
        executor._log_callback = lambda msg: logs.append(msg)

        progress_cb = executor._create_progress_callback(project_db, "refined")

        # Test various percentages
        progress_cb(1, 10, "term1")  # 10%
        progress_cb(5, 10, "term5")  # 50%
        progress_cb(10, 10, "term10")  # 100%

        assert len(logs) == 3
        assert "10%" in logs[0]["message"]
        assert "50%" in logs[1]["message"]
        assert "100%" in logs[2]["message"]

    def test_create_progress_callback_handles_zero_total(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """total が 0 の場合も正常に動作する"""
        logs = []
        executor._run_id = 1
        executor._log_callback = lambda msg: logs.append(msg)

        progress_cb = executor._create_progress_callback(project_db, "provisional")

        # Should not raise error
        progress_cb(0, 0, "")

        assert len(logs) == 1
        assert "0%" in logs[0]["message"]


class TestPipelineExecutorLogExtended:
    """Tests for extended _log method."""

    def test_log_with_extended_fields(
        self,
        executor: PipelineExecutor,
    ) -> None:
        """_log は拡張フィールドを含むログを出力する"""
        logs = []
        executor._run_id = 1
        executor._log_callback = lambda msg: logs.append(msg)

        executor._log(
            "info",
            "量子コンピュータ: 25%",
            step="provisional",
            current=5,
            total=20,
            current_term="量子コンピュータ",
        )

        assert len(logs) == 1
        log = logs[0]
        assert log["run_id"] == 1
        assert log["level"] == "info"
        assert log["message"] == "量子コンピュータ: 25%"
        assert log["step"] == "provisional"
        assert log["progress_current"] == 5
        assert log["progress_total"] == 20
        assert log["current_term"] == "量子コンピュータ"

    def test_log_without_extended_fields_backward_compatible(
        self,
        executor: PipelineExecutor,
    ) -> None:
        """拡張フィールドなしの _log 呼び出しは後方互換性を保つ"""
        logs = []
        executor._run_id = 1
        executor._log_callback = lambda msg: logs.append(msg)

        executor._log("info", "Starting pipeline execution: full")

        assert len(logs) == 1
        log = logs[0]
        assert log["run_id"] == 1
        assert log["level"] == "info"
        assert log["message"] == "Starting pipeline execution: full"
        # 拡張フィールドは含まれないはず
        assert "step" not in log
        assert "progress_current" not in log


class TestPipelineExecutorProgressCallbackIntegration:
    """Tests for progress callback integration with GlossaryGenerator/Refiner."""

    def test_execute_from_terms_passes_term_progress_callback_to_generator(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """GlossaryGenerator に term_progress_callback が渡される"""
        logs = []
        callback = lambda msg: logs.append(msg)

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator_cls, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}, {"term_text": "term2"}]

            mock_glossary = Glossary(terms={})
            mock_generator_cls.return_value.generate.return_value = mock_glossary
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "from_terms", cancel_event, callback, run_id=1)

            # Verify term_progress_callback was passed to generate
            mock_generator_cls.return_value.generate.assert_called_once()
            call_kwargs = mock_generator_cls.return_value.generate.call_args.kwargs
            assert "term_progress_callback" in call_kwargs
            assert callable(call_kwargs["term_progress_callback"])

    def test_execute_refiner_passes_term_progress_callback_to_refiner(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """GlossaryRefiner に term_progress_callback が渡される"""
        logs = []
        callback = lambda msg: logs.append(msg)

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_prov.return_value = [
                {"term_name": "term1", "definition": "def1", "confidence": 0.8, "occurrences": []}
            ]

            mock_reviewer.return_value.review.return_value = [
                GlossaryIssue(term_name="term1", issue_type="unclear", description="Issue")
            ]

            mock_refiner_cls.return_value.refine.return_value = Glossary(terms={})

            executor.execute(project_db, "provisional_to_refined", cancel_event, callback, run_id=1)

            # Verify term_progress_callback was passed to refine
            mock_refiner_cls.return_value.refine.assert_called_once()
            call_kwargs = mock_refiner_cls.return_value.refine.call_args.kwargs
            assert "term_progress_callback" in call_kwargs
            assert callable(call_kwargs["term_progress_callback"])


class TestPipelineExecutorLogCallbackExceptionHandling:
    """Tests for log callback exception handling."""

    def test_log_continues_when_callback_raises_exception(
        self,
        executor: PipelineExecutor,
    ) -> None:
        """_log は callback が例外を投げても継続する"""
        exception_count = 0

        def failing_callback(msg: dict) -> None:
            nonlocal exception_count
            exception_count += 1
            raise RuntimeError("Callback error")

        executor._run_id = 1
        executor._log_callback = failing_callback

        # Should NOT raise exception even though callback fails
        executor._log("info", "Test message 1")
        executor._log("info", "Test message 2")
        executor._log("info", "Test message 3")

        # All three calls should have been attempted
        assert exception_count == 3

    def test_log_with_extended_fields_continues_when_callback_raises_exception(
        self,
        executor: PipelineExecutor,
    ) -> None:
        """拡張フィールド付き _log も callback 例外で継続する"""
        exception_count = 0

        def failing_callback(msg: dict) -> None:
            nonlocal exception_count
            exception_count += 1
            raise RuntimeError("Callback error")

        executor._run_id = 1
        executor._log_callback = failing_callback

        # Should NOT raise exception even though callback fails
        executor._log(
            "info",
            "量子コンピュータ: 25%",
            step="provisional",
            current=5,
            total=20,
            current_term="量子コンピュータ",
        )

        assert exception_count == 1


class TestPipelineExecutorDBDocumentsLegacy:
    """Legacy tests for backward compatibility (doc_root="." case)."""

    def test_full_scope_uses_db_documents_when_doc_root_is_default(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """doc_root="." (GUI mode) の場合、DBのドキュメントを使用する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB documents (simulating GUI-uploaded files)
            mock_list_docs.return_value = [
                {"file_name": "uploaded.txt", "content": "uploaded content"}
            ]

            # Mock term extraction
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM),
            ]

            # Mock glossary generation
            mock_glossary = Glossary(terms={
                "term1": Term(
                    name="term1",
                    definition="test definition",
                    confidence=0.9,
                    occurrences=[
                        TermOccurrence(
                            document_path="uploaded.txt",
                            line_number=1,
                            context="uploaded content"
                        )
                    ]
                )
            })
            mock_generator.return_value.generate.return_value = mock_glossary
            mock_reviewer.return_value.review.return_value = []

            # Execute full scope with default doc_root="." (GUI mode)
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root=".", run_id=1)

            # DocumentLoader.load_directory should NOT be called (DB documents used in GUI mode)
            mock_loader.return_value.load_directory.assert_not_called()

            # TermExtractor should be called with DB documents
            mock_extractor.return_value.extract_terms.assert_called_once()
            call_args = mock_extractor.return_value.extract_terms.call_args
            documents_arg = call_args[0][0]
            assert len(documents_arg) == 1
            assert documents_arg[0].file_path == "uploaded.txt"
            assert documents_arg[0].content == "uploaded content"

    def test_full_scope_uses_filesystem_when_doc_root_is_explicit(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """doc_root が明示的に指定された場合（CLIモード）、ファイルシステムから読み込みDBを上書き"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.delete_all_documents") as mock_delete_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock filesystem loading
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="cli_file.txt", content="cli content")
            ]

            # Mock term extraction
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM),
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute full scope with explicit doc_root (CLI mode)
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/custom/path", run_id=1)

            # DocumentLoader.load_directory SHOULD be called with custom path
            mock_loader.return_value.load_directory.assert_called_once_with("/custom/path")

            # Existing documents should be cleared before adding new ones
            mock_delete_docs.assert_called_once()


class TestPipelineExecutorBugFixes:
    """Tests for bug fixes discovered during code review.

    These tests reproduce the bugs before fixing:
    - A: Refined glossary is not saved when no issues exist
    - B: Duplicate terms cause IntegrityError crash
    - C: Same filename from different directories causes IntegrityError
    """

    def test_refined_glossary_saved_when_no_issues_exist(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """Bug A: issues がない場合でも refined glossary が保存される

        期待する動作:
        - Reviewer が空の issues を返した場合
        - Refiner は呼ばれない（改善する問題がないため）
        - しかし provisional glossary は refined として保存されるべき
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner, \
             patch("genglossary.runs.executor.create_refined_term") as mock_create_refined:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_prov.return_value = [
                {
                    "term_name": "term1",
                    "definition": "definition1",
                    "confidence": 0.9,
                    "occurrences": [TermOccurrence(document_path="test.txt", line_number=1, context="ctx")]
                }
            ]

            # Reviewer returns empty issues list
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "provisional_to_refined", cancel_event, log_callback, run_id=1)

            # Refiner should NOT be called (no issues to refine)
            mock_refiner.return_value.refine.assert_not_called()

            # But refined term should be saved (provisional copied to refined)
            mock_create_refined.assert_called_once_with(
                project_db,
                "term1",
                "definition1",
                0.9,
                [TermOccurrence(document_path="test.txt", line_number=1, context="ctx")]
            )

    def test_duplicate_terms_from_llm_do_not_crash_pipeline(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """Bug B: LLM が重複用語を返してもパイプラインがクラッシュしない

        期待する動作:
        - TermExtractor が同じ用語を複数回返した場合
        - IntegrityError は発生しない
        - 重複は無視され、ユニークな用語のみ保存される
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.delete_all_documents"):

            mock_llm_factory.return_value = MagicMock()
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="test.txt", content="test content")
            ]

            # LLM returns duplicate terms
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="duplicate_term", category=TermCategory.TECHNICAL_TERM),
                ClassifiedTerm(term="duplicate_term", category=TermCategory.TECHNICAL_TERM),  # duplicate
                ClassifiedTerm(term="unique_term", category=TermCategory.TECHNICAL_TERM),
            ]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Should NOT raise IntegrityError
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path", run_id=1)

            # Verify only unique terms were saved (no crash)
            from genglossary.db.term_repository import list_all_terms
            terms = list_all_terms(project_db)
            term_texts = [row["term_text"] for row in terms]
            assert "duplicate_term" in term_texts
            assert "unique_term" in term_texts
            # Should have exactly 2 unique terms, not 3
            assert len(term_texts) == 2

    def test_same_filename_from_different_directories_does_not_crash(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """Bug C: 異なるディレクトリの同名ファイルでもクラッシュしない

        期待する動作:
        - docs/README.md と examples/README.md を読み込んだ場合
        - IntegrityError は発生しない
        - ファイル名に相対パスを含めるか、衝突回避処理を行う
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            mock_llm_factory.return_value = MagicMock()

            # DB is empty (CLI mode)
            mock_list_docs.return_value = []

            # Multiple files with same basename from different directories
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="docs/README.md", content="docs readme content"),
                MagicMock(file_path="examples/README.md", content="examples readme content"),
            ]

            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="term1", category=TermCategory.TECHNICAL_TERM),
            ]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Should NOT raise IntegrityError
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path", run_id=1)

            # Verify both documents were saved (no crash)
            from genglossary.db.document_repository import list_all_documents
            docs = list_all_documents(project_db)
            assert len(docs) == 2
            # File names should be distinguishable
            file_names = [row["file_name"] for row in docs]
            assert len(set(file_names)) == 2  # Both should have unique names
