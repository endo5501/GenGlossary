"""Tests for PipelineExecutor LLM debug integration."""

from pathlib import Path
from unittest.mock import patch

import pytest

from genglossary.runs.executor import PipelineExecutor


class TestPipelineExecutorLlmDebug:
    """Tests for PipelineExecutor debug logging parameters."""

    def test_executor_accepts_llm_debug_params(self) -> None:
        """PipelineExecutorがllm_debugとdebug_dirパラメータを受け付ける"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_factory:
            PipelineExecutor(
                provider="ollama",
                model="test",
                llm_debug=True,
                debug_dir="/tmp/test-debug",
            )
            mock_factory.assert_called_once()
            call_kwargs = mock_factory.call_args.kwargs
            assert call_kwargs["llm_debug"] is True
            assert call_kwargs["debug_dir"] == "/tmp/test-debug"

    def test_executor_passes_llm_debug_false_by_default(self) -> None:
        """PipelineExecutorがデフォルトでllm_debug=Falseを渡す"""
        with patch("genglossary.runs.executor.create_llm_client") as mock_factory:
            PipelineExecutor(provider="ollama", model="test")
            call_kwargs = mock_factory.call_args.kwargs
            assert call_kwargs.get("llm_debug", False) is False
