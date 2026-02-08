"""Tests for Config.llm_debug field."""

import pytest

from genglossary.config import Config


class TestConfigLlmDebug:
    """Tests for llm_debug configuration field."""

    def test_llm_debug_defaults_to_false(self) -> None:
        """llm_debugのデフォルト値はFalse"""
        config = Config()
        assert config.llm_debug is False

    def test_llm_debug_from_env_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """環境変数LLM_DEBUG=trueで有効化"""
        monkeypatch.setenv("LLM_DEBUG", "true")
        config = Config()
        assert config.llm_debug is True

    def test_llm_debug_from_env_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """環境変数LLM_DEBUG=falseで無効"""
        monkeypatch.setenv("LLM_DEBUG", "false")
        config = Config()
        assert config.llm_debug is False
