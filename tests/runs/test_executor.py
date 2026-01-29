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
            with pytest.raises(RuntimeError, match="No documents found"):
                executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/some/path")

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
                executor.execute(project_db, "full", cancel_event, log_callback, doc_root=".")

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
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path")

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
            executor.execute(project_db, "full", cancel_event, log_callback)

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

            executor.execute(project_db, "from_terms", cancel_event, log_callback)

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

            executor.execute(project_db, "provisional_to_refined", cancel_event, log_callback)

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
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path")

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
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/custom/path")

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
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path")

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

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.delete_all_terms") as mock_delete_terms, \
             patch("genglossary.runs.executor.delete_all_provisional") as mock_delete_prov, \
             patch("genglossary.runs.executor.delete_all_issues") as mock_delete_issues, \
             patch("genglossary.runs.executor.delete_all_refined") as mock_delete_refined, \
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
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/test/path")

            # Verify tables were cleared before execution (documents are NOT cleared in _clear_tables_for_scope)
            mock_delete_terms.assert_called_once()
            mock_delete_prov.assert_called_once()
            mock_delete_issues.assert_called_once()
            mock_delete_refined.assert_called_once()


class TestPipelineExecutorDBDocuments:
    """Tests for DB-first document loading in full scope."""

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
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root=".")

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
            executor.execute(project_db, "full", cancel_event, log_callback, doc_root="/custom/path")

            # DocumentLoader.load_directory SHOULD be called with custom path
            mock_loader.return_value.load_directory.assert_called_once_with("/custom/path")

            # Existing documents should be cleared before adding new ones
            mock_delete_docs.assert_called_once()
