"""Token counter utility for measuring prompt sizes."""


class TokenCounter:
    """Count tokens and other text metrics."""

    def count(self, text: str) -> dict[str, int]:
        """Count various text metrics.

        Args:
            text: Text to analyze

        Returns:
            Dictionary containing:
            - characters: Number of characters
            - words: Number of words
            - lines: Number of lines
            - estimated_tokens: Estimated token count
        """
        # Stub implementation - will fail tests
        return {}
