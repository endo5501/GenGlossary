"""Progress bar utilities for CLI."""

from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from genglossary.types import ProgressCallback


def create_standard_progress(console: Console) -> Progress:
    """Create a standard progress bar with spinner, bar, task progress, and time.

    Args:
        console: Rich console for output.

    Returns:
        Configured Progress object with standard columns.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )


def create_spinner_progress(console: Console) -> Progress:
    """Create a spinner-only progress bar with description and time.

    Args:
        console: Rich console for output.

    Returns:
        Configured Progress object with spinner columns only.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    )


@contextmanager
def progress_task(
    console: Console,
    description: str,
    total: int | None = None,
    use_spinner_only: bool = False,
) -> Generator[ProgressCallback, None, None]:
    """Context manager for running a task with a progress bar.

    Yields a callback function that accepts (current, total) to update progress.
    The callback automatically updates the total if it was initially None.

    Usage:
        with progress_task(console, "Processing...", total=100) as update:
            for i in range(100):
                do_work()
                update(i + 1, 100)

    Args:
        console: Rich console for output.
        description: Task description to display.
        total: Total number of items (None for indeterminate progress).
        use_spinner_only: If True, use spinner-only progress without bar.

    Yields:
        ProgressCallback function that accepts (current, total) arguments.
    """
    progress_factory = create_spinner_progress if use_spinner_only else create_standard_progress

    with progress_factory(console) as progress:
        task: TaskID = progress.add_task(description, total=total)

        def update_callback(current: int, new_total: int) -> None:
            """Update progress with current position and optionally update total."""
            # Update total on first call if not set
            if progress.tasks[task].total is None:
                progress.update(task, total=new_total)
            progress.update(task, completed=current)

        yield update_callback
