"""Term extractor - SudachiPy morphological analysis + LLM judgment."""

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.term import TermCategory
from genglossary.morphological_analyzer import MorphologicalAnalyzer


class TermJudgmentResponse(BaseModel):
    """Response model for term judgment by LLM."""

    approved_terms: list[str]


class TermClassificationResponse(BaseModel):
    """Response model for term classification by LLM.

    Used in the first phase of two-phase LLM processing.
    Each term is classified into one of the TermCategory categories.
    """

    classified_terms: dict[str, list[str]]
    """Dictionary mapping category names to lists of terms."""


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

    pre_filter_candidate_count: int = 0
    """Count of candidates before contained terms filtering."""

    post_filter_candidate_count: int = 0
    """Count of candidates after contained terms filtering."""

    classification_results: dict[str, list[str]] = {}
    """LLM classification results by category."""


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

        Uses a two-phase LLM process:
        1. Classification phase: Categorize terms into 6 categories
        2. Selection phase: Select terms from non-common-noun categories

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

        # Step 2: Classify terms (Phase 1 of LLM processing)
        classification = self._classify_terms(candidates, non_empty_docs)

        # Step 3: Select terms, excluding common nouns (Phase 2 of LLM processing)
        return self._select_terms(classification, non_empty_docs)

    def analyze_extraction(
        self, documents: list[Document]
    ) -> TermExtractionAnalysis:
        """Analyze term extraction without generating full glossary.

        Returns intermediate results from both SudachiPy and LLM stages,
        useful for debugging and improving extraction quality.

        Uses two-phase LLM processing:
        1. Classification phase: Categorize terms into 6 categories
        2. Selection phase: Select terms from non-common-noun categories

        Args:
            documents: List of documents to analyze.

        Returns:
            TermExtractionAnalysis with candidates, approved, rejected terms,
            filter counts, and classification results.
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
                pre_filter_candidate_count=0,
                post_filter_candidate_count=0,
                classification_results={},
            )

        # Step 1a: Extract candidates WITHOUT filter to get pre-filter count
        pre_filter_candidates = self._extract_candidates_raw(non_empty_docs)
        pre_filter_count = len(pre_filter_candidates)

        # Step 1b: Extract candidates WITH filter to get post-filter count
        candidates = self._extract_candidates(non_empty_docs)
        post_filter_count = len(candidates)

        if not candidates:
            return TermExtractionAnalysis(
                sudachi_candidates=[],
                llm_approved=[],
                llm_rejected=[],
                pre_filter_candidate_count=pre_filter_count,
                post_filter_candidate_count=0,
                classification_results={},
            )

        # Step 2: Classify terms (Phase 1 of LLM processing)
        classification = self._classify_terms(candidates, non_empty_docs)

        # Step 3: Select terms (Phase 2 of LLM processing)
        approved = self._select_terms(classification, non_empty_docs)

        # Calculate rejected terms (candidates not in approved)
        approved_set = set(approved)
        rejected = [c for c in candidates if c not in approved_set]

        return TermExtractionAnalysis(
            sudachi_candidates=candidates,
            llm_approved=approved,
            llm_rejected=rejected,
            pre_filter_candidate_count=pre_filter_count,
            post_filter_candidate_count=post_filter_count,
            classification_results=classification.classified_terms,
        )

    def _extract_candidates(self, documents: list[Document]) -> list[str]:
        """Extract candidate terms using morphological analysis.

        Uses enhanced extraction with:
        - Compound noun extraction (e.g., 騎士団長, アソリウス島騎士団)
        - Common noun inclusion (e.g., 聖印, 魔神討伐)
        - Minimum length filtering (2 characters to keep common proper nouns)
        - Contained term filtering (removes redundant substring terms)

        Args:
            documents: List of documents to analyze.

        Returns:
            List of unique candidate terms.
        """
        candidates: list[str] = []
        seen: set[str] = set()

        for doc in documents:
            # Use enhanced extraction parameters
            # min_length=2 keeps common Japanese proper nouns (東京, 日本, etc.)
            # filter_contained=True removes redundant compound noun variants
            terms = self._morphological_analyzer.extract_proper_nouns(
                doc.content,
                extract_compound_nouns=True,
                include_common_nouns=True,
                min_length=2,
                filter_contained=True,
            )
            for term in terms:
                if term not in seen:
                    candidates.append(term)
                    seen.add(term)

        return candidates

    def _extract_candidates_raw(self, documents: list[Document]) -> list[str]:
        """Extract candidate terms WITHOUT contained term filtering.

        Used for analysis to show pre-filter candidate count.

        Args:
            documents: List of documents to analyze.

        Returns:
            List of unique candidate terms (before filtering).
        """
        candidates: list[str] = []
        seen: set[str] = set()

        for doc in documents:
            # Same parameters as _extract_candidates but filter_contained=False
            terms = self._morphological_analyzer.extract_proper_nouns(
                doc.content,
                extract_compound_nouns=True,
                include_common_nouns=True,
                min_length=2,
                filter_contained=False,
            )
            for term in terms:
                if term not in seen:
                    candidates.append(term)
                    seen.add(term)

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
形態素解析により以下の用語候補が抽出されました。
候補には固有名詞、複合名詞、技術用語が含まれています。

## 候補用語:
{candidates_text}

## 判断基準
この用語集は、ドキュメントの読者が文脈を理解するための補助として使われます。
以下の基準で、用語集に掲載すべきかどうか判断してください:

1. 読者がこの用語の「この文脈での意味」を知りたいと思うか？
2. 辞書を引いても、この文脈での意味は分からないか？
3. 固有名詞・組織名・役職名であれば、説明があると文章理解が深まるか？
4. 専門用語・技術用語として、この文脈での定義が必要か？

## 採用しない例
- 広く知られた一般的な地名や国名（ただし、文脈で特殊な意味を持つ場合は採用）
- 一般的すぎる普通名詞（「方角」「重要」など）
- 文脈に依存しない基本的な単語

## 採用する例
- 固有の組織名、役職名、称号（例: アソリウス島騎士団、騎士代理爵位）
- この文脈特有の意味を持つ用語（例: 聖印、魔神討伐）
- 複合的な専門用語（例: 魔神代理領、近衛騎士団長）

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

    def _classify_terms(
        self, candidates: list[str], documents: list[Document]
    ) -> TermClassificationResponse:
        """Classify terms into categories using LLM.

        This is the first phase of two-phase LLM processing.
        Terms are classified into 6 categories:
        - person_name: Person names
        - place_name: Place names
        - organization: Organization/group names
        - title: Titles and positions
        - technical_term: Technical/domain-specific terms
        - common_noun: Common nouns (will be excluded)

        Args:
            candidates: List of candidate terms to classify.
            documents: List of documents for context.

        Returns:
            TermClassificationResponse with classified terms.
        """
        prompt = self._create_classification_prompt(candidates, documents)
        return self.llm_client.generate_structured(prompt, TermClassificationResponse)

    def _create_classification_prompt(
        self, candidates: list[str], documents: list[Document]
    ) -> str:
        """Create the prompt for LLM term classification.

        Args:
            candidates: List of candidate terms to classify.
            documents: List of documents for context.

        Returns:
            The formatted prompt string.
        """
        candidates_text = ", ".join(candidates)
        combined_content = "\n\n---\n\n".join(doc.content for doc in documents)

        prompt = f"""あなたは用語分類の専門家です。
