"""Tests for CLI --llm-debug option."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from genglossary.cli_api import serve


class TestServeCommandLlmDebugOption:
    """Tests for 'api serve --llm-debug' option."""

    def test_serve_accepts_llm_debug_flag(self) -> None:
        """serve コマンドが --llm-debug フラグを受け付ける"""
        runner = CliRunner()
        with patch("genglossary.cli_api.uvicorn") as mock_uvicorn, \
             patch.dict("os.environ", {}, clear=False):
            mock_uvicorn.run = MagicMock()
            result = runner.invoke(serve, ["--llm-debug"])
            # Should not fail due to unrecognized option
            assert result.exit_code == 0

    def test_serve_sets_llm_debug_env_when_flag_provided(self) -> None:
        """--llm-debug フラグ指定時に LLM_DEBUG 環境変数が設定される"""
        runner = CliRunner()
        with patch("genglossary.cli_api.uvicorn") as mock_uvicorn, \
             patch.dict("os.environ", {}, clear=False) as mock_env:
            mock_uvicorn.run = MagicMock()
            result = runner.invoke(serve, ["--llm-debug"])
            assert result.exit_code == 0
            import os
            assert os.environ.get("LLM_DEBUG") == "true"

    def test_serve_does_not_set_llm_debug_env_without_flag(self) -> None:
        """--llm-debug フラグなしの場合、LLM_DEBUG 環境変数は設定されない"""
        runner = CliRunner()
        with patch("genglossary.cli_api.uvicorn") as mock_uvicorn, \
             patch.dict("os.environ", {"LLM_DEBUG": ""}, clear=False):
            mock_uvicorn.run = MagicMock()
            result = runner.invoke(serve, [])
            assert result.exit_code == 0
            import os
            assert os.environ.get("LLM_DEBUG") != "true"
