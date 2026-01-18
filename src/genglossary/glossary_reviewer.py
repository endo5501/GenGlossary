"""Glossary reviewer - Step 3: Review glossary for issues using LLM."""

from typing import Any

from pydantic import BaseModel, ValidationError

from genglossary.llm.base import BaseLLMClient
from genglossary.models.glossary import Glossary, GlossaryIssue, IssueType


class RawIssue(BaseModel):
    """Raw issue data from LLM response."""

    term: str
    issue_type: IssueType
    description: str
    should_exclude: bool = False
    exclusion_reason: str | None = None


class ReviewResponse(BaseModel):
    """Response model for glossary review."""

    issues: list[dict[str, Any]]


class GlossaryReviewer:
    """Reviews glossary for issues using LLM.

    This class handles the third step of the glossary generation pipeline:
    reviewing the glossary and identifying issues like unclear definitions,
    contradictions, or missing relationships.
    """

    def __init__(self, llm_client: BaseLLMClient) -> None:
        """Initialize the GlossaryReviewer.

        Args:
            llm_client: The LLM client to use for review.
        """
        self.llm_client = llm_client

    def review(self, glossary: Glossary) -> list[GlossaryIssue]:
        """Review the glossary and identify issues.

        Args:
            glossary: The glossary to review.

        Returns:
            A list of identified issues.
        """
        if glossary.term_count == 0:
            return []

        try:
            prompt = self._create_review_prompt(glossary)
            response = self.llm_client.generate_structured(prompt, ReviewResponse)
            return self._parse_issues(response.issues)
        except Exception as e:
            # If review fails, log warning and continue without issues
            print(f"Warning: Failed to review glossary: {e}")
            return []

    def _create_review_prompt(self, glossary: Glossary) -> str:
        """Create the prompt for glossary review.

        Args:
            glossary: The glossary to review.

        Returns:
            The formatted prompt string.
        """
        # Build term list with definitions and confidence
        term_lines: list[str] = []
        for term_name in glossary.all_term_names:
            term = glossary.get_term(term_name)
            if term is not None:
                confidence_pct = int(term.confidence * 100)
                term_lines.append(
                    f"- {term.name}: {term.definition} (信頼度: {confidence_pct}%)"
                )

        terms_text = "\n".join(term_lines)

        prompt = f"""以下の用語集を精査し、不明確な点や矛盾を特定してください。

用語集:
{terms_text}

## チェック観点

### 1. 定義の品質チェック
- 定義が曖昧または不完全な用語 (issue_type: "unclear")
- 複数の用語間で矛盾する説明 (issue_type: "contradiction")
- 関連用語の欠落や関係性の不明確さ (issue_type: "missing_relation")

### 2. 用語の必要性チェック（重要）

用語集は「この文書を読む人が、文脈での意味を理解するため」に存在します。
以下の条件に該当する用語は除外してください (issue_type: "unnecessary", should_exclude: true):

**除外基準（1つでも該当すれば除外）:**
1. 一般的な辞書で調べれば意味が分かり、この文書固有の特別な意味を持たない
2. 日常会話で普通に使われる語彙で、専門知識なしに理解できる
3. 複数の一般語を組み合わせただけで、組み合わせ自体に特別な意味がない

**重要: 迷った場合は除外してください。用語集は必要最小限が望ましいです。**

## Few-shot Examples

### 除外すべき用語の例
❌ **全力疾走** - 一般的な動作表現。辞書で分かる。
❌ **偵察** - 一般的な軍事用語。文脈固有の意味なし。
❌ **侵攻** - 一般的な軍事用語。辞書で分かる。
❌ **傭兵団** - 「傭兵」+「団」の単純な組み合わせ。
❌ **個人戦闘能力** - 各語の辞書的意味から理解可能。

### 用語集に含めるべき例
✅ **アソリウス島騎士団** - この作品固有の組織名。辞書には載っていない。
✅ **聖印** - この文脈で特別な意味を持つ概念。
✅ **魔神討伐** - この世界観特有の概念。単なる「討伐」とは異なる。

JSON形式で回答してください:
{{"issues": [{{"term": "用語名", "issue_type": "unclear|contradiction|missing_relation|unnecessary", "description": "問題の説明", "should_exclude": true/false, "exclusion_reason": "除外理由（should_exclude=trueの場合）"}}]}}

問題がない場合は空のリストを返してください: {{"issues": []}}"""

        return prompt

    def _parse_issues(self, raw_issues: list[dict[str, Any]]) -> list[GlossaryIssue]:
        """Parse raw issue data into GlossaryIssue objects.

        Args:
            raw_issues: List of raw issue dictionaries from LLM.

        Returns:
            List of validated GlossaryIssue objects.
        """
        issues: list[GlossaryIssue] = []

        for raw in raw_issues:
            try:
                validated = RawIssue(**raw)
                issue = GlossaryIssue(
                    term_name=validated.term,
                    issue_type=validated.issue_type,
                    description=validated.description,
                    should_exclude=validated.should_exclude,
                    exclusion_reason=validated.exclusion_reason,
                )
                issues.append(issue)
            except ValidationError:
                # Skip invalid issues
                continue

        return issues