以下の用語候補を6つのカテゴリに分類してください。

## 候補用語:
{candidates_text}

## カテゴリ定義

1. **person_name（人名）**: 架空・実在の人物名
   例: ガウス卿、田中太郎、アリス

2. **place_name（地名）**: 国名、都市名、地域名、場所の名前
   例: エデルト、アソリウス島、東京

3. **organization（組織・団体名）**: 騎士団、軍隊、企業、団体など
   例: アソリウス島騎士団、エデルト軍、近衛騎士団

4. **title（役職・称号）**: 王子、騎士団長、将軍などの役職や称号
   例: 騎士団長、騎士代理爵位、将軍

5. **technical_term（技術用語・専門用語）**: この文脈特有の専門用語
   例: 聖印、魔神討伐、魔神代理領

6. **common_noun（一般名詞）**: 辞書的意味で理解できる一般的な名詞
   例: 未亡人、行方不明、方角、重要

## ドキュメントのコンテキスト:
{combined_content}

## 注意事項
- 各用語は必ず1つのカテゴリにのみ分類してください
- 文脈を考慮して、最も適切なカテゴリを選んでください
- 迷った場合は、用語集に載せるべきかどうかを基準に判断してください

JSON形式で回答してください:
{{
  "classified_terms": {{
    "person_name": ["用語1", "用語2"],
    "place_name": ["用語3"],
    "organization": ["用語4"],
    "title": ["用語5"],
    "technical_term": ["用語6"],
    "common_noun": ["用語7", "用語8"]
  }}
}}

