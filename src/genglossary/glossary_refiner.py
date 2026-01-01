"""Glossary refiner - Step 4: Refine glossary based on issues using LLM."""

import re

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term


class RefinementResponse(BaseModel):
    """Response model for term refinement."""

    refined_definition: str
    related_terms: list[str]
    confidence: float


class GlossaryRefiner:
    """Refines glossary based on identified issues using LLM.

    This class handles the fourth step of the glossary generation pipeline:
    refining term definitions based on issues identified during review.
    """

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
        # Create a copy of the glossary to avoid modifying the original
        refined_glossary = Glossary(
            terms=dict(glossary.terms),
            issues=list(glossary.issues),
            metadata=dict(glossary.metadata),
        )

        if not issues:
            return refined_glossary

        resolved_count = 0

        for issue in issues:
            try:
                term = refined_glossary.get_term(issue.term_name)
                if term is None:
                    continue

                # Resolve the issue and get refined term
                refined_term = self._resolve_issue(term, issue, documents)

                # Update the glossary with the refined term
                refined_glossary.terms[issue.term_name] = refined_term
                resolved_count += 1
            except Exception as e:
                # Skip this issue and continue with the next one
                print(f"Warning: Failed to refine '{issue.term_name}': {e}")
                continue

        # Track resolved issues in metadata
        refined_glossary.metadata["resolved_issues"] = resolved_count

        return refined_glossary

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
        prompt = self._create_refinement_prompt(term, issue, documents)
        response = self.llm_client.generate_structured(prompt, RefinementResponse)

        # Create a new term with updated values
        refined_term = Term(
            name=term.name,
            definition=response.refined_definition,
            occurrences=term.occurrences,  # Preserve occurrences
            related_terms=list(set(term.related_terms + response.related_terms)),
            confidence=response.confidence,
        )

        return refined_term

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
        # Extract relevant context from documents
        additional_context = self._extract_context(term.name, documents)

        prompt = f"""用語: {term.name}
現在の定義: {term.definition}
問題点: {issue.description}
問題タイプ: {issue.issue_type}

追加コンテキスト:
{additional_context}

改善された定義を提供してください。問題点を解消し、より明確で具体的な定義を作成してください。

JSON形式で回答してください:
{{"refined_definition": "改善された定義", "related_terms": ["関連用語1", "関連用語2"], "confidence": 0.0-1.0}}"""

        return prompt

    def _extract_context(self, term_name: str, documents: list[Document]) -> str:
        """Extract relevant context for a term from documents.

        Args:
            term_name: The term to find context for.
            documents: List of documents to search.

        Returns:
            Formatted context string.
        """
        contexts: list[str] = []

        # Escape special regex characters
        escaped_term = re.escape(term_name)

        for doc in documents:
            for line_num, line in enumerate(doc.lines, start=1):
                if re.search(escaped_term, line, re.IGNORECASE):
                    contexts.append(f"- [{doc.file_path}:{line_num}] {line.strip()}")

        if contexts:
            return "\n".join(contexts[:5])  # Limit to 5 contexts
        else:
            return "(追加のコンテキストはありません)"
