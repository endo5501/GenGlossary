"""Tests for RunManager LLM debug integration."""

from pathlib import Path
from threading import Event
from unittest.mock import MagicMock, patch

import pytest

from genglossary.runs.manager import RunManager


def _prepare_manager(manager: RunManager, run_id: int) -> None:
    """Set up cancel event for a run (normally done in start_run)."""
    manager._cancel_events[run_id] = Event()


class TestRunManagerLlmDebug:
    """Tests for RunManager passing debug settings to PipelineExecutor."""

    def test_executor_created_with_debug_when_config_enabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config.llm_debug=Trueの場合、PipelineExecutorにデバッグ設定が渡される"""
        monkeypatch.setenv("LLM_DEBUG", "true")

        db_path = str(tmp_path / "test.db")
        manager = RunManager(
            db_path=db_path,
            doc_root=str(tmp_path),
            llm_provider="ollama",
            llm_model="test-model",
        )
        _prepare_manager(manager, 1)

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor, \
             patch("genglossary.runs.manager.get_connection"), \
             patch("genglossary.runs.manager.transaction"), \
             patch("genglossary.runs.manager.update_run_status"):
            mock_exec_instance = MagicMock()
            mock_executor.return_value = mock_exec_instance

            manager._execute_run(run_id=1, scope="full")

            mock_executor.assert_called_once()
            call_kwargs = mock_executor.call_args.kwargs
            assert call_kwargs["llm_debug"] is True
            assert "llm-debug" in call_kwargs["debug_dir"]

    def test_executor_created_without_debug_when_config_disabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config.llm_debug=Falseの場合、デバッグ設定が無効"""
        monkeypatch.setenv("LLM_DEBUG", "false")

        db_path = str(tmp_path / "test.db")
        manager = RunManager(
            db_path=db_path,
            doc_root=str(tmp_path),
            llm_provider="ollama",
            llm_model="test-model",
        )
        _prepare_manager(manager, 1)

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor, \
             patch("genglossary.runs.manager.get_connection"), \
             patch("genglossary.runs.manager.transaction"), \
             patch("genglossary.runs.manager.update_run_status"):
            mock_exec_instance = MagicMock()
            mock_executor.return_value = mock_exec_instance

            manager._execute_run(run_id=1, scope="full")

            mock_executor.assert_called_once()
            call_kwargs = mock_executor.call_args.kwargs
            assert call_kwargs["llm_debug"] is False

    def test_debug_dir_is_under_db_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """デバッグディレクトリがdb_pathの親ディレクトリ/llm-debug/に設定される"""
        monkeypatch.setenv("LLM_DEBUG", "true")

        db_path = str(tmp_path / "projects" / "test.db")
        manager = RunManager(
            db_path=db_path,
            doc_root=str(tmp_path),
            llm_provider="ollama",
            llm_model="test-model",
        )
        _prepare_manager(manager, 1)

        with patch("genglossary.runs.manager.PipelineExecutor") as mock_executor, \
             patch("genglossary.runs.manager.get_connection"), \
             patch("genglossary.runs.manager.transaction"), \
             patch("genglossary.runs.manager.update_run_status"):
            mock_exec_instance = MagicMock()
            mock_executor.return_value = mock_exec_instance

            manager._execute_run(run_id=1, scope="full")

            call_kwargs = mock_executor.call_args.kwargs
            expected_dir = str(tmp_path / "projects" / "llm-debug")
            assert call_kwargs["debug_dir"] == expected_dir
