"""Tests for PipelineExecutor."""

import sqlite3
import time
from pathlib import Path
from threading import Event, Thread
from unittest.mock import MagicMock, patch

import pytest

from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import ClassifiedTerm, Term, TermCategory, TermOccurrence
from genglossary.runs.executor import ExecutionContext, PipelineExecutor


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
    logs: list[dict] = []

    def callback(msg: dict) -> None:
        logs.append(msg)

    callback.logs = logs  # type: ignore
    return callback


@pytest.fixture
def execution_context(cancel_event: Event, log_callback) -> ExecutionContext:
    """Create an ExecutionContext with default settings."""
    return ExecutionContext(
        run_id=1,
        log_callback=log_callback,
        cancel_event=cancel_event,
    )


class TestPipelineExecutorFull:
    """Tests for full scope execution."""

    def test_full_scope_raises_error_when_no_documents_cli_mode(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
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
                executor.execute(project_db, "full", execution_context, doc_root="/some/path")

    def test_full_scope_raises_error_when_no_documents_gui_mode(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
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
                executor.execute(project_db, "full", execution_context, doc_root=".")

    def test_full_scope_executes_generate_review_refine(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """full scopeはextractをスキップしgenerate→review→refineを実行する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data (documents and terms already exist)
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test content"}]
            mock_list_terms.return_value = [
                {"term_text": "term1"},
                {"term_text": "term2"},
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

            # Execute full pipeline (GUI mode)
            executor.execute(project_db, "full", execution_context)

            # TermExtractor should NOT be called (extract skipped)
            mock_extractor.return_value.extract_terms.assert_not_called()
            # Generate, Review should be called
            mock_generator.return_value.generate.assert_called_once()
            mock_reviewer.return_value.review.assert_called_once()

    def test_full_scope_respects_cancellation(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """キャンセル時は途中で停止し、PipelineCancelledException を raise する"""
        from genglossary.runs.executor import PipelineCancelledException

        # Set cancellation before execution
        cancel_event.set()

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client"), \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader:
            with pytest.raises(PipelineCancelledException):
                executor.execute(project_db, "full", context)

            # DocumentLoader should not be called when cancelled
            mock_loader.return_value.load_directory.assert_not_called()


    def test_full_scope_skips_extract_and_loads_terms_from_db(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """full scopeはextractをスキップし、DBから既存の用語を読み込んでgenerate以降を実行する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data (documents and terms already exist)
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test content"}]
            mock_list_terms.return_value = [
                {"term_text": "term1"},
                {"term_text": "term2"},
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

            # Execute full pipeline (GUI mode)
            executor.execute(project_db, "full", execution_context)

            # TermExtractor should NOT be called (extract skipped)
            mock_extractor.return_value.extract_terms.assert_not_called()

            # Generator should be called with terms loaded from DB
            mock_generator.return_value.generate.assert_called_once()
            mock_reviewer.return_value.review.assert_called_once()

    def test_full_scope_raises_error_when_no_terms_in_db(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """full scope: DBに用語が存在しない場合はRuntimeErrorを発生させる"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB: documents exist but no terms
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test content"}]
            mock_list_terms.return_value = []

            with pytest.raises(RuntimeError, match="Cannot execute full pipeline without extracted terms"):
                executor.execute(project_db, "full", execution_context)

    def test_full_scope_does_not_clear_terms_table(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """full scopeはterms_extractedテーブルをクリアしない（extractスキップのため）"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner, \
             patch("genglossary.runs.executor.delete_all_terms") as mock_delete_terms:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test content"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_glossary = Glossary(terms={})
            mock_generator.return_value.generate.return_value = mock_glossary
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "full", execution_context)

            # delete_all_terms should NOT be called for full scope
            mock_delete_terms.assert_not_called()


class TestPipelineExecutorGenerate:
    """Tests for generate scope execution."""

    def test_generate_loads_from_db_and_skips_extraction(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """generateスコープはDBから用語を読み込み、抽出をスキップする"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data loading
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test content"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Mock glossary generation
            mock_glossary = Glossary(terms={})
            mock_generator.return_value.generate.return_value = mock_glossary

            executor.execute(project_db, "generate", execution_context)

            # DocumentLoader.load_directory should not be called (we load from DB instead)
            mock_loader.return_value.load_directory.assert_not_called()
            # TermExtractor should not be called
            mock_extractor.return_value.extract_terms.assert_not_called()
            # Generator should be called
            mock_generator.return_value.generate.assert_called_once()


class TestPipelineExecutorReview:
    """Tests for review scope execution."""

    def test_review_loads_provisional_and_runs_review_only(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """reviewスコープはprovisionalを読み込んでレビューのみ実行する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_provisional:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data loading
            from genglossary.models.term import TermOccurrence
            mock_list_provisional.return_value = [
                {
                    "term_name": "term1",
                    "definition": "def1",
                    "confidence": 0.9,
                    "occurrences": [TermOccurrence(document_path="test.txt", line_number=1, context="ctx")]
                }
            ]

            # Mock review
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "review", execution_context)

            # Earlier stages should not be called
            mock_loader.return_value.load_directory.assert_not_called()
            mock_extractor.return_value.extract_terms.assert_not_called()
            mock_generator.return_value.generate.assert_not_called()

            # Reviewer should be called
            mock_reviewer.return_value.review.assert_called_once()

            # Refiner should NOT be called (review scope only runs review)
            mock_refiner.return_value.refine.assert_not_called()


class TestPipelineExecutorProgress:
    """Tests for progress reporting."""

    def test_progress_updates_are_logged(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
        log_callback,
    ) -> None:
        """進捗がlog_callbackに送信される"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute (GUI mode)
            executor.execute(project_db, "full", execution_context)

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
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            executor = PipelineExecutor()
            # Execute (GUI mode)
            executor.execute(project_db, "full", context)

            assert len(logs) > 0
            assert all(log.get("run_id") == 1 for log in logs)


class TestPipelineExecutorConfiguration:
    """Tests for executor configuration (doc_root, LLM settings)."""

    def test_executor_uses_doc_root(
        self,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """executorがdoc_rootパラメータを使用することを確認"""
        executor = PipelineExecutor(provider="ollama")

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock empty DB (force filesystem loading)
            mock_list_docs.return_value = []
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Mock components
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="/custom/path/test.txt", content="test")
            ]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with custom doc_root
            executor.execute(project_db, "full", execution_context, doc_root="/custom/path")

            # Verify load_directory was called with the custom doc_root
            mock_loader.return_value.load_directory.assert_called_once_with("/custom/path")

    def test_executor_uses_llm_settings(
        self,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """executorがllm_provider/llm_modelを使用することを確認"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Create executor with custom provider and model
            executor = PipelineExecutor(provider="openai", model="gpt-4")

            # Mock DB data
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute (GUI mode)
            executor.execute(project_db, "full", execution_context)

            # Verify LLM client was created with custom settings
            mock_llm_factory.assert_called_once()
            call_kwargs = mock_llm_factory.call_args.kwargs
            assert call_kwargs["provider"] == "openai"
            assert call_kwargs["model"] == "gpt-4"

    def test_re_execution_clears_tables(
        self,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """再実行時にテーブルがクリアされることを確認（full scopeではtermsはクリアしない）"""
        executor = PipelineExecutor(provider="ollama")

        # Create mock clear functions
        mock_delete_prov = MagicMock()
        mock_delete_issues = MagicMock()
        mock_delete_refined = MagicMock()

        # Patch _SCOPE_CLEAR_FUNCTIONS to use our mocks (using Enum keys)
        # Full scope does NOT clear terms (extract is excluded)
        from genglossary.runs.executor import PipelineScope
        mock_scope_clear_functions = {
            PipelineScope.FULL: [mock_delete_prov, mock_delete_issues, mock_delete_refined],
            PipelineScope.EXTRACT: [MagicMock()],
            PipelineScope.GENERATE: [mock_delete_prov],
            PipelineScope.REVIEW: [mock_delete_issues],
            PipelineScope.REFINE: [mock_delete_refined],
        }

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor._SCOPE_CLEAR_FUNCTIONS", mock_scope_clear_functions), \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB data
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with full scope (GUI mode)
            executor.execute(project_db, "full", execution_context)

            # Verify tables were cleared (terms NOT cleared for full scope)
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
        execution_context: ExecutionContext,
    ) -> None:
        """GUIモード: doc_rootが自動生成パスでもDBにドキュメントがあればDBを使用する

        これがバグ修正の核心テスト。GUIで作成したプロジェクトは
        doc_root = ~/.genglossary/projects/ProjectName のような値を持つが、
        ドキュメントはDBに保存されている。
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB documents (simulating GUI-uploaded files)
            mock_list_docs.return_value = [
                {"file_name": "uploaded.txt", "content": "uploaded content from GUI"}
            ]
            mock_list_terms.return_value = [{"term_text": "term1"}]

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
                project_db, "full", execution_context,
                doc_root="/Users/user/.genglossary/projects/MyProject",
            )

            # DocumentLoader.load_directory should NOT be called (DB has documents)
            mock_loader.return_value.load_directory.assert_not_called()

    def test_cli_mode_uses_filesystem_when_db_is_empty(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """CLIモード: DBが空でdoc_rootにファイルがある場合はファイルシステムを使用"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms, \
             patch("genglossary.runs.executor.delete_all_documents") as mock_delete_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock empty DB
            mock_list_docs.return_value = []
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Mock filesystem loading
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="/custom/cli/path/cli_file.txt", content="cli content")
            ]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with explicit doc_root (CLI mode, empty DB)
            executor.execute(
                project_db, "full", execution_context,
                doc_root="/custom/cli/path",
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
        execution_context: ExecutionContext,
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
                    project_db, "full", execution_context,
                    doc_root="/empty/path",
                )

    def test_db_documents_take_priority_over_filesystem(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """DBにドキュメントがある場合はファイルシステムをチェックしない（DB優先）"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB with documents and terms
            mock_list_docs.return_value = [
                {"file_name": "db_file.txt", "content": "db content"}
            ]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with doc_root
            executor.execute(
                project_db, "full", execution_context,
                doc_root="/some/path",
            )

            # DocumentLoader should NOT be called at all (DB has documents)
            mock_loader.return_value.load_directory.assert_not_called()


class TestPipelineExecutorProgressCallback:
    """Tests for _create_progress_callback method."""

    def test_create_progress_callback_logs_with_extended_fields(
        self,
        executor: PipelineExecutor,
        cancel_event: Event,
    ) -> None:
        """_create_progress_callback は拡張フィールド付きでログを出力する"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        # Create context
        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.update_run_progress") as mock_update:
            # Create progress callback with mock connection
            mock_conn = MagicMock()
            progress_cb = executor._create_progress_callback(mock_conn, context, "provisional")

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

            # Verify database was updated
            mock_update.assert_called_once_with(mock_conn, 1, 5, 20, "provisional")

    def test_create_progress_callback_calculates_percentage(
        self,
        executor: PipelineExecutor,
        cancel_event: Event,
    ) -> None:
        """進捗パーセントが正しく計算される"""
        logs: list[dict] = []
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.update_run_progress"):
            mock_conn = MagicMock()
            progress_cb = executor._create_progress_callback(mock_conn, context, "refined")

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
        cancel_event: Event,
    ) -> None:
        """total が 0 の場合も正常に動作する"""
        logs: list[dict] = []
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.update_run_progress"):
            mock_conn = MagicMock()
            progress_cb = executor._create_progress_callback(mock_conn, context, "provisional")

            # Should not raise error
            progress_cb(0, 0, "")

            assert len(logs) == 1
            assert "0%" in logs[0]["message"]

    def test_create_progress_callback_handles_empty_term_name(
        self,
        executor: PipelineExecutor,
        cancel_event: Event,
    ) -> None:
        """term_name が空の場合、メッセージに ': ' が含まれない

        空の term_name で `f"{term_name}: {percent}%"` とすると ": 0%" になる。
        これを避け、フォールバックラベルを使用するか current_term を省略する。
        """
        logs: list[dict] = []
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.update_run_progress"):
            mock_conn = MagicMock()
            progress_cb = executor._create_progress_callback(mock_conn, context, "provisional")

            # Call with empty term_name
            progress_cb(1, 10, "")

            assert len(logs) == 1
            message = logs[0]["message"]
            # Should NOT start with ": " (bad format from empty term_name)
            assert not message.startswith(": "), f"Message should not start with ': ', got: {message}"
            # Should contain percentage
            assert "10%" in message
            # current_term should be omitted when empty
            assert "current_term" not in logs[0] or logs[0]["current_term"] == ""

    def test_create_progress_callback_handles_whitespace_term_name(
        self,
        executor: PipelineExecutor,
        cancel_event: Event,
    ) -> None:
        """term_name がホワイトスペースのみの場合も空と同様に扱う"""
        logs: list[dict] = []
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.update_run_progress"):
            mock_conn = MagicMock()
            progress_cb = executor._create_progress_callback(mock_conn, context, "provisional")

            # Call with whitespace-only term_name
            progress_cb(1, 10, "   ")

            assert len(logs) == 1
            message = logs[0]["message"]
            # Should NOT start with whitespace + ": " (bad format)
            assert not message.startswith(": "), f"Message should not start with ': ', got: {message}"
            assert "   :" not in message, "Whitespace should be stripped"
            # Should contain percentage
            assert "10%" in message


class TestPipelineExecutorLogExtended:
    """Tests for extended _log method."""

    def test_log_with_extended_fields(
        self,
        executor: PipelineExecutor,
        cancel_event: Event,
    ) -> None:
        """_log は拡張フィールドを含むログを出力する"""
        logs: list[dict] = []
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        executor._log(
            context,
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
        cancel_event: Event,
    ) -> None:
        """拡張フィールドなしの _log 呼び出しは後方互換性を保つ"""
        logs: list[dict] = []
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        executor._log(context, "info", "Starting pipeline execution: full")

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

    def test_execute_generate_passes_term_progress_callback_to_generator(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """GlossaryGenerator に term_progress_callback が渡される"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}, {"term_text": "term2"}]

            mock_glossary = Glossary(terms={})
            mock_generator_cls.return_value.generate.return_value = mock_glossary

            executor.execute(project_db, "generate", context)

            # Verify term_progress_callback was passed to generate
            mock_generator_cls.return_value.generate.assert_called_once()
            call_kwargs = mock_generator_cls.return_value.generate.call_args.kwargs
            assert "term_progress_callback" in call_kwargs
            assert callable(call_kwargs["term_progress_callback"])

    def test_execute_refine_passes_term_progress_callback_to_refiner(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """GlossaryRefiner に term_progress_callback が渡される"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.list_all_issues") as mock_list_issues, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_prov.return_value = [
                {"term_name": "term1", "definition": "def1", "confidence": 0.8, "occurrences": []}
            ]
            mock_list_issues.return_value = [
                {"term_name": "term1", "issue_type": "unclear", "description": "Issue", "should_exclude": 0, "exclusion_reason": None}
            ]

            mock_refiner_cls.return_value.refine.return_value = Glossary(terms={})

            executor.execute(project_db, "refine", context)

            # Verify term_progress_callback was passed to refine
            mock_refiner_cls.return_value.refine.assert_called_once()
            call_kwargs = mock_refiner_cls.return_value.refine.call_args.kwargs
            assert "term_progress_callback" in call_kwargs
            assert callable(call_kwargs["term_progress_callback"])

    def test_execute_extract_passes_progress_callback_to_extractor(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """TermExtractor に progress_callback が渡される"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]

            mock_extractor_cls.return_value.extract_terms.return_value = []

            executor.execute(project_db, "extract", context)

            # Verify progress_callback was passed to extract_terms
            mock_extractor_cls.return_value.extract_terms.assert_called_once()
            call_kwargs = mock_extractor_cls.return_value.extract_terms.call_args.kwargs
            assert "progress_callback" in call_kwargs
            assert callable(call_kwargs["progress_callback"])

    def test_execute_extract_logs_start_message_in_japanese(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """用語抽出開始時に日本語のメッセージがログ出力される"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_extractor_cls.return_value.extract_terms.return_value = []

            executor.execute(project_db, "extract", context)

            # Find the extract start message
            extract_start_logs = [
                log for log in logs
                if log.get("level") == "info" and "用語抽出を開始" in log.get("message", "")
            ]
            assert len(extract_start_logs) == 1
            assert "用語抽出を開始しました" in extract_start_logs[0]["message"]

    def test_execute_extract_progress_callback_sends_step_field(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """用語抽出の進捗コールバックが step='extract' を含むログを出力する"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]

            # Capture the progress callback and simulate calling it
            captured_callback = None

            def capture_extract_terms(*args, **kwargs):
                nonlocal captured_callback
                captured_callback = kwargs.get("progress_callback")
                return []

            mock_extractor_cls.return_value.extract_terms.side_effect = capture_extract_terms

            executor.execute(project_db, "extract", context)

            # Verify callback was captured
            assert captured_callback is not None

            # Clear logs and call the callback
            logs.clear()
            captured_callback(3, 10)

            # Verify log has step='extract' and progress fields
            assert len(logs) == 1
            assert logs[0]["step"] == "extract"
            assert logs[0]["progress_current"] == 3
            assert logs[0]["progress_total"] == 10

    def test_execute_review_progress_callback_sends_step_field(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """レビューの進捗コールバックが step='issues' を含むログを出力する"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_prov.return_value = [
                {"term_name": "term1", "definition": "def1", "confidence": 0.8, "occurrences": []}
            ]

            # Capture the batch_progress_callback and simulate calling it
            captured_callback = None

            def capture_review(*args, **kwargs):
                nonlocal captured_callback
                captured_callback = kwargs.get("batch_progress_callback")
                return []

            mock_reviewer_cls.return_value.review.side_effect = capture_review

            executor.execute(project_db, "review", context)

            # Verify callback was captured
            assert captured_callback is not None

            # Clear logs and call the callback
            logs.clear()
            captured_callback(3, 10)

            # Verify log has step='issues' and progress fields
            assert len(logs) == 1
            assert logs[0]["step"] == "issues"
            assert logs[0]["progress_current"] == 3
            assert logs[0]["progress_total"] == 10

    def test_review_emits_initial_step_update_before_processing(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """レビューステップ開始時に初期進捗更新（step='issues'）が送信される"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_prov.return_value = [
                {"term_name": "term1", "definition": "def1", "confidence": 0.8, "occurrences": []},
                {"term_name": "term2", "definition": "def2", "confidence": 0.9, "occurrences": []},
            ]

            # Track when batch_progress_callback is first called
            callback_call_order: list[str] = []

            def capture_review(*args, **kwargs):
                callback_call_order.append("review_called")
                return []

            mock_reviewer_cls.return_value.review.side_effect = capture_review

            executor.execute(project_db, "review", context)

            # Find logs with step='issues' that were emitted BEFORE review was called
            # The initial update should have current=0, total=batch_count
            # With 2 terms and default batch_size=20, batch_count=1
            initial_step_logs = [
                log for log in logs
                if log.get("step") == "issues" and log.get("progress_current") == 0
            ]

            assert len(initial_step_logs) >= 1, \
                "Expected initial step update with step='issues' and progress_current=0"
            assert initial_step_logs[0]["progress_total"] == 1, \
                "Expected progress_total to equal batch count (1 batch for 2 terms)"

    def test_review_emits_initial_step_update_for_empty_glossary(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
    ) -> None:
        """空の用語集でも初期進捗更新（step='issues'）が送信される"""
        logs: list[dict] = []
        callback = lambda msg: logs.append(msg)

        context = ExecutionContext(
            run_id=1,
            log_callback=callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer_cls:

            mock_llm_factory.return_value = MagicMock()
            # Empty glossary - no terms
            mock_list_prov.return_value = []

            mock_reviewer_cls.return_value.review.return_value = []

            # Even with empty glossary, we expect RuntimeError because
            # _load_provisional_glossary raises when no terms found
            # But we want to test the _do_review directly with empty Glossary
            # So we need to patch _load_provisional_glossary to return empty Glossary

        # Test _do_review directly with empty glossary
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_reviewer_cls.return_value.review.return_value = []

            logs.clear()
            empty_glossary = Glossary()

            # Call _do_review directly with empty glossary
            executor._do_review(project_db, context, empty_glossary)

            # Should still emit initial step update even for empty glossary
            initial_step_logs = [
                log for log in logs
                if log.get("step") == "issues" and log.get("progress_current") == 0
            ]

            assert len(initial_step_logs) >= 1, \
                "Expected initial step update with step='issues' even for empty glossary"
            assert initial_step_logs[0]["progress_total"] == 0, \
                "Expected progress_total=0 for empty glossary"


class TestPipelineExecutorLogCallbackExceptionHandling:
    """Tests for log callback exception handling."""

    def test_log_continues_when_callback_raises_exception(
        self,
        executor: PipelineExecutor,
        cancel_event: Event,
    ) -> None:
        """_log は callback が例外を投げても継続する"""
        exception_count = 0

        def failing_callback(msg: dict) -> None:
            nonlocal exception_count
            exception_count += 1
            raise RuntimeError("Callback error")

        context = ExecutionContext(
            run_id=1,
            log_callback=failing_callback,
            cancel_event=cancel_event,
        )

        # Should NOT raise exception even though callback fails
        executor._log(context, "info", "Test message 1")
        executor._log(context, "info", "Test message 2")
        executor._log(context, "info", "Test message 3")

        # All three calls should have been attempted
        assert exception_count == 3

    def test_log_with_extended_fields_continues_when_callback_raises_exception(
        self,
        executor: PipelineExecutor,
        cancel_event: Event,
    ) -> None:
        """拡張フィールド付き _log も callback 例外で継続する"""
        exception_count = 0

        def failing_callback(msg: dict) -> None:
            nonlocal exception_count
            exception_count += 1
            raise RuntimeError("Callback error")

        context = ExecutionContext(
            run_id=1,
            log_callback=failing_callback,
            cancel_event=cancel_event,
        )

        # Should NOT raise exception even though callback fails
        executor._log(
            context,
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
        execution_context: ExecutionContext,
    ) -> None:
        """doc_root="." (GUI mode) の場合、DBのドキュメントを使用する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock DB documents and terms
            mock_list_docs.return_value = [
                {"file_name": "uploaded.txt", "content": "uploaded content"}
            ]
            mock_list_terms.return_value = [{"term_text": "term1"}]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute full scope with default doc_root="." (GUI mode)
            executor.execute(project_db, "full", execution_context, doc_root=".")

            # DocumentLoader.load_directory should NOT be called (DB documents used in GUI mode)
            mock_loader.return_value.load_directory.assert_not_called()

    def test_full_scope_uses_filesystem_when_doc_root_is_explicit(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """doc_root が明示的に指定された場合（CLIモード）、ファイルシステムから読み込みDBを上書き"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms, \
             patch("genglossary.runs.executor.delete_all_documents") as mock_delete_docs:

            # Mock LLM client
            mock_llm_client = MagicMock()
            mock_llm_factory.return_value = mock_llm_client

            # Mock filesystem loading
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="/custom/path/cli_file.txt", content="cli content")
            ]

            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute full scope with explicit doc_root (CLI mode)
            executor.execute(project_db, "full", execution_context, doc_root="/custom/path")

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
        execution_context: ExecutionContext,
    ) -> None:
        """Bug A: issues がない場合でも refined glossary が保存される

        期待する動作:
        - DB に issues がない場合
        - Refiner は呼ばれない（改善する問題がないため）
        - しかし provisional glossary は refined として保存されるべき
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.list_all_issues") as mock_list_issues, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner, \
             patch("genglossary.runs.executor.create_refined_terms_batch") as mock_create_refined_batch:

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

            # No issues in DB
            mock_list_issues.return_value = []

            executor.execute(project_db, "refine", execution_context)

            # Refiner should NOT be called (no issues to refine)
            mock_refiner.return_value.refine.assert_not_called()

            # But refined terms should be saved using batch insert (provisional copied to refined)
            mock_create_refined_batch.assert_called_once()
            call_args = mock_create_refined_batch.call_args
            assert call_args[0][0] == project_db
            terms_data = call_args[0][1]
            assert len(terms_data) == 1
            assert terms_data[0][0] == "term1"
            assert terms_data[0][1] == "definition1"
            assert terms_data[0][2] == 0.9

    def test_duplicate_terms_from_llm_do_not_crash_extract_scope(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
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
             patch("genglossary.runs.executor.delete_all_documents"):

            mock_llm_factory.return_value = MagicMock()
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="/test/path/test.txt", content="test content")
            ]

            # LLM returns duplicate terms
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="duplicate_term", category=TermCategory.TECHNICAL_TERM),
                ClassifiedTerm(term="duplicate_term", category=TermCategory.TECHNICAL_TERM),  # duplicate
                ClassifiedTerm(term="unique_term", category=TermCategory.TECHNICAL_TERM),
            ]

            # Should NOT raise IntegrityError (using extract scope directly)
            executor.execute(project_db, "extract", execution_context, doc_root="/test/path")

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
        execution_context: ExecutionContext,
    ) -> None:
        """Bug C: 異なるディレクトリの同名ファイルでもクラッシュしない

        期待する動作:
        - docs/README.md と examples/README.md を読み込んだ場合
        - IntegrityError は発生しない
        - ファイル名に相対パスを含めるか、衝突回避処理を行う
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            mock_llm_factory.return_value = MagicMock()

            # DB is empty (CLI mode)
            mock_list_docs.return_value = []
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Multiple files with same basename from different directories
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="/test/path/docs/README.md", content="docs readme content"),
                MagicMock(file_path="/test/path/examples/README.md", content="examples readme content"),
            ]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Should NOT raise IntegrityError
            executor.execute(project_db, "full", execution_context, doc_root="/test/path")

            # Verify both documents were saved (no crash)
            from genglossary.db.document_repository import list_all_documents
            docs = list_all_documents(project_db)
            assert len(docs) == 2
            # File names should be distinguishable
            file_names = [row["file_name"] for row in docs]
            assert len(set(file_names)) == 2  # Both should have unique names


class TestPipelineExecutorUnknownScope:
    """Tests for unknown scope handling."""

    def test_unknown_scope_raises_value_error(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """不明なスコープはValueErrorを発生させる"""
        with patch("genglossary.runs.executor.create_llm_client"):
            # Invalid scope string raises ValueError from PipelineScope enum conversion
            with pytest.raises(ValueError, match="invalid_scope.*is not a valid PipelineScope"):
                executor.execute(project_db, "invalid_scope", execution_context)


class TestPipelineScopeEnum:
    """Tests for PipelineScope enum."""

    def test_pipeline_scope_enum_exists(self) -> None:
        """PipelineScope Enum が存在することを確認"""
        from genglossary.runs.executor import PipelineScope

        assert hasattr(PipelineScope, "FULL")
        assert hasattr(PipelineScope, "EXTRACT")
        assert hasattr(PipelineScope, "GENERATE")
        assert hasattr(PipelineScope, "REVIEW")
        assert hasattr(PipelineScope, "REFINE")

    def test_pipeline_scope_values(self) -> None:
        """PipelineScope Enum の値が正しいことを確認"""
        from genglossary.runs.executor import PipelineScope

        assert PipelineScope.FULL.value == "full"
        assert PipelineScope.EXTRACT.value == "extract"
        assert PipelineScope.GENERATE.value == "generate"
        assert PipelineScope.REVIEW.value == "review"
        assert PipelineScope.REFINE.value == "refine"

    def test_old_scopes_removed(self) -> None:
        """旧スコープが削除されていることを確認"""
        from genglossary.runs.executor import PipelineScope

        assert not hasattr(PipelineScope, "FROM_TERMS")
        assert not hasattr(PipelineScope, "PROVISIONAL_TO_REFINED")

    def test_execute_accepts_pipeline_scope_enum(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """execute メソッドが PipelineScope Enum を受け付けることを確認"""
        from genglossary.runs.executor import PipelineCancelledException, PipelineScope

        # Set cancellation to skip actual execution
        cancel_event.set()

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client"):
            # Should raise PipelineCancelledException (not TypeError) when using enum
            with pytest.raises(PipelineCancelledException):
                executor.execute(project_db, PipelineScope.FULL, context)

    def test_scope_clear_functions_use_enum_keys(self) -> None:
        """_SCOPE_CLEAR_FUNCTIONS が PipelineScope Enum をキーとして使用することを確認"""
        from genglossary.runs.executor import PipelineScope, _SCOPE_CLEAR_FUNCTIONS

        # Keys must be PipelineScope enum values (not strings)
        assert PipelineScope.FULL in _SCOPE_CLEAR_FUNCTIONS
        assert PipelineScope.EXTRACT in _SCOPE_CLEAR_FUNCTIONS
        assert PipelineScope.GENERATE in _SCOPE_CLEAR_FUNCTIONS
        assert PipelineScope.REVIEW in _SCOPE_CLEAR_FUNCTIONS
        assert PipelineScope.REFINE in _SCOPE_CLEAR_FUNCTIONS

    def test_execute_dispatches_to_correct_handler(self) -> None:
        """execute() が各スコープに対して正しいハンドラーを呼び出すことを確認"""
        from unittest.mock import MagicMock, patch

        from genglossary.runs.executor import PipelineExecutor, PipelineScope

        executor = PipelineExecutor()

        # Test that each scope calls the expected internal method
        for scope in PipelineScope:
            with patch.object(executor, "_execute_full") as mock_full, \
                 patch.object(executor, "_execute_extract") as mock_extract, \
                 patch.object(executor, "_execute_generate") as mock_generate, \
                 patch.object(executor, "_execute_review") as mock_review, \
                 patch.object(executor, "_execute_refine") as mock_refine, \
                 patch.object(executor, "_clear_tables_for_scope"), \
                 patch.object(executor, "_log"), \
                 patch.object(executor, "_check_cancellation", return_value=False):

                mock_conn = MagicMock()
                mock_context = MagicMock()

                executor.execute(mock_conn, scope, mock_context, doc_root="/test")

                # Verify the correct handler was called
                if scope == PipelineScope.FULL:
                    mock_full.assert_called_once()
                    mock_extract.assert_not_called()
                    mock_generate.assert_not_called()
                    mock_review.assert_not_called()
                    mock_refine.assert_not_called()
                elif scope == PipelineScope.EXTRACT:
                    mock_full.assert_not_called()
                    mock_extract.assert_called_once()
                    mock_generate.assert_not_called()
                    mock_review.assert_not_called()
                    mock_refine.assert_not_called()
                elif scope == PipelineScope.GENERATE:
                    mock_full.assert_not_called()
                    mock_extract.assert_not_called()
                    mock_generate.assert_called_once()
                    mock_review.assert_not_called()
                    mock_refine.assert_not_called()
                elif scope == PipelineScope.REVIEW:
                    mock_full.assert_not_called()
                    mock_extract.assert_not_called()
                    mock_generate.assert_not_called()
                    mock_review.assert_called_once()
                    mock_refine.assert_not_called()
                elif scope == PipelineScope.REFINE:
                    mock_full.assert_not_called()
                    mock_extract.assert_not_called()
                    mock_generate.assert_not_called()
                    mock_review.assert_not_called()
                    mock_refine.assert_called_once()


class TestCancellationCheckBeforeRefinedSave:
    """Tests for cancellation check before refined glossary is saved."""

    def test_late_cancel_still_saves_refined_when_no_issues(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """issues が空の場合、処理完了後のキャンセルでも refined が保存されることを確認

        Late-cancel race condition fix: once refinement completes, results are saved
        even if cancel arrives before the final save.
        """
        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.list_all_issues") as mock_list_issues, \
             patch("genglossary.runs.executor.create_refined_terms_batch") as mock_create_refined_batch:

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

            # No issues in DB
            mock_list_issues.return_value = []

            # Set cancel after "No issues found" log (simulate late cancel)
            original_log = executor._log

            def log_and_cancel(ctx, level, message, **kwargs):
                original_log(ctx, level, message, **kwargs)
                # Cancel after "No issues found" log
                if "No issues found" in message:
                    cancel_event.set()

            with patch.object(executor, "_log", log_and_cancel):
                # Pipeline completes successfully (no exception raised)
                # because late cancel happens after the no-check-before-save point
                executor.execute(project_db, "refine", context)

            # Refined terms batch SHOULD be saved even with late cancel
            # (late-cancel race condition fix: preserve user's work)
            mock_create_refined_batch.assert_called_once()


class TestDuplicateFilteringBeforeGenerate:
    """Tests for duplicate filtering before passing terms to generator."""

    def test_extract_saves_unique_terms_only(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """extract scopeで重複用語がユニークに保存されることを確認"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.TermExtractor") as mock_extractor, \
             patch("genglossary.runs.executor.delete_all_documents"):

            mock_llm_factory.return_value = MagicMock()
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(file_path="/test/path/test.txt", content="test content")
            ]

            # LLM returns duplicate terms
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="duplicate_term", category=TermCategory.TECHNICAL_TERM),
                ClassifiedTerm(term="duplicate_term", category=TermCategory.TECHNICAL_TERM),  # duplicate
                ClassifiedTerm(term="unique_term", category=TermCategory.TECHNICAL_TERM),
            ]

            executor.execute(project_db, "extract", execution_context, doc_root="/test/path")

            # Verify only unique terms were saved in DB
            from genglossary.db.term_repository import list_all_terms
            terms = list_all_terms(project_db)
            term_texts = [row["term_text"] for row in terms]

            # Should have 2 unique terms, not 3
            assert len(term_texts) == 2
            assert "duplicate_term" in term_texts
            assert "unique_term" in term_texts


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""

    def test_execution_context_exists(self) -> None:
        """ExecutionContext dataclass が存在することを確認"""
        from genglossary.runs.executor import ExecutionContext

        cancel_event = Event()
        log_callback = lambda msg: None

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        assert context.run_id == 1
        assert context.log_callback is log_callback
        assert context.cancel_event is cancel_event

    def test_execution_context_is_immutable(self) -> None:
        """ExecutionContext は frozen=True でイミュータブルであることを確認"""
        from genglossary.runs.executor import ExecutionContext

        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: None,
            cancel_event=Event(),
        )

        # Should raise FrozenInstanceError (subclass of AttributeError)
        with pytest.raises(AttributeError):
            context.run_id = 2  # type: ignore


