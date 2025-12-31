"""Glossary generator - Step 2: Generate provisional glossary using LLM."""

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.models.term import TermOccurrence


class GlossaryGenerator:
    """Generates provisional glossary from terms and documents using LLM."""

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
        raise NotImplementedError("generate not yet implemented")

    def _find_term_occurrences(
        self, term: str, documents: list[Document]
    ) -> list[TermOccurrence]:
        """Find all occurrences of a term in the documents.

        Args:
            term: The term to search for.
            documents: List of documents to search in.

        Returns:
            List of TermOccurrence objects.
        """
        raise NotImplementedError("_find_term_occurrences not yet implemented")

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
        raise NotImplementedError("_generate_definition not yet implemented")

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
        raise NotImplementedError("_extract_related_terms not yet implemented")
