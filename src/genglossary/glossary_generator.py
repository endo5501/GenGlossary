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


class RelatedTermsResponse(BaseModel):
    """Response model for related terms extraction."""

    related_terms: list[str]


class GlossaryGenerator:
    """Generates provisional glossary from terms and documents using LLM.

    This class handles the second step of the glossary generation pipeline:
    generating definitions for terms using context from documents.
    """

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
            # Find occurrences
            occurrences = self._find_term_occurrences(term_name, documents)

            # Generate definition using LLM
            definition, confidence = self._generate_definition(
                term_name, occurrences
            )

            # Extract related terms
            related = self._extract_related_terms(
                term_name, definition, terms
            )

            # Create Term object
            term = Term(
                name=term_name,
                definition=definition,
                occurrences=occurrences,
                related_terms=related,
                confidence=confidence,
            )

            glossary.add_term(term)

        return glossary

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
        occurrences: list[TermOccurrence] = []

        # Escape special regex characters in the term
        escaped_term = re.escape(term)

        # Create pattern with word boundaries
        # For Japanese/CJK characters, we need different handling
        if self._contains_cjk(term):
            # For CJK characters, don't use word boundaries
            pattern = re.compile(escaped_term)
        else:
            # For ASCII terms, use lookahead/lookbehind for word boundaries
            # This works better with mixed Japanese/English text
            # Match if not preceded/followed by ASCII word characters
            pattern = re.compile(
                rf"(?<![a-zA-Z0-9_]){escaped_term}(?![a-zA-Z0-9_])"
            )

        for doc in documents:
            for line_num, line in enumerate(doc.lines, start=1):
                if pattern.search(line):
                    # Get context (the line itself and surrounding context)
                    context_lines = doc.get_context(line_num, context_lines=1)
                    context = "\n".join(context_lines)

                    occurrence = TermOccurrence(
                        document_path=doc.file_path,
                        line_number=line_num,
                        context=context,
                    )
                    occurrences.append(occurrence)

        return occurrences

    def _contains_cjk(self, text: str) -> bool:
        """Check if text contains CJK (Chinese, Japanese, Korean) characters.

        Args:
            text: The text to check.

        Returns:
            True if the text contains CJK characters.
        """
        for char in text:
            # CJK Unified Ideographs and common ranges
            if "\u4e00" <= char <= "\u9fff":  # CJK Unified Ideographs
                return True
            if "\u3040" <= char <= "\u309f":  # Hiragana
                return True
            if "\u30a0" <= char <= "\u30ff":  # Katakana
                return True
            if "\uac00" <= char <= "\ud7af":  # Korean Hangul
                return True
        return False

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

    def _extract_related_terms(
        self, term: str, definition: str, all_terms: list[str]
    ) -> list[str]:
        """Extract related terms using LLM.

        Args:
            term: The current term.
            definition: The term's definition.
            all_terms: List of all terms in the glossary.

        Returns:
            List of related term names.
        """
        # Filter out the current term from candidates
        candidates = [t for t in all_terms if t != term]

        if not candidates:
            return []

        candidates_text = ", ".join(candidates)

        prompt = f"""用語: {term}
定義: {definition}
候補用語リスト: {candidates_text}

上記の候補用語リストから、「{term}」と関連のある用語を選んでください。
JSON形式で回答してください: {{"related_terms": ["用語1", "用語2", ...]}}"""

        response = self.llm_client.generate_structured(
            prompt, RelatedTermsResponse
        )

        return response.related_terms
