"""Morphological analyzer using SudachiPy for proper noun extraction."""

from sudachipy import Dictionary, SplitMode


class MorphologicalAnalyzer:
    """Analyzes Japanese text to extract proper nouns using SudachiPy.

    Uses SudachiPy with split mode C (long unit) to keep compound nouns together.
    """

    def __init__(self) -> None:
        """Initialize the MorphologicalAnalyzer with SudachiPy dictionary."""
        self._dictionary = Dictionary()
        self._tokenizer = self._dictionary.create()

    def extract_proper_nouns(self, text: str) -> list[str]:
        """Extract proper nouns from the given text.

        Uses SudachiPy's morphological analysis to identify proper nouns.
        Proper nouns include:
        - Person names
        - Place names
        - Organization names
        - Product/service names

        Args:
            text: The Japanese text to analyze.

        Returns:
            List of unique proper nouns in order of first occurrence.
        """
        if not text or not text.strip():
            return []

        # Use split mode C for long unit segmentation
        morphemes = self._tokenizer.tokenize(text, SplitMode.C)

        proper_nouns: list[str] = []
        seen: set[str] = set()

        for morpheme in morphemes:
            # Get part of speech info
            pos = morpheme.part_of_speech()

            # Check if it's a proper noun (固有名詞)
            # pos[0] is the main category (e.g., "名詞")
            # pos[1] is the subcategory (e.g., "固有名詞")
            if len(pos) >= 2 and pos[0] == "名詞" and pos[1] == "固有名詞":
                surface = morpheme.surface()
                if surface not in seen:
                    proper_nouns.append(surface)
                    seen.add(surface)

        return proper_nouns