class TestPipelineExecutorWithContext:
    """Tests for PipelineExecutor with ExecutionContext."""

    def test_execute_accepts_execution_context(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """execute メソッドが ExecutionContext を受け付けることを確認"""
        from genglossary.runs.executor import PipelineCancelledException

        logs: list[dict] = []
        cancel_event = Event()
        cancel_event.set()  # Cancel immediately to skip actual execution

        context = ExecutionContext(
            run_id=42,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client"):
            # Should raise PipelineCancelledException (not TypeError) when using ExecutionContext
            with pytest.raises(PipelineCancelledException):
                executor.execute(
                    project_db, "full", context, doc_root="."
                )

    def test_execute_logs_use_context_run_id(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """execute のログが context.run_id を使用することを確認"""
        logs = []
        cancel_event = Event()

        context = ExecutionContext(
            run_id=99,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "full", context)

        # All logs should have run_id=99
        assert len(logs) > 0
        assert all(log.get("run_id") == 99 for log in logs)

    def test_execute_respects_context_cancel_event(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """execute が context.cancel_event を正しく使用し、キャンセル時に例外を raise することを確認"""
        from genglossary.runs.executor import PipelineCancelledException

        logs: list[dict] = []
        cancel_event = Event()
        cancel_event.set()  # Set before execution

        context = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs.append(msg),
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client"), \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader:

            with pytest.raises(PipelineCancelledException):
                executor.execute(project_db, "full", context, doc_root="/test/path")

            # DocumentLoader should not be called when cancelled
            mock_loader.return_value.load_directory.assert_not_called()

    def test_executor_no_longer_has_instance_state_after_context(
        self,
        executor: PipelineExecutor,
    ) -> None:
        """PipelineExecutor が _run_id, _log_callback, _cancel_event を持たないことを確認

        これらの状態は ExecutionContext に移動されるべき
        """
        # After refactoring, these should not exist as instance attributes
        assert not hasattr(executor, "_run_id") or executor._run_id is None
        assert not hasattr(executor, "_log_callback") or executor._log_callback is None
        assert not hasattr(executor, "_cancel_event") or executor._cancel_event is None


class TestPipelineExecutorThreadSafety:
    """Tests for thread safety with ExecutionContext."""

    def test_same_executor_can_handle_multiple_contexts_concurrently(
        self,
        project_db_path: str,
    ) -> None:
        """同一 PipelineExecutor インスタンスで複数コンテキストを並行実行できることを確認

        各実行は独立した ExecutionContext を持ち、状態が混在しない
        """
        logs_1: list[dict] = []
        logs_2: list[dict] = []

        cancel_1 = Event()
        cancel_2 = Event()

        context_1 = ExecutionContext(
            run_id=1,
            log_callback=lambda msg: logs_1.append(msg),
            cancel_event=cancel_1,
        )

        context_2 = ExecutionContext(
            run_id=2,
            log_callback=lambda msg: logs_2.append(msg),
            cancel_event=cancel_2,
        )

        # Create shared executor
        executor = PipelineExecutor()

        def run_with_context(context: ExecutionContext, db_path: str) -> None:
            conn = get_connection(db_path)
            try:
                with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
                     patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
                     patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
                     patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
                     patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

                    mock_llm_factory.return_value = MagicMock()
                    mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
                    mock_list_terms.return_value = [{"term_text": "term1"}]
                    mock_generator.return_value.generate.return_value = Glossary(terms={})
                    mock_reviewer.return_value.review.return_value = []

                    executor.execute(conn, "full", context)
            finally:
                conn.close()

        # Run two executions concurrently with the same executor
        thread_1 = Thread(target=run_with_context, args=(context_1, project_db_path))
        thread_2 = Thread(target=run_with_context, args=(context_2, project_db_path))

        thread_1.start()
        thread_2.start()

        thread_1.join(timeout=10)
        thread_2.join(timeout=10)

        # Verify logs are separated by run_id
        assert len(logs_1) > 0, "Context 1 should have logs"
        assert len(logs_2) > 0, "Context 2 should have logs"

        # All logs in logs_1 should have run_id=1
        for log in logs_1:
            assert log.get("run_id") == 1, f"Log in logs_1 has wrong run_id: {log}"

        # All logs in logs_2 should have run_id=2
        for log in logs_2:
            assert log.get("run_id") == 2, f"Log in logs_2 has wrong run_id: {log}"


class TestCancellableDecorator:
    """Tests for _cancellable decorator."""

    def test_cancellable_decorator_checks_cancellation_at_method_entry(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        log_callback,
    ) -> None:
        """@_cancellable デコレータがメソッドエントリーでキャンセルをチェックし例外を raise する"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        cancel_event.set()  # Already cancelled

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader:

            mock_llm_factory.return_value = MagicMock()

            # _execute_full should raise PipelineCancelledException due to decorator check
            with pytest.raises(PipelineCancelledException):
                executor._execute_full(project_db, context, doc_root="/test/path")

            # DocumentLoader should NOT be called (decorator raised early)
            mock_loader.return_value.load_directory.assert_not_called()

    def test_cancellable_decorator_allows_execution_when_not_cancelled(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """キャンセルされていない場合、デコレータは実行を許可する"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Should execute normally (no exception)
            executor._execute_full(project_db, execution_context)

            # list_all_documents should be called (DB loading)
            mock_list_docs.assert_called()

    def test_cancellable_decorator_finds_context_in_positional_args(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        log_callback,
    ) -> None:
        """デコレータが位置引数からcontextを見つけ、キャンセル時に例外を raise する"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        cancel_event.set()

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            mock_llm_factory.return_value = MagicMock()

            # Call with context as positional arg - should raise
            with pytest.raises(PipelineCancelledException):
                executor._execute_generate(project_db, context)

            # Should not access DB (raised early)
            mock_list_docs.assert_not_called()


class TestDocumentFilePathStorage:
    """Tests for document file path storage.

    Documents should be stored with relative paths (from doc_root)
    instead of absolute paths for:
    - Security: Prevent server path leakage via API/logs
    - Portability: DB can be moved between environments
    - Consistency: API/schema expects file_name, not full path
    """

    def test_documents_stored_with_relative_path_not_absolute(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """ドキュメントは絶対パスではなく相対パスで保存される

        DocumentLoader は絶対パスを返すが、DB保存時に doc_root からの
        相対パスに変換される必要がある。
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            mock_llm_factory.return_value = MagicMock()

            # DB is empty (CLI mode)
            mock_list_docs.return_value = []
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # DocumentLoader returns absolute paths (simulating real behavior)
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(
                    file_path="/home/user/project/docs/chapter1/intro.md",
                    content="intro content"
                ),
                MagicMock(
                    file_path="/home/user/project/docs/chapter2/summary.md",
                    content="summary content"
                ),
            ]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with doc_root=/home/user/project/docs
            executor.execute(
                project_db, "full", execution_context,
                doc_root="/home/user/project/docs"
            )

            # Verify stored file names are relative paths, not absolute
            from genglossary.db.document_repository import list_all_documents
            docs = list_all_documents(project_db)
            file_names = [row["file_name"] for row in docs]

            # Should be relative paths from doc_root
            assert "chapter1/intro.md" in file_names
            assert "chapter2/summary.md" in file_names

            # Should NOT contain absolute paths
            for file_name in file_names:
                assert not file_name.startswith("/"), \
                    f"file_name should not be absolute path: {file_name}"

    def test_relative_path_preserves_directory_structure(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """相対パスがディレクトリ構造を保持する（同名ファイル衝突回避）"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = []
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Same basename in different directories (absolute paths)
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(
                    file_path="/project/docs/README.md",
                    content="docs readme"
                ),
                MagicMock(
                    file_path="/project/examples/README.md",
                    content="examples readme"
                ),
            ]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Execute with doc_root=/project
            executor.execute(
                project_db, "full", execution_context,
                doc_root="/project"
            )

            # Verify both files saved with distinct relative paths
            from genglossary.db.document_repository import list_all_documents
            docs = list_all_documents(project_db)
            file_names = [row["file_name"] for row in docs]

            assert len(file_names) == 2
            assert "docs/README.md" in file_names
            assert "examples/README.md" in file_names

    def test_files_outside_doc_root_raise_value_error(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """doc_root 外のファイルは ValueError で拒否される

        セキュリティ上の理由から、doc_root の外部にあるファイルは
        処理対象にしてはならない。
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = []

            # File outside doc_root (doc_root=/project/docs, file=/etc/passwd)
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(
                    file_path="/etc/passwd",
                    content="root:x:0:0:root:/root:/bin/bash"
                ),
            ]

            # Should raise ValueError for file outside doc_root
            with pytest.raises(ValueError, match="outside root directory"):
                executor.execute(
                    project_db, "full", execution_context,
                    doc_root="/project/docs"
                )

    def test_relative_path_stored_in_posix_format(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """相対パスは POSIX 形式（/）で保存される

        Windows 環境でも、DB には / を使ったパスで保存することで
        クロスプラットフォームでの互換性を確保する。
        """
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.DocumentLoader") as mock_loader, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = []
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Absolute paths (could have Windows-style separators internally)
            mock_loader.return_value.load_directory.return_value = [
                MagicMock(
                    file_path="/project/docs/subdir/file.md",
                    content="content"
                ),
            ]

            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            executor.execute(
                project_db, "full", execution_context,
                doc_root="/project/docs"
            )

            # Verify paths use forward slashes (POSIX format)
            from genglossary.db.document_repository import list_all_documents
            docs = list_all_documents(project_db)

            for row in docs:
                file_name = row["file_name"]
                assert "\\" not in file_name, \
                    f"file_name should use / not \\: {file_name}"
                # Should be: subdir/file.md
                assert file_name == "subdir/file.md"


class TestPipelineExecutorCancelEventPropagation:
    """Tests for cancel_event propagation to LLM processing classes.

    These tests verify that PipelineExecutor passes cancel_event to
    GlossaryGenerator, GlossaryReviewer, and GlossaryRefiner for
    improved cancellation responsiveness.
    """

    def test_cancel_event_passed_to_generator(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """GlossaryGenerator.generate() に cancel_event が渡されることを確認"""
        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator_cls, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]

            mock_glossary = Glossary(terms={})
            mock_generator_cls.return_value.generate.return_value = mock_glossary
            mock_reviewer.return_value.review.return_value = []

            executor.execute(project_db, "generate", context)

            # Verify cancel_event was passed to generate
            mock_generator_cls.return_value.generate.assert_called_once()
            call_kwargs = mock_generator_cls.return_value.generate.call_args.kwargs
            assert "cancel_event" in call_kwargs
            assert call_kwargs["cancel_event"] is cancel_event

    def test_cancel_event_passed_to_reviewer(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """GlossaryReviewer.review() に cancel_event が渡されることを確認"""
        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_prov.return_value = [
                {"term_name": "term1", "definition": "def1", "confidence": 0.8, "occurrences": []}
            ]

            mock_reviewer_cls.return_value.review.return_value = []

            executor.execute(project_db, "review", context)

            # Verify cancel_event was passed to review
            mock_reviewer_cls.return_value.review.assert_called_once()
            call_kwargs = mock_reviewer_cls.return_value.review.call_args.kwargs
            assert "cancel_event" in call_kwargs
            assert call_kwargs["cancel_event"] is cancel_event

    def test_cancel_event_passed_to_refiner(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """GlossaryRefiner.refine() に cancel_event が渡されることを確認"""
        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.list_all_issues") as mock_list_issues, \
             patch("genglossary.runs.executor.GlossaryRefiner") as mock_refiner_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_prov.return_value = [
                {"term_name": "term1", "definition": "def1", "confidence": 0.8, "occurrences": []}
            ]

            # Return issues from DB to trigger refiner
            mock_list_issues.return_value = [
                {"term_name": "term1", "issue_type": "unclear", "description": "Issue", "should_exclude": 0, "exclusion_reason": None}
            ]

            mock_refiner_cls.return_value.refine.return_value = Glossary(terms={})

            executor.execute(project_db, "refine", context)

            # Verify cancel_event was passed to refine
            mock_refiner_cls.return_value.refine.assert_called_once()
            call_kwargs = mock_refiner_cls.return_value.refine.call_args.kwargs
            assert "cancel_event" in call_kwargs
            assert call_kwargs["cancel_event"] is cancel_event

    def test_provisional_glossary_saved_even_with_late_cancel(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """generate() が完了した後のキャンセルでも provisional が保存されることを確認

        Late-cancel race condition fix: once generation completes (returns a value),
        results are saved even if cancel arrives before the save.
        """
        from genglossary.runs.executor import PipelineCancelledException

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator_cls, \
             patch("genglossary.runs.executor.create_provisional_terms_batch") as mock_create_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer_cls:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "test.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]

            # Simulate late cancel: generate completes, then cancel is set
            def generate_with_late_cancel(*_args, **_kwargs):
                cancel_event.set()  # Cancel arrives after generate completes
                return Glossary(terms={"term1": Term(
                    name="term1",
                    definition="test",
                    confidence=0.9,
                    occurrences=[TermOccurrence(document_path="test.txt", line_number=1, context="ctx")]
                )})

            mock_generator_cls.return_value.generate.side_effect = generate_with_late_cancel

            # Generate scope completes normally (no reviewer call)
            executor.execute(project_db, "generate", context)

            # Provisional terms SHOULD be saved (late-cancel fix)
            mock_create_prov.assert_called_once()

    def test_issues_not_saved_when_review_cancelled(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        cancel_event: Event,
        log_callback,
    ) -> None:
        """review() がキャンセルでNoneを返した場合、issues が保存されずに例外が raise される"""
        from genglossary.runs.executor import PipelineCancelledException

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_provisional") as mock_list_prov, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer_cls, \
             patch("genglossary.runs.executor.create_issues_batch") as mock_create_issues:

            mock_llm_factory.return_value = MagicMock()
            mock_list_prov.return_value = [
                {"term_name": "term1", "definition": "def1", "confidence": 0.8, "occurrences": []}
            ]

            # Reviewer returns None (cancelled)
            mock_reviewer_cls.return_value.review.return_value = None

            with pytest.raises(PipelineCancelledException):
                executor.execute(project_db, "review", context)

            # Issues should NOT be saved when review was cancelled
            mock_create_issues.assert_not_called()


class TestExecuteCompletionBehavior:
    """Tests for execute() completion and cancellation behavior."""

    def test_execute_completes_normally_without_exception(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """execute が正常完了時に例外を raise しないことを確認"""
        cancel_event = Event()
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda _: None,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.GlossaryGenerator") as mock_generator, \
             patch("genglossary.runs.executor.GlossaryReviewer") as mock_reviewer, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:

            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.return_value = [{"file_name": "doc.txt", "content": "test"}]
            mock_list_terms.return_value = [{"term_text": "term1"}]
            mock_generator.return_value.generate.return_value = Glossary(terms={})
            mock_reviewer.return_value.review.return_value = []

            # Should complete without raising any exception
            executor.execute(project_db, "full", context)

    def test_execute_raises_exception_when_cancelled_before_start(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """execute が開始前にキャンセルされた場合に PipelineCancelledException を raise することを確認"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        cancel_event.set()  # Set before execution
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda _: None,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client"), \
             patch("genglossary.runs.executor.DocumentLoader"):

            with pytest.raises(PipelineCancelledException):
                executor.execute(project_db, "full", context, doc_root="/test")

    def test_execute_raises_exception_when_cancelled_after_document_load(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
    ) -> None:
        """execute がドキュメント読み込み後にキャンセルされた場合に PipelineCancelledException を raise することを確認"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        context = ExecutionContext(
            run_id=1,
            log_callback=lambda _: None,
            cancel_event=cancel_event,
        )

        def set_cancel_and_return_docs(*_args, **_kwargs):
            cancel_event.set()
            return [{"file_name": "doc.txt", "content": "test"}]

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:
            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.side_effect = set_cancel_and_return_docs
            mock_list_terms.return_value = [{"term_text": "term1"}]

            with pytest.raises(PipelineCancelledException):
                executor.execute(project_db, "full", context)


class TestPipelineCancelledException:
    """Tests for PipelineCancelledException class and cancellation via exception."""

    def test_pipeline_cancelled_exception_class_exists(self) -> None:
        """PipelineCancelledException クラスが存在し、Exception を継承している"""
        from genglossary.runs.executor import PipelineCancelledException

        assert issubclass(PipelineCancelledException, Exception)

    def test_pipeline_cancelled_exception_can_be_raised(self) -> None:
        """PipelineCancelledException が正常に raise できる"""
        from genglossary.runs.executor import PipelineCancelledException

        with pytest.raises(PipelineCancelledException):
            raise PipelineCancelledException()

    def test_execute_raises_exception_when_cancelled_before_start(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        log_callback,
    ) -> None:
        """キャンセル状態で execute を呼び出すと PipelineCancelledException が発生する"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        cancel_event.set()  # Set before execution

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with pytest.raises(PipelineCancelledException):
            executor.execute(project_db, "full", context)

    def test_execute_raises_exception_when_cancelled_during_execution(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        log_callback,
    ) -> None:
        """実行中にキャンセルされると PipelineCancelledException が発生する"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        def set_cancel_and_return_docs(*_args, **_kwargs):
            cancel_event.set()
            return [{"file_name": "doc.txt", "content": "test"}]

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory, \
             patch("genglossary.runs.executor.list_all_documents") as mock_list_docs, \
             patch("genglossary.runs.executor.list_all_terms") as mock_list_terms:
            mock_llm_factory.return_value = MagicMock()
            mock_list_docs.side_effect = set_cancel_and_return_docs
            mock_list_terms.return_value = [{"term_text": "term1"}]

            with pytest.raises(PipelineCancelledException):
                executor.execute(project_db, "full", context)

    def test_check_cancellation_raises_exception(
        self,
        executor: PipelineExecutor,
        log_callback,
    ) -> None:
        """_check_cancellation がキャンセル時に例外を raise する"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        cancel_event.set()

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with pytest.raises(PipelineCancelledException):
            executor._check_cancellation(context)

    def test_cancellable_decorator_raises_exception(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        log_callback,
    ) -> None:
        """@_cancellable デコレータがキャンセル時に例外を raise する"""
        from genglossary.runs.executor import PipelineCancelledException

        cancel_event = Event()
        cancel_event.set()

        context = ExecutionContext(
            run_id=1,
            log_callback=log_callback,
            cancel_event=cancel_event,
        )

        with patch("genglossary.runs.executor.create_llm_client"):
            with pytest.raises(PipelineCancelledException):
                executor._execute_full(project_db, context, doc_root="/test/path")


class TestDoExtractExcludedTermRepo:
    """Tests for _do_extract passing excluded_term_repo to TermExtractor."""

    def test_do_extract_passes_conn_as_excluded_term_repo(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """_do_extract は TermExtractor に conn を excluded_term_repo として渡す"""
        from genglossary.models.document import Document

        # Create a test document
        documents = [Document(file_path="/test/doc.txt", content="テスト文書です。量子コンピュータを使用します。")]

        with patch("genglossary.runs.executor.TermExtractor") as mock_extractor_class:
            mock_extractor = MagicMock()
            mock_extractor.extract_terms.return_value = []
            mock_extractor_class.return_value = mock_extractor

            with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory:
                mock_llm_client = MagicMock()
                mock_llm_factory.return_value = mock_llm_client

                # Set up LLM client on executor
                executor._llm_client = mock_llm_client

                # Call _do_extract
                executor._do_extract(project_db, execution_context, documents)

                # Verify TermExtractor was instantiated with excluded_term_repo=conn
                mock_extractor_class.assert_called_once()
                call_kwargs = mock_extractor_class.call_args.kwargs
                assert "excluded_term_repo" in call_kwargs
                assert call_kwargs["excluded_term_repo"] is project_db


class TestPipelineExecutorBaseUrl:
    """Tests for base_url parameter propagation to LLM client."""

    def test_executor_passes_base_url_to_create_llm_client(self) -> None:
        """PipelineExecutorがbase_urlをcreate_llm_clientに渡すことを確認"""
        custom_url = "http://192.168.1.100:11434"

        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory:
            mock_llm_factory.return_value = MagicMock()

            PipelineExecutor(provider="ollama", model="test-model", base_url=custom_url)

            mock_llm_factory.assert_called_once()
            call_kwargs = mock_llm_factory.call_args.kwargs
            assert call_kwargs.get("base_url") == custom_url

    def test_executor_passes_none_base_url_when_not_provided(self) -> None:
        """PipelineExecutorがbase_urlを指定しない場合、Noneが渡されることを確認"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_llm_factory:
            mock_llm_factory.return_value = MagicMock()

            PipelineExecutor(provider="ollama", model="test-model")

            mock_llm_factory.assert_called_once()
            call_kwargs = mock_llm_factory.call_args.kwargs
            # base_url should not be in kwargs or should be None
            assert call_kwargs.get("base_url") is None


class TestExtractPreservesUserNotes:
    """Test that extract scope preserves user_notes."""

    def test_extract_scope_preserves_user_notes(
        self,
        executor: PipelineExecutor,
        project_db: sqlite3.Connection,
        execution_context: ExecutionContext,
    ) -> None:
        """Test that re-extract preserves existing user_notes."""
        from genglossary.db.connection import transaction
        from genglossary.db.term_repository import (
            create_term,
            get_term,
            list_all_terms,
            update_term,
        )

        # Setup: create terms with user_notes
        with transaction(project_db):
            term_id = create_term(project_db, "GP", "abbreviation")
            update_term(
                project_db, term_id, "GP", "abbreviation",
                user_notes="General Practitioner",
            )
            create_term(project_db, "量子ビット", "technical")

        # Add a document to DB so extract can find it
        with transaction(project_db):
            project_db.execute(
                "INSERT INTO documents (file_name, content, content_hash) VALUES (?, ?, ?)",
                ("test.md", "GPは医師です。量子ビットは基本単位。", "hash123"),
            )

        # Mock TermExtractor to return terms including GP
        with patch("genglossary.runs.executor.TermExtractor") as mock_extractor:
            mock_extractor.return_value.extract_terms.return_value = [
                ClassifiedTerm(term="GP", category=TermCategory.TECHNICAL_TERM),
                ClassifiedTerm(term="新用語", category=TermCategory.TECHNICAL_TERM),
            ]

            executor.execute(project_db, "extract", execution_context)

        # Verify user_notes preserved for GP
        terms = list_all_terms(project_db)
        term_map = {t["term_text"]: t["user_notes"] for t in terms}
        assert term_map.get("GP") == "General Practitioner"
        # New term should have empty notes
        assert term_map.get("新用語") == ""
