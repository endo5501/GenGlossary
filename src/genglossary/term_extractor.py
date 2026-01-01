"""Term extractor - Step 1: Extract terms from documents using LLM."""

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document


class ExtractedTerms(BaseModel):
    """Response model for extracted terms."""

    terms: list[str]


class TermExtractor:
    """Extracts terms from documents using LLM.

    This class handles the first step of the glossary generation pipeline:
    extracting relevant terms from documents using an LLM.
    """

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
        # Filter out empty or whitespace-only documents
        non_empty_docs = [
            doc for doc in documents if doc.content and doc.content.strip()
        ]

        if not non_empty_docs:
            return []

        # Create prompt and extract terms using LLM
        prompt = self._create_extraction_prompt(non_empty_docs)
        response = self.llm_client.generate_structured(prompt, ExtractedTerms)

        # Process and deduplicate terms
        return self._process_terms(response.terms)

    def _create_extraction_prompt(self, documents: list[Document]) -> str:
        """Create the prompt for term extraction.

        Args:
            documents: List of documents to include in the prompt.

        Returns:
            The formatted prompt string.
        """
        # Combine all document contents
        combined_content = "\n\n---\n\n".join(doc.content for doc in documents)

        prompt = f"""あなたは技術文書の専門家です。以下のドキュメントから重要な専門用語を抽出してください。

抽出基準:
- ドキュメント内で繰り返し使用される用語
- 特定の文脈で特別な意味を持つ用語
- 読者が理解すべき重要な概念

ドキュメント:
{combined_content}

JSON形式で回答してください: {{"terms": ["用語1", "用語2", ...]}}"""

        return prompt

    def _process_terms(self, terms: list[str]) -> list[str]:
        """Process and deduplicate extracted terms.

        Args:
            terms: Raw list of terms from LLM.

        Returns:
            Processed list with duplicates removed and whitespace stripped.
        """
        seen: set[str] = set()
        result: list[str] = []

        for term in terms:
            # Strip whitespace
            stripped = term.strip()

            # Skip empty terms
            if not stripped:
                continue

            # Skip duplicates (preserve first occurrence order)
            if stripped in seen:
                continue

            # Apply filtering rules
            if self._should_filter_term(stripped):
                continue

            seen.add(stripped)
            result.append(stripped)

        return result

    def _should_filter_term(self, term: str) -> bool:
        """Check if a term should be filtered out.

        Args:
            term: The term to check.

        Returns:
            True if the term should be filtered out.
        """
        # Rule 1: Filter terms that are too short (1 character)
        if len(term) <= 1:
            return True

        # Rule 2: Filter verb phrases (ending with common verb patterns)
        verb_endings = (
            "する",
            "した",
            "している",
            "された",
            "される",
            "を発見",
            "の発見",
            "を潜り抜ける",
            "を行う",
            "を実施",
            "になる",
            "となる",
            "ている",
            "てある",
            "の崩壊",
        )
        if term.endswith(verb_endings):
            return True

        # Rule 3: Filter adjective phrases (common patterns)
        adjective_patterns = (
            "が良い",
            "が悪い",
            "が高い",
            "が低い",
            "の髪",
            "の目",
            "の顔",
            "の体",
            "色の",
            "的な",
        )
        for pattern in adjective_patterns:
            if pattern in term:
                return True

        # Rule 4: Filter if term is only hiragana and very common
        # (This helps filter common words like "とても", "しかし")
        if self._is_only_hiragana(term) and len(term) <= 4:
            return True

        return False

    def _is_only_hiragana(self, text: str) -> bool:
        """Check if text consists only of hiragana characters.

        Args:
            text: The text to check.

        Returns:
            True if text is only hiragana.
        """
        for char in text:
            if not ("\u3040" <= char <= "\u309f"):
                return False
        return True
