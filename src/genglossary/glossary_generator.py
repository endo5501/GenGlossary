"""Glossary generator - Step 2: Generate provisional glossary using LLM."""

import re

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.models.term import Term, TermOccurrence


class DefinitionResponse(BaseModel):
    """Response model for definition generation."""

    definition: str
    confidence: float


class GlossaryGenerator:
    """Generates provisional glossary from terms and documents using LLM.

    This class handles the second step of the glossary generation pipeline:
    generating definitions for terms using context from documents.
    """

    # Unicode ranges for CJK character detection
    CJK_RANGES = [
        ("\u4e00", "\u9fff"),  # CJK Unified Ideographs
        ("\u3040", "\u309f"),  # Hiragana
        ("\u30a0", "\u30ff"),  # Katakana
        ("\uac00", "\ud7af"),  # Korean Hangul
    ]

    def __init__(self, llm_client: BaseLLMClient) -> None:
        """Initialize the GlossaryGenerator.

        Args:
            llm_client: The LLM client to use for definition generation.
        """
        self.llm_client = llm_client

    def generate(
        self, terms: list[str], documents: list[Document]
    ) -> Glossary:
        """Generate a provisional glossary.

        Args:
            terms: List of terms to generate definitions for.
            documents: List of documents containing the terms.

        Returns:
            A Glossary object with terms and their definitions.
        """
        glossary = Glossary()

        if not terms:
            return glossary

        for term_name in terms:
            try:
                # Find occurrences
                occurrences = self._find_term_occurrences(term_name, documents)

                # Generate definition using LLM
                definition, confidence = self._generate_definition(
                    term_name, occurrences
                )

                # Create Term object
                term = Term(
                    name=term_name,
                    definition=definition,
                    occurrences=occurrences,
                    confidence=confidence,
                )

                glossary.add_term(term)
            except Exception as e:
                # Skip this term and continue with the next one
                print(f"Warning: Failed to generate definition for '{term_name}': {e}")
                continue

        return glossary

    def _build_search_pattern(self, term: str) -> re.Pattern:
        """Build a regex pattern for searching a term.

        For CJK characters, uses simple matching without word boundaries.
        For ASCII terms, uses lookahead/lookbehind for word boundaries.

        Args:
            term: The term to build a pattern for.

        Returns:
            Compiled regex pattern.
        """
        escaped_term = re.escape(term)

        if self._contains_cjk(term):
            return re.compile(escaped_term)

        # For ASCII terms, match if not preceded/followed by ASCII word characters
        return re.compile(rf"(?<![a-zA-Z0-9_]){escaped_term}(?![a-zA-Z0-9_])")

    def _create_occurrence(
        self, doc: Document, line_num: int
    ) -> TermOccurrence:
        """Create a TermOccurrence with context from a document.

        Args:
            doc: The document containing the occurrence.
            line_num: The line number where the term occurs.

        Returns:
            A TermOccurrence object with context.
        """
        context_lines = doc.get_context(line_num, context_lines=1)
        context = "\n".join(context_lines)

        return TermOccurrence(
            document_path=doc.file_path,
            line_number=line_num,
            context=context,
        )

    def _find_term_occurrences(
        self, term: str, documents: list[Document]
    ) -> list[TermOccurrence]:
        """Find all occurrences of a term in the documents.

        Uses regex with word boundaries for precise matching.

        Args:
            term: The term to search for.
            documents: List of documents to search in.

        Returns:
            List of TermOccurrence objects.
        """
        pattern = self._build_search_pattern(term)
        occurrences: list[TermOccurrence] = []

        for doc in documents:
            for line_num, line in enumerate(doc.lines, start=1):
                if pattern.search(line):
                    occurrences.append(self._create_occurrence(doc, line_num))

        return occurrences

    def _contains_cjk(self, text: str) -> bool:
        """Check if text contains CJK (Chinese, Japanese, Korean) characters.

        Args:
            text: The text to check.

        Returns:
            True if the text contains CJK characters.
        """
        return any(
            start <= char <= end
            for char in text
            for start, end in self.CJK_RANGES
        )

    def _generate_definition(
        self, term: str, occurrences: list[TermOccurrence]
    ) -> tuple[str, float]:
        """Generate a definition for a term using LLM.

        Args:
            term: The term to define.
            occurrences: List of occurrences with context.

        Returns:
            Tuple of (definition, confidence).
        """
        # Build context from occurrences
        if occurrences:
            contexts = [
                f"- {occ.context}" for occ in occurrences[:5]  # Limit to 5
            ]
            context_text = "\n".join(contexts)
        else:
            context_text = "(ドキュメント内に出現箇所がありません)"

        prompt = f"""用語: {term}
出現箇所とコンテキスト:
{context_text}

このドキュメント固有の使われ方を説明してください。
JSON形式で回答してください: {{"definition": "...", "confidence": 0.0-1.0}}"""

        response = self.llm_client.generate_structured(
            prompt, DefinitionResponse
        )

        return response.definition, response.confidence
