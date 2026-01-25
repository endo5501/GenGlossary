"""Glossary generator - Step 2: Generate provisional glossary using LLM."""

import re

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.models.term import ClassifiedTerm, Term, TermCategory, TermOccurrence
from genglossary.types import ProgressCallback


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
        self,
        terms: list[str] | list[ClassifiedTerm],
        documents: list[Document],
        progress_callback: ProgressCallback | None = None,
        skip_common_nouns: bool = True,
    ) -> Glossary:
        """Generate a provisional glossary.

        Args:
            terms: List of terms to generate definitions for.
                Can be either list[str] or list[ClassifiedTerm].
            documents: List of documents containing the terms.
            progress_callback: Optional callback called after each term is processed.
                Receives (current, total) where current is 1-indexed.
            skip_common_nouns: If True (default), skip terms categorized as common_noun
                when terms is list[ClassifiedTerm]. Has no effect when terms is list[str].

        Returns:
            A Glossary object with terms and their definitions.
        """
        glossary = Glossary()

        if not terms:
            return glossary

        # Filter terms if ClassifiedTerm list and skip_common_nouns is True
        filtered_terms = self._filter_terms(terms, skip_common_nouns)
        if not filtered_terms:
            return glossary

        total_terms = len(filtered_terms)
        for idx, term_item in enumerate(filtered_terms, start=1):
            # Extract term name (support both str and ClassifiedTerm)
            term_name = term_item if isinstance(term_item, str) else term_item.term

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
            finally:
                # Call progress callback if provided
                if progress_callback is not None:
                    progress_callback(idx, total_terms)

        return glossary

    def _filter_terms(
        self, terms: list[str] | list[ClassifiedTerm], skip_common_nouns: bool
    ) -> list[str] | list[ClassifiedTerm]:
        """Filter terms based on skip_common_nouns flag.

        Args:
            terms: List of terms (str or ClassifiedTerm).
            skip_common_nouns: Whether to skip common_noun category.

        Returns:
            Filtered list of terms.
        """
        # If terms is list[str], return as-is
        if not terms or isinstance(terms[0], str):
            return terms

        # If skip_common_nouns is False, return all terms
        if not skip_common_nouns:
            return terms

        # Filter out common_noun category
        return [
            term
            for term in terms
            if isinstance(term, ClassifiedTerm)
            and term.category != TermCategory.COMMON_NOUN
        ]

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

## Few-shot Examples

**用語:** アソリウス島騎士団
**定義:** エデルト王国の辺境、アソリウス島を守る騎士団。魔神討伐の最前線として重要な役割を担う。
**信頼度:** 0.9

文脈固有の意味を1-2文で説明。信頼度: 明確=0.8+, 推測可能=0.5-0.7, 不明確=0.0-0.4
JSON形式で回答してください: {{"definition": "...", "confidence": 0.0-1.0}}"""

        response = self.llm_client.generate_structured(
            prompt, DefinitionResponse
        )

        return response.definition, response.confidence
