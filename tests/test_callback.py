"""Tests for safe_callback utility function."""

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from genglossary.utils.callback import safe_callback


class TestSafeCallback:
    """Tests for safe_callback function."""

    def test_invokes_callback_with_args(self) -> None:
        """Test that callback is invoked with correct arguments."""
        mock_callback = MagicMock()

        safe_callback(mock_callback, 1, 2, "test")

        mock_callback.assert_called_once_with(1, 2, "test")

    def test_none_callback_does_nothing(self) -> None:
        """Test that None callback is safely handled without exception."""
        # Should not raise any exception
        safe_callback(None, 1, 2, 3)

    def test_callback_exception_is_ignored(self) -> None:
        """Test that exceptions from callback are caught and ignored."""
        mock_callback = MagicMock(side_effect=ValueError("test error"))

        # Should not raise any exception
        safe_callback(mock_callback, "arg1")

        mock_callback.assert_called_once_with("arg1")

    def test_callback_runtime_error_is_ignored(self) -> None:
        """Test that RuntimeError from callback is caught and ignored."""
        mock_callback = MagicMock(side_effect=RuntimeError("runtime error"))

        # Should not raise any exception
        safe_callback(mock_callback)

        mock_callback.assert_called_once_with()

    def test_callback_with_no_args(self) -> None:
        """Test callback invocation without arguments."""
        mock_callback = MagicMock()

        safe_callback(mock_callback)

        mock_callback.assert_called_once_with()

    def test_callback_with_kwargs_style_args(self) -> None:
        """Test callback invocation with complex argument types."""
        mock_callback = MagicMock()
        data = {"key": "value"}
        items = [1, 2, 3]

        safe_callback(mock_callback, data, items)

        mock_callback.assert_called_once_with(data, items)

    def test_logs_debug_when_callback_raises(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that safe_callback logs debug when callback raises an exception."""

        def failing_callback(*args: Any) -> None:
            raise RuntimeError("Callback exploded")

        with caplog.at_level(logging.DEBUG):
            safe_callback(failing_callback, 1, 2, 3)

        # Should have logged a debug message
        assert len(caplog.records) >= 1
        debug_record = caplog.records[0]
        assert debug_record.levelno == logging.DEBUG
        assert "Callback exploded" in debug_record.message
        assert "callback" in debug_record.name

    def test_logs_debug_with_exc_info(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that safe_callback logs with exc_info for full traceback."""

        def failing_callback(*args: Any) -> None:
            raise ValueError("Test error with traceback")

        with caplog.at_level(logging.DEBUG):
            safe_callback(failing_callback, "arg1")

        # Should have logged with exc_info (traceback available)
        assert len(caplog.records) >= 1
        debug_record = caplog.records[0]
        assert debug_record.exc_info is not None
        assert debug_record.exc_info[0] is ValueError
