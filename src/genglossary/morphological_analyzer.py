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

    def extract_proper_nouns(
        self,
        text: str,
        extract_compound_nouns: bool = False,
        include_common_nouns: bool = False,
        min_length: int = 1,
        min_frequency: int = 1,
        filter_contained: bool = False,
    ) -> list[str]:
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
            extract_compound_nouns: If True, extract compound nouns by combining
                consecutive noun morphemes.
            include_common_nouns: If True, include common nouns (普通名詞) in addition
                to proper nouns. Useful for extracting domain-specific technical terms.
            min_length: Minimum character length for extracted terms. Terms shorter
                than this are filtered out. Default is 1 (no filtering).
            min_frequency: Minimum number of occurrences for a term to be included.
                Terms appearing fewer times are filtered out. Default is 1 (no filtering).
            filter_contained: If True, remove terms that are substrings of other
                longer terms. Useful for removing redundant compound noun variants.
                Default is False for backward compatibility.

        Returns:
            List of unique terms in order of first occurrence.
        """
        if not text or not text.strip():
            return []

        # Check if text exceeds the size limit
        text_bytes = len(text.encode("utf-8"))
        if text_bytes <= self.MAX_CHUNK_BYTES:
            terms = self._extract_from_text(
                text, extract_compound_nouns, include_common_nouns
            )
        else:
            # Split text into chunks and process each
            chunks = self._split_into_chunks(text)
            terms_list: list[str] = []
            seen: set[str] = set()

            for chunk in chunks:
                chunk_terms = self._extract_from_text(
                    chunk, extract_compound_nouns, include_common_nouns
                )
                for term in chunk_terms:
                    if term not in seen:
                        terms_list.append(term)
                        seen.add(term)

            terms = terms_list

        # Apply length and frequency filtering
        if min_length > 1 or min_frequency > 1:
            terms = self._apply_filters(text, terms, min_length, min_frequency)

        # Apply contained term filtering
        if filter_contained:
            terms = self.filter_contained_terms(terms)

        return terms

    def _extract_from_text(
        self,
        text: str,
        extract_compound_nouns: bool = False,
        include_common_nouns: bool = False,
    ) -> list[str]:
        """Extract terms from a single chunk of text.

        Args:
            text: The text chunk to analyze (must be within size limit).
            extract_compound_nouns: If True, extract compound nouns.
            include_common_nouns: If True, include common nouns.

        Returns:
            List of unique terms in order of first occurrence.
        """
        # Use split mode C for long unit segmentation
        morphemes = self._tokenizer.tokenize(text, SplitMode.C)

        terms: list[str] = []
        seen: set[str] = set()

        # For compound noun extraction, track consecutive nouns and noun-like elements
        if extract_compound_nouns:
            i = 0
            while i < len(morphemes):
                pos = morphemes[i].part_of_speech()

                # Check if it's a noun or noun-like element (including suffixes)
                if self._is_noun_like(pos):
                    # Start collecting consecutive noun-like elements
                    compound_parts: list[str] = [morphemes[i].surface()]
                    j = i + 1

                    # Collect consecutive noun-like elements
                    while j < len(morphemes):
                        next_pos = morphemes[j].part_of_speech()
                        if self._is_noun_like(next_pos):
                            compound_parts.append(morphemes[j].surface())
                            j += 1
                        else:
                            break

                    # Extract all possible compound nouns (length >= 2)
                    # This includes partial combinations like 騎士団, 団長, 騎士団長
                    if len(compound_parts) >= 2:
                        for start_idx in range(len(compound_parts)):
                            for end_idx in range(start_idx + 2, len(compound_parts) + 1):
                                compound = "".join(compound_parts[start_idx:end_idx])
                                if compound not in seen:
                                    terms.append(compound)
                                    seen.add(compound)

                    # Also add individual nouns if they match our criteria
                    for k in range(i, j):
                        if self._should_extract_noun(
                            morphemes[k], include_common_nouns
                        ):
                            surface = morphemes[k].surface()
                            if surface not in seen:
                                terms.append(surface)
                                seen.add(surface)

                    i = j
                else:
                    i += 1
        else:
            # Original behavior: extract individual nouns
            for morpheme in morphemes:
                if self._should_extract_noun(morpheme, include_common_nouns):
                    surface = morpheme.surface()
                    if surface not in seen:
                        terms.append(surface)
                        seen.add(surface)

        return terms

    def _is_noun_like(self, pos: list[str]) -> bool:
        """Check if a morpheme is noun-like (noun or noun-forming suffix).

        Args:
            pos: Part of speech information.

        Returns:
            True if the morpheme is noun-like.
        """
        if len(pos) < 1:
            return False

        # Include nouns
        if pos[0] == "名詞":
            return True

        # Include noun-forming suffixes (接尾辞-名詞的)
        if pos[0] == "接尾辞" and len(pos) >= 2 and pos[1] == "名詞的":
            return True

        return False

    def _should_extract_noun(self, morpheme, include_common_nouns: bool) -> bool:
        """Check if a morpheme should be extracted as a term.

        Args:
            morpheme: The morpheme to check.
            include_common_nouns: Whether to include common nouns.

        Returns:
            True if the morpheme should be extracted.
        """
        pos = morpheme.part_of_speech()

        # Always extract proper nouns
        if len(pos) >= 2 and pos[0] == "名詞" and pos[1] == "固有名詞":
            return True

        # Extract common nouns if enabled
        if include_common_nouns and len(pos) >= 2 and pos[0] == "名詞":
            # Include 普通名詞 (common nouns)
            if pos[1] == "普通名詞":
                return True

        return False

    def _apply_filters(
        self, text: str, terms: list[str], min_length: int, min_frequency: int
    ) -> list[str]:
        """Apply length and frequency filters to extracted terms.

        Args:
            text: The original text.
            terms: List of extracted terms.
            min_length: Minimum character length.
            min_frequency: Minimum occurrence count.

        Returns:
            Filtered list of terms, preserving order of first occurrence.
        """
        # Count frequency of each term in the original text
        frequency_map: dict[str, int] = {}
        for term in terms:
            frequency_map[term] = text.count(term)

        # Apply filters while preserving order
        filtered_terms: list[str] = []
        for term in terms:
            # Length filter
            if len(term) < min_length:
                continue

            # Frequency filter
            if frequency_map[term] < min_frequency:
                continue

            filtered_terms.append(term)

        return filtered_terms

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

    def filter_contained_terms(self, terms: list[str]) -> list[str]:
        """Filter out terms that are contained within other longer terms.

        When compound noun extraction generates all possible sub-combinations,
        this method keeps only the longest terms by removing any term that
        is a substring of another term.

        Args:
            terms: List of terms to filter.

        Returns:
            List of terms with contained (substring) terms removed,
            preserving the order of first occurrence.
        """
        if len(terms) <= 1:
            return terms.copy() if terms else []

        # Remove duplicates while preserving order
        unique_terms: list[str] = []
        seen: set[str] = set()
        for term in terms:
            if term not in seen:
                unique_terms.append(term)
                seen.add(term)

        # Build a set of terms that are contained in other terms
        contained_terms: set[str] = set()

        for term in unique_terms:
            for other_term in unique_terms:
                # Check if term is contained in other_term (but not equal)
                if term != other_term and term in other_term:
                    contained_terms.add(term)
                    break  # No need to check further once we know it's contained

        # Return terms that are not contained in any other term
        return [term for term in unique_terms if term not in contained_terms]
