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
        if not text:
            return {
                "characters": 0,
                "words": 0,
                "lines": 0,
                "estimated_tokens": 0,
            }

        characters = len(text)
        words = len(text.split())
        lines = len(text.splitlines()) if text else 0
        # Rough estimation: ~4 characters per token for English text
        estimated_tokens = characters // 4

        return {
            "characters": characters,
            "words": words,
            "lines": lines,
            "estimated_tokens": estimated_tokens,
        }
