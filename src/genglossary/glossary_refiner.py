"""Glossary refiner - Step 4: Refine glossary based on issues using LLM."""

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term


class GlossaryRefiner:
    """Refines glossary based on identified issues using LLM."""

    def __init__(self, llm_client: BaseLLMClient) -> None:
        """Initialize the GlossaryRefiner.

        Args:
            llm_client: The LLM client to use for refinement.
        """
        self.llm_client = llm_client

    def refine(
        self,
        glossary: Glossary,
        issues: list[GlossaryIssue],
        documents: list[Document],
    ) -> Glossary:
        """Refine the glossary based on identified issues.

        Args:
            glossary: The glossary to refine.
            issues: List of issues to address.
            documents: List of documents for additional context.

        Returns:
            A refined Glossary object.
        """
        raise NotImplementedError("refine not yet implemented")

    def _resolve_issue(
        self,
        term: Term,
        issue: GlossaryIssue,
        documents: list[Document],
    ) -> Term:
        """Resolve a single issue for a term.

        Args:
            term: The term to refine.
            issue: The issue to resolve.
            documents: List of documents for additional context.

        Returns:
            A refined Term object.
        """
        raise NotImplementedError("_resolve_issue not yet implemented")

    def _create_refinement_prompt(
        self,
        term: Term,
        issue: GlossaryIssue,
        documents: list[Document],
    ) -> str:
        """Create the prompt for term refinement.

        Args:
            term: The term to refine.
            issue: The issue to address.
            documents: List of documents for additional context.

        Returns:
            The formatted prompt string.
        """
        raise NotImplementedError("_create_refinement_prompt not yet implemented")
