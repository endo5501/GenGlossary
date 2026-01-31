"""Tests for safe_callback utility function."""

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
