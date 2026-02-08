"""Tests for LLM debug logging integration with BaseLLMClient and factory."""

from pathlib import Path
from typing import Type
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.llm.debug_logger import LlmDebugLogger


class SampleResponse(BaseModel):
    """Sample response model for testing."""

    text: str


class StubLLMClient(BaseLLMClient):
    """Stub LLM client for testing debug integration."""

    def __init__(self) -> None:
        self.model = "stub-model"

    def generate(self, prompt: str) -> str:
        return "stub response"

    def generate_structured(
        self, prompt: str, response_model: Type[BaseModel]
    ) -> BaseModel:
        return response_model(text="stub")

    def is_available(self) -> bool:
        return True


class TestBaseLLMClientDebugLogger:
    """Tests for debug logger attribute on BaseLLMClient."""

    def test_debug_logger_defaults_to_none(self) -> None:
        """_debug_loggerのデフォルト値はNone"""
        client = StubLLMClient()
        assert client._debug_logger is None

    def test_debug_logger_can_be_set(self, tmp_path: Path) -> None:
        """_debug_loggerを設定できる"""
        client = StubLLMClient()
        logger = LlmDebugLogger(debug_dir=str(tmp_path / "llm-debug"))
        client._debug_logger = logger
        assert client._debug_logger is logger


class TestGenerateWithDebugLogging:
    """Tests for generate() with debug logging."""

    def test_generate_writes_debug_log(self, tmp_path: Path) -> None:
        """generate()呼び出し時にデバッグログファイルが作成される"""
        debug_dir = tmp_path / "llm-debug"
        client = StubLLMClient()
        client._debug_logger = LlmDebugLogger(debug_dir=str(debug_dir))

        result = client.generate("test prompt")

        assert result == "stub response"
        files = list(debug_dir.iterdir())
        assert len(files) == 1

    def test_generate_debug_log_contains_prompt_and_response(
        self, tmp_path: Path
    ) -> None:
        """generate()のデバッグログにプロンプトとレスポンスが含まれる"""
        debug_dir = tmp_path / "llm-debug"
        client = StubLLMClient()
        client._debug_logger = LlmDebugLogger(debug_dir=str(debug_dir))

        client.generate("my test prompt")

        files = list(debug_dir.iterdir())
        content = files[0].read_text(encoding="utf-8")
        assert "my test prompt" in content
        assert "stub response" in content

    def test_generate_debug_log_contains_model_name(self, tmp_path: Path) -> None:
        """generate()のデバッグログにモデル名が含まれる"""
        debug_dir = tmp_path / "llm-debug"
        client = StubLLMClient()
        client._debug_logger = LlmDebugLogger(debug_dir=str(debug_dir))

        client.generate("test")

        files = list(debug_dir.iterdir())
        content = files[0].read_text(encoding="utf-8")
        assert "# Model: stub-model" in content
        assert "# Method: generate" in content

    def test_generate_without_debug_logger_no_files(self, tmp_path: Path) -> None:
        """_debug_logger未設定時はファイルが作成されない"""
        client = StubLLMClient()
        result = client.generate("test prompt")
        assert result == "stub response"
        # No debug directory should exist
        assert not (tmp_path / "llm-debug").exists()


class TestGenerateStructuredWithDebugLogging:
    """Tests for generate_structured() with debug logging via _retry_json_parsing."""

    def test_generate_structured_writes_debug_log(self, tmp_path: Path) -> None:
        """generate_structured()呼び出し時にデバッグログが作成される"""
        debug_dir = tmp_path / "llm-debug"
        client = StubLLMClient()
        client._debug_logger = LlmDebugLogger(debug_dir=str(debug_dir))

        result = client.generate_structured("test prompt", SampleResponse)

        assert result.text == "stub"
        files = list(debug_dir.iterdir())
        assert len(files) >= 1


class TestFactoryDebugIntegration:
    """Tests for create_llm_client with debug settings."""

    def test_factory_sets_debug_logger_when_enabled(self, tmp_path: Path) -> None:
        """llm_debug=Trueの場合、ファクトリがdebug_loggerを設定する"""
        from genglossary.llm.factory import create_llm_client

        with patch("genglossary.llm.factory.OllamaClient") as mock_ollama:
            mock_ollama.return_value = StubLLMClient()

            client = create_llm_client(
                provider="ollama",
                llm_debug=True,
                debug_dir=str(tmp_path / "llm-debug"),
            )

            assert client._debug_logger is not None

    def test_factory_no_debug_logger_when_disabled(self) -> None:
        """llm_debug=Falseの場合、debug_loggerが設定されない"""
        from genglossary.llm.factory import create_llm_client

        with patch("genglossary.llm.factory.OllamaClient") as mock_ollama:
            mock_ollama.return_value = StubLLMClient()

            client = create_llm_client(provider="ollama", llm_debug=False)

            assert client._debug_logger is None

    def test_factory_no_debug_logger_by_default(self) -> None:
        """デフォルトではdebug_loggerが設定されない"""
        from genglossary.llm.factory import create_llm_client

        with patch("genglossary.llm.factory.OllamaClient") as mock_ollama:
            mock_ollama.return_value = StubLLMClient()

            client = create_llm_client(provider="ollama")

            assert client._debug_logger is None

    def test_factory_raises_when_debug_enabled_without_dir(self) -> None:
        """llm_debug=Trueでdebug_dir未指定の場合、ValueErrorが発生する"""
        from genglossary.llm.factory import create_llm_client

        with patch("genglossary.llm.factory.OllamaClient") as mock_ollama:
            mock_ollama.return_value = StubLLMClient()

            with pytest.raises(ValueError, match="debug_dir"):
                create_llm_client(provider="ollama", llm_debug=True)


class TestDebugLoggingBestEffort:
    """Tests for best-effort debug logging (errors don't break LLM calls)."""

    def test_generate_returns_result_when_logging_fails(
        self, tmp_path: Path
    ) -> None:
        """ロギングが失敗してもgenerate()は結果を返す"""
        client = StubLLMClient()
        logger = LlmDebugLogger(debug_dir=str(tmp_path / "llm-debug"))
        client._debug_logger = logger
        # Make log method raise an exception
        logger.log = lambda **kwargs: (_ for _ in ()).throw(OSError("disk full"))  # type: ignore[assignment]

        result = client.generate("test prompt")

        assert result == "stub response"

    def test_generate_structured_returns_result_when_logging_fails(
        self, tmp_path: Path
    ) -> None:
        """ロギングが失敗してもgenerate_structured()は結果を返す"""
        client = StubLLMClient()
        logger = LlmDebugLogger(debug_dir=str(tmp_path / "llm-debug"))
        client._debug_logger = logger
        # Make log method raise an exception
        logger.log = lambda **kwargs: (_ for _ in ()).throw(OSError("disk full"))  # type: ignore[assignment]

        result = client.generate_structured("test prompt", SampleResponse)

        assert result.text == "stub"
