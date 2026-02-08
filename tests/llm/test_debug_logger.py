"""Tests for LLM debug logger."""

import os
from pathlib import Path

import pytest

from genglossary.llm.debug_logger import LlmDebugLogger


class TestLlmDebugLoggerInit:
    """Tests for LlmDebugLogger initialization."""

    def test_creates_debug_dir_on_init(self, tmp_path: Path) -> None:
        """デバッグディレクトリが初期化時に作成される"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))
        assert debug_dir.exists()

    def test_counter_starts_at_one(self, tmp_path: Path) -> None:
        """連番カウンターは1から始まる"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))
        assert logger.counter == 1

    def test_reset_counter(self, tmp_path: Path) -> None:
        """reset_counter()で連番が1に戻る"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))
        logger.counter = 5
        logger.reset_counter()
        assert logger.counter == 1


class TestLlmDebugLoggerLog:
    """Tests for LlmDebugLogger.log() method."""

    def test_log_creates_file(self, tmp_path: Path) -> None:
        """log()がファイルを作成する"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))

        logger.log(
            model="test-model",
            method="generate",
            request="test prompt",
            response="test response",
            duration=1.5,
        )

        files = list(debug_dir.iterdir())
        assert len(files) == 1

    def test_log_file_name_format(self, tmp_path: Path) -> None:
        """ファイル名が YYYYMMDD-HHmmss-NNNN.txt 形式"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))

        logger.log(
            model="test-model",
            method="generate",
            request="test prompt",
            response="test response",
            duration=1.0,
        )

        files = list(debug_dir.iterdir())
        filename = files[0].name
        # Format: YYYYMMDD-HHmmss-NNNN.txt
        assert filename.endswith(".txt")
        parts = filename.replace(".txt", "").split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHmmss
        assert len(parts[2]) == 4  # NNNN

    def test_log_file_contains_header(self, tmp_path: Path) -> None:
        """ファイルにメタ情報ヘッダが含まれる"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))

        logger.log(
            model="test-model",
            method="generate_structured",
            request="test prompt",
            response="test response",
            duration=2.5,
        )

        files = list(debug_dir.iterdir())
        content = files[0].read_text(encoding="utf-8")
        assert "# Model: test-model" in content
        assert "# Method: generate_structured" in content
        assert "# Duration: 2.5s" in content
        assert "# Timestamp:" in content

    def test_log_file_contains_request_and_response(self, tmp_path: Path) -> None:
        """ファイルにリクエストとレスポンスが含まれる"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))

        logger.log(
            model="test-model",
            method="generate",
            request="my prompt text",
            response="my response text",
            duration=1.0,
        )

        files = list(debug_dir.iterdir())
        content = files[0].read_text(encoding="utf-8")
        assert "## REQUEST" in content
        assert "my prompt text" in content
        assert "## RESPONSE" in content
        assert "my response text" in content

    def test_counter_increments_after_log(self, tmp_path: Path) -> None:
        """log()呼び出し後に連番がインクリメントされる"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))

        logger.log(
            model="m", method="generate", request="r", response="resp", duration=1.0
        )
        assert logger.counter == 2

        logger.log(
            model="m", method="generate", request="r", response="resp", duration=1.0
        )
        assert logger.counter == 3

    def test_multiple_logs_create_separate_files(self, tmp_path: Path) -> None:
        """複数回のlog()呼び出しが別ファイルを生成する"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))

        for i in range(3):
            logger.log(
                model="m",
                method="generate",
                request=f"prompt {i}",
                response=f"response {i}",
                duration=1.0,
            )

        files = list(debug_dir.iterdir())
        assert len(files) == 3

    def test_counter_in_filename_is_zero_padded(self, tmp_path: Path) -> None:
        """ファイル名の連番が4桁ゼロ埋め"""
        debug_dir = tmp_path / "llm-debug"
        logger = LlmDebugLogger(debug_dir=str(debug_dir))

        logger.log(
            model="m", method="generate", request="r", response="resp", duration=1.0
        )

        files = list(debug_dir.iterdir())
        filename = files[0].name
        counter_part = filename.replace(".txt", "").split("-")[2]
        assert counter_part == "0001"


class TestLlmDebugLoggerDisabled:
    """Tests for disabled debug logger (None)."""

    def test_no_op_when_debug_dir_is_none(self) -> None:
        """debug_dir=Noneの場合、log()は何もしない"""
        logger = LlmDebugLogger(debug_dir=None)
        # Should not raise any error
        logger.log(
            model="m", method="generate", request="r", response="resp", duration=1.0
        )

    def test_no_files_created_when_disabled(self, tmp_path: Path) -> None:
        """無効化時にファイルが作成されない"""
        logger = LlmDebugLogger(debug_dir=None)
        logger.log(
            model="m", method="generate", request="r", response="resp", duration=1.0
        )
        # No files should exist anywhere related to debug
        assert not (tmp_path / "llm-debug").exists()
