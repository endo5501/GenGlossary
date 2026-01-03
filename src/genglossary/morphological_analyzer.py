"""Morphological analyzer using SudachiPy for proper noun extraction."""

from sudachipy import Dictionary, SplitMode


class MorphologicalAnalyzer:
    """Analyzes Japanese text to extract proper nouns using SudachiPy.

    Uses SudachiPy with split mode C (long unit) to keep compound nouns together.
    Handles long texts by splitting into chunks to avoid SudachiPy's size limit.
    """

    # SudachiPy's maximum input size is 49149 bytes
    # Use a smaller chunk size to leave buffer for safety
    MAX_CHUNK_BYTES = 40000

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

        For texts exceeding SudachiPy's size limit, the text is split into
        smaller chunks and processed separately.

        Args:
            text: The Japanese text to analyze.

        Returns:
            List of unique proper nouns in order of first occurrence.
        """
        if not text or not text.strip():
            return []

        # Check if text exceeds the size limit
        text_bytes = len(text.encode("utf-8"))
        if text_bytes <= self.MAX_CHUNK_BYTES:
            return self._extract_from_text(text)

        # Split text into chunks and process each
        chunks = self._split_into_chunks(text)
        proper_nouns: list[str] = []
        seen: set[str] = set()

        for chunk in chunks:
            chunk_nouns = self._extract_from_text(chunk)
            for noun in chunk_nouns:
                if noun not in seen:
                    proper_nouns.append(noun)
                    seen.add(noun)

        return proper_nouns

    def _extract_from_text(self, text: str) -> list[str]:
        """Extract proper nouns from a single chunk of text.

        Args:
            text: The text chunk to analyze (must be within size limit).

        Returns:
            List of unique proper nouns in order of first occurrence.
        """
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

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into chunks that fit within SudachiPy's size limit.

        Attempts to split at sentence boundaries (。) to avoid breaking
        proper nouns that span multiple characters.

        Args:
            text: The text to split.

        Returns:
            List of text chunks, each within the size limit.
        """
        chunks: list[str] = []
        current_chunk = ""
        current_bytes = 0

        # Split by sentences first
        sentences = text.split("。")

        for i, sentence in enumerate(sentences):
            # Add back the period except for the last empty part
            if i < len(sentences) - 1:
                sentence = sentence + "。"

            sentence_bytes = len(sentence.encode("utf-8"))

            # If a single sentence exceeds the limit, split by characters
            if sentence_bytes > self.MAX_CHUNK_BYTES:
                # First, flush the current chunk if any
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                    current_bytes = 0

                # Split the long sentence by characters
                char_chunks = self._split_long_sentence(sentence)
                chunks.extend(char_chunks)
            elif current_bytes + sentence_bytes > self.MAX_CHUNK_BYTES:
                # Start a new chunk
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                current_bytes = sentence_bytes
            else:
                current_chunk += sentence
                current_bytes += sentence_bytes

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_long_sentence(self, sentence: str) -> list[str]:
        """Split a very long sentence into smaller chunks by characters.

        Args:
            sentence: A sentence that exceeds the chunk size limit.

        Returns:
            List of character-based chunks.
        """
        chunks: list[str] = []
        current_chunk = ""
        current_bytes = 0

        for char in sentence:
            char_bytes = len(char.encode("utf-8"))

            if current_bytes + char_bytes > self.MAX_CHUNK_BYTES:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = char
                current_bytes = char_bytes
            else:
                current_chunk += char
                current_bytes += char_bytes

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
