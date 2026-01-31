"""Callback utility functions."""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def safe_callback(callback: Callable[..., None] | None, *args: Any) -> None:
    """Safely invoke a callback, ignoring any exceptions.

    This prevents callback errors from interrupting the pipeline.
    Errors are logged at DEBUG level for debugging purposes.

    Args:
        callback: The callback function to invoke, or None.
        *args: Arguments to pass to the callback.
    """
    if callback is not None:
        try:
            callback(*args)
        except Exception as e:
            logger.debug(
                "Callback error ignored (to prevent pipeline interruption): %s",
                e,
                exc_info=True,
            )
