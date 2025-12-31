"""Term extractor - Step 1: Extract terms from documents using LLM."""

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document


class TermExtractor:
    """Extracts terms from documents using LLM."""

    def __init__(self, llm_client: BaseLLMClient) -> None:
        """Initialize the TermExtractor.

        Args:
            llm_client: The LLM client to use for term extraction.
        """
        self.llm_client = llm_client

    def extract_terms(self, documents: list[Document]) -> list[str]:
        """Extract terms from the given documents.

        Args:
            documents: List of documents to extract terms from.

        Returns:
            A list of unique extracted terms.
        """
        raise NotImplementedError("extract_terms not yet implemented")

    def _create_extraction_prompt(self, documents: list[Document]) -> str:
        """Create the prompt for term extraction.

        Args:
            documents: List of documents to include in the prompt.

        Returns:
            The formatted prompt string.
        """
        raise NotImplementedError("_create_extraction_prompt not yet implemented")