候補用語をすべて分類してください。"""

        return prompt

    def _select_terms(
        self,
        classification: TermClassificationResponse,
        documents: list[Document],
    ) -> list[str]:
        """Select terms from classification results, excluding common nouns.

        This is the second phase of two-phase LLM processing.
        Common nouns are automatically excluded. Other categories
        are sent to LLM for final selection.

        Args:
            classification: Classification results from first phase.
            documents: List of documents for context.

        Returns:
            List of approved terms.
        """
        # Collect non-common-noun terms
        candidates_for_selection: list[str] = []
        for category, terms in classification.classified_terms.items():
            if category != TermCategory.COMMON_NOUN.value:
                candidates_for_selection.extend(terms)

        if not candidates_for_selection:
            return []

        # Send to LLM for final selection
        prompt = self._create_selection_prompt(
            candidates_for_selection, classification, documents
        )
        response = self.llm_client.generate_structured(prompt, TermJudgmentResponse)

        return self._process_terms(response.approved_terms)

    def _create_selection_prompt(
        self,
        candidates: list[str],
        classification: TermClassificationResponse,
        documents: list[Document],
    ) -> str:
        """Create the prompt for LLM term selection (second phase).

        Args:
            candidates: List of candidate terms (excluding common nouns).
            classification: Classification results for context.
            documents: List of documents for context.

        Returns:
            The formatted prompt string.
        """
        combined_content = "\n\n---\n\n".join(doc.content for doc in documents)

        # Format classified terms for context
        classification_text = ""
        for category, terms in classification.classified_terms.items():
            if category != TermCategory.COMMON_NOUN.value and terms:
                category_label = {
                    "person_name": "人名",
                    "place_name": "地名",
                    "organization": "組織・団体名",
                    "title": "役職・称号",
                    "technical_term": "技術用語",
                }.get(category, category)
                classification_text += f"- {category_label}: {', '.join(terms)}\n"

        prompt = f"""あなたは用語集作成の専門家です。
以下の分類済み用語から、用語集に掲載すべきものを選んでください。

## 分類済み用語（一般名詞は除外済み）:
{classification_text}

## 選定基準
この用語集は、ドキュメントの読者が文脈を理解するための補助として使われます。

1. 読者がこの用語の「この文脈での意味」を知りたいと思うか？
2. 辞書を引いても、この文脈での意味は分からないか？
3. 説明があると文章理解が深まるか？

## 採用しない例
- 広く知られた一般的な地名や国名（東京、日本など）
- 文脈に依存しない基本的な役職名（社長、部長など）

## 採用する例
- この作品/文脈特有の組織名、人名、地名
- 特殊な意味を持つ役職や称号
- 文脈特有の専門用語

## ドキュメントのコンテキスト:
{combined_content}

JSON形式で回答してください: {{"approved_terms": ["用語1", "用語2", ...]}}

用語集に掲載すべきものだけを選んで approved_terms に含めてください。"""

        return prompt
