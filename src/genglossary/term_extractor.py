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

        prompt = f"""あなたは用語集作成の専門家です。以下のドキュメントから、用語集に掲載すべき重要な用語を抽出してください。

## 抽出すべき用語（含める）
- 固有名詞: 人名、地名、組織名、作品固有の名称
- 専門用語: その文脈で特別な意味を持つ語
- 造語・特殊用語: 作品やドキュメント固有の造語
- 概念名: 重要なコンセプトや仕組みの名称
- 略語・頭字語: API、LLM など

## 抽出しない用語（除外）
- 一般名詞: 辞書で意味が自明な日常語（借金、ビール、再会、張り紙など）
- 動詞・動詞句: 「〜する」「〜を発見」「死戦を潜り抜ける」など動作を表すフレーズ
- 形容詞句・描写表現: 「顔が良い」「銀色の髪」など外見や状態の描写
- 接続詞・副詞: しかし、ただし、非常に、など
- 数量表現: 3つ、2回目、など

## 判断基準
1. 読者がこの用語の「この文脈での意味」を知りたいと思うか？
2. 辞書を引いても、この文脈での意味は分からないか？
3. 固有名詞であれば、説明があると文章理解が深まるか？

上記に該当する場合は用語として抽出してください。

## ドキュメント:
{combined_content}

JSON形式で回答してください: {{"terms": ["用語1", "用語2", ...]}}

注意: 用語は名詞または名詞句のみを抽出し、動詞句や形容詞句は含めないでください。"""

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
