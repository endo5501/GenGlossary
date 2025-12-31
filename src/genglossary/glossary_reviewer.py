"""Glossary reviewer - Step 3: Review glossary for issues using LLM."""

from genglossary.llm.base import BaseLLMClient
from genglossary.models.glossary import Glossary, GlossaryIssue


class GlossaryReviewer:
    """Reviews glossary for issues using LLM."""

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
        raise NotImplementedError("review not yet implemented")

    def _create_review_prompt(self, glossary: Glossary) -> str:
        """Create the prompt for glossary review.

        Args:
            glossary: The glossary to review.

        Returns:
            The formatted prompt string.
        """
        raise NotImplementedError("_create_review_prompt not yet implemented")

    def _parse_issues(self, raw_issues: list[dict[str, str]]) -> list[GlossaryIssue]:
        """Parse raw issue data into GlossaryIssue objects.

        Args:
            raw_issues: List of raw issue dictionaries from LLM.

        Returns:
            List of validated GlossaryIssue objects.
        """
        raise NotImplementedError("_parse_issues not yet implemented")
