"""Term extractor - SudachiPy morphological analysis + LLM judgment."""

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.morphological_analyzer import MorphologicalAnalyzer


class TermJudgmentResponse(BaseModel):
    """Response model for term judgment by LLM."""

    approved_terms: list[str]


class TermExtractionAnalysis(BaseModel):
    """Analysis result of term extraction process.

    Contains intermediate results from both SudachiPy and LLM stages,
    useful for debugging and improving extraction quality.
    """

    sudachi_candidates: list[str]
    """Proper nouns extracted by SudachiPy morphological analysis."""

    llm_approved: list[str]
    """Terms approved by LLM for inclusion in glossary."""

    llm_rejected: list[str]
    """Terms rejected by LLM (candidates - approved)."""


class TermExtractor:
    """Extracts terms from documents using SudachiPy + LLM judgment.

    This class handles the first step of the glossary generation pipeline:
    1. Extract proper nouns using SudachiPy morphological analysis
    2. Send candidates to LLM for judgment on glossary suitability

    Attributes:
        llm_client: The LLM client for term judgment.
    """

    def __init__(self, llm_client: BaseLLMClient) -> None:
        """Initialize the TermExtractor.

        Args:
            llm_client: The LLM client to use for term judgment.
        """
        self.llm_client = llm_client
        self._morphological_analyzer = MorphologicalAnalyzer()

    def extract_terms(self, documents: list[Document]) -> list[str]:
        """Extract terms from the given documents.

        Uses SudachiPy to extract proper nouns, then LLM judges
        which are suitable for the glossary.

        Args:
            documents: List of documents to extract terms from.

        Returns:
            A list of unique approved terms.
        """
        # Filter out empty or whitespace-only documents
        non_empty_docs = [
            doc for doc in documents if doc.content and doc.content.strip()
        ]

        if not non_empty_docs:
            return []

        # Step 1: Extract proper nouns using morphological analysis
        candidates = self._extract_candidates(non_empty_docs)

        if not candidates:
            return []

        # Step 2: Send to LLM for judgment
        prompt = self._create_judgment_prompt(candidates, non_empty_docs)
        response = self.llm_client.generate_structured(prompt, TermJudgmentResponse)

        # Process and deduplicate approved terms
        return self._process_terms(response.approved_terms)

    def analyze_extraction(
        self, documents: list[Document]
    ) -> TermExtractionAnalysis:
        """Analyze term extraction without generating full glossary.

        Returns intermediate results from both SudachiPy and LLM stages,
        useful for debugging and improving extraction quality.

        Args:
            documents: List of documents to analyze.

        Returns:
            TermExtractionAnalysis with candidates, approved, and rejected terms.
        """
        # Filter out empty or whitespace-only documents
        non_empty_docs = [
            doc for doc in documents if doc.content and doc.content.strip()
        ]

        if not non_empty_docs:
            return TermExtractionAnalysis(
                sudachi_candidates=[],
                llm_approved=[],
                llm_rejected=[],
            )

        # Step 1: Extract proper nouns using morphological analysis
        candidates = self._extract_candidates(non_empty_docs)

        if not candidates:
            return TermExtractionAnalysis(
                sudachi_candidates=[],
                llm_approved=[],
                llm_rejected=[],
            )

        # Step 2: Send to LLM for judgment
        prompt = self._create_judgment_prompt(candidates, non_empty_docs)
        response = self.llm_client.generate_structured(prompt, TermJudgmentResponse)

        # Process approved terms
        raw_approved = self._process_terms(response.approved_terms)

        # Filter to only include terms that were in candidates
        # (LLM may suggest terms not in the original candidates)
        candidates_set = set(candidates)
        approved = [t for t in raw_approved if t in candidates_set]

        # Calculate rejected terms (candidates not in approved)
        approved_set = set(approved)
        rejected = [c for c in candidates if c not in approved_set]

        return TermExtractionAnalysis(
            sudachi_candidates=candidates,
            llm_approved=approved,
            llm_rejected=rejected,
        )

    def _extract_candidates(self, documents: list[Document]) -> list[str]:
        """Extract candidate terms using morphological analysis.

        Args:
            documents: List of documents to analyze.

        Returns:
            List of unique candidate proper nouns.
        """
        candidates: list[str] = []
        seen: set[str] = set()

        for doc in documents:
            proper_nouns = self._morphological_analyzer.extract_proper_nouns(
                doc.content
            )
            for noun in proper_nouns:
                if noun not in seen:
                    candidates.append(noun)
                    seen.add(noun)

        return candidates

    def _create_judgment_prompt(
        self, candidates: list[str], documents: list[Document]
    ) -> str:
        """Create the prompt for LLM term judgment.

        Args:
            candidates: List of candidate terms from morphological analysis.
            documents: List of documents for context.

        Returns:
            The formatted prompt string.
        """
        candidates_text = ", ".join(candidates)
        combined_content = "\n\n---\n\n".join(doc.content for doc in documents)

        prompt = f"""あなたは用語集作成の専門家です。
形態素解析により以下の固有名詞候補が抽出されました。

## 候補用語:
{candidates_text}

## 判断基準
この用語集は、ドキュメントの読者が文脈を理解するための補助として使われます。
以下の基準で、用語集に掲載すべきかどうか判断してください:

1. 読者がこの用語の「この文脈での意味」を知りたいと思うか？
2. 辞書を引いても、この文脈での意味は分からないか？
3. 固有名詞であれば、説明があると文章理解が深まるか？

## 採用しない例
- 広く知られた一般的な地名や国名（ただし、文脈で特殊な意味を持つ場合は採用）
- 自明な略語や標準的な技術用語

## ドキュメントのコンテキスト:
{combined_content}

JSON形式で回答してください: {{"approved_terms": ["用語1", "用語2", ...]}}

候補用語から、用語集に掲載すべきものだけを選んで approved_terms に含めてください。"""

        return prompt

    def _process_terms(self, terms: list[str]) -> list[str]:
        """Process and deduplicate approved terms.

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

            seen.add(stripped)
            result.append(stripped)

        return result
