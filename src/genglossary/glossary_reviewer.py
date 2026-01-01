"""Glossary reviewer - Step 3: Review glossary for issues using LLM."""

from typing import Any

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.glossary import Glossary, GlossaryIssue, IssueType


class ReviewResponse(BaseModel):
    """Response model for glossary review."""

    issues: list[dict[str, str]]


class GlossaryReviewer:
    """Reviews glossary for issues using LLM.

    This class handles the third step of the glossary generation pipeline:
    reviewing the glossary and identifying issues like unclear definitions,
    contradictions, or missing relationships.
    """

    VALID_ISSUE_TYPES: set[str] = {"unclear", "contradiction", "missing_relation"}

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

チェック観点:
1. 定義が曖昧または不完全な用語 (issue_type: "unclear")
2. 複数の用語間で矛盾する説明 (issue_type: "contradiction")
3. 関連用語の欠落や関係性の不明確さ (issue_type: "missing_relation")
4. 定義が実際の使用例と一致していない箇所

JSON形式で回答してください:
{{"issues": [{{"term": "用語名", "issue_type": "unclear|contradiction|missing_relation", "description": "問題の説明"}}]}}

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
            # Check required fields
            if not all(key in raw for key in ["term", "issue_type", "description"]):
                continue

            term_name = raw.get("term", "")
            issue_type = raw.get("issue_type", "")
            description = raw.get("description", "")

            # Validate issue type
            if issue_type not in self.VALID_ISSUE_TYPES:
                continue

            # Create GlossaryIssue
            issue = GlossaryIssue(
                term_name=term_name,
                issue_type=issue_type,  # type: ignore[arg-type]
                description=description,
            )
            issues.append(issue)

        return issues
