"""LLM debug logger for recording prompts and responses to files."""

from datetime import datetime
from pathlib import Path


class LlmDebugLogger:
    """Logs LLM request/response pairs to debug files.

    When debug_dir is None, all operations are no-ops.
    """

    def __init__(self, debug_dir: str | None) -> None:
        self._debug_dir = debug_dir
        self.counter = 1

        if debug_dir is not None:
            Path(debug_dir).mkdir(parents=True, exist_ok=True)

    def reset_counter(self) -> None:
        """Reset the sequential counter to 1."""
        self.counter = 1

    def log(
        self,
        *,
        model: str,
        method: str,
        request: str,
        response: str,
        duration: float,
    ) -> None:
        """Write a debug log file with request and response.

        Args:
            model: LLM model name.
            method: Method name (generate or generate_structured).
            request: Prompt text sent to the LLM.
            response: Response text received from the LLM.
            duration: Duration in seconds.
        """
        if self._debug_dir is None:
            return

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        counter_str = f"{self.counter:04d}"

        filename = f"{date_part}-{time_part}-{counter_str}.txt"
        filepath = Path(self._debug_dir) / filename

        content = (
            f"# Timestamp: {timestamp}\n"
            f"# Model: {model}\n"
            f"# Method: {method}\n"
            f"# Duration: {duration}s\n"
            f"\n"
            f"## REQUEST\n"
            f"{request}\n"
            f"\n"
            f"## RESPONSE\n"
            f"{response}\n"
        )

        filepath.write_text(content, encoding="utf-8")
        self.counter += 1
