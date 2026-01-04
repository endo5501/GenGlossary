"""Glossary refiner - Step 4: Refine glossary based on issues using LLM."""

import re
from collections import defaultdict

from pydantic import BaseModel

from genglossary.llm.base import BaseLLMClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term


class RefinementResponse(BaseModel):
    """Response model for term refinement."""

    refined_definition: str
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
        refined_glossary = Glossary(
            terms=dict(glossary.terms),
            issues=list(glossary.issues),
            metadata=dict(glossary.metadata),
        )

        if not issues:
            return refined_glossary

        # Build context index once for all issues
        context_index = self._build_context_index(documents)
        resolved_count = 0

        for issue in issues:
            term = refined_glossary.get_term(issue.term_name)
            if term is None:
                continue

            try:
                refined_term = self._resolve_issue(term, issue, context_index)
                refined_glossary.terms[issue.term_name] = refined_term
                resolved_count += 1
            except Exception as e:
                print(f"Warning: Failed to refine '{issue.term_name}': {e}")

        refined_glossary.metadata["resolved_issues"] = resolved_count
        return refined_glossary

    def _build_context_index(
        self, documents: list[Document]
    ) -> dict[str, list[str]]:
        """Build an index mapping normalized terms to their context lines.

        This method processes all documents once to create a searchable index,
        avoiding O(n²) complexity when looking up contexts for multiple terms.

        Args:
            documents: List of documents to index.

        Returns:
            Dictionary mapping normalized term names to their context lines.
        """
        index: dict[str, list[str]] = defaultdict(list)

        for doc in documents:
            for line_num, line in enumerate(doc.lines, start=1):
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Store context with location for later retrieval
                context = f"- [{doc.file_path}:{line_num}] {line_stripped}"

                # Index by words in the line (normalized to lowercase)
                words = re.findall(r"\w+", line_stripped)
                for word in words:
                    index[word.lower()].append(context)

        return index

    def _resolve_issue(
        self,
        term: Term,
        issue: GlossaryIssue,
        context_index: dict[str, list[str]],
    ) -> Term:
        """Resolve a single issue for a term.

        Args:
            term: The term to refine.
            issue: The issue to resolve.
            context_index: Pre-built index of term contexts.

        Returns:
            A refined Term object.
        """
        prompt = self._create_refinement_prompt(term, issue, context_index)
        response = self.llm_client.generate_structured(prompt, RefinementResponse)

        return Term(
            name=term.name,
            definition=response.refined_definition,
            occurrences=term.occurrences,
            confidence=response.confidence,
        )

    def _create_refinement_prompt(
        self,
        term: Term,
        issue: GlossaryIssue,
        context_index: dict[str, list[str]],
    ) -> str:
        """Create the prompt for term refinement.

        Args:
            term: The term to refine.
            issue: The issue to address.
            context_index: Pre-built index of term contexts.

        Returns:
            The formatted prompt string.
        """
        additional_context = self._extract_context(term.name, context_index)

        return f"""用語: {term.name}
現在の定義: {term.definition}
問題点: {issue.description}
問題タイプ: {issue.issue_type}

追加コンテキスト:
{additional_context}

改善された定義を提供してください。問題点を解消し、より明確で具体的な定義を作成してください。

JSON形式で回答してください:
{{"refined_definition": "改善された定義", "confidence": 0.0-1.0}}"""

    def _extract_context(
        self, term_name: str, context_index: dict[str, list[str]]
    ) -> str:
        """Extract relevant context for a term from the pre-built index.

        Args:
            term_name: The term to find context for.
            context_index: Pre-built index of term contexts.

        Returns:
            Formatted context string.
        """
        # Search for contexts containing the term (case-insensitive)
        term_lower = term_name.lower()
        matching_contexts: list[str] = []

        # Check each word in the term name
        term_words = re.findall(r"\w+", term_name)
        for word in term_words:
            word_lower = word.lower()
            if word_lower in context_index:
                for context in context_index[word_lower]:
                    # Verify the full term appears in the context
                    if re.search(re.escape(term_name), context, re.IGNORECASE):
                        if context not in matching_contexts:
                            matching_contexts.append(context)

        if matching_contexts:
            return "\n".join(matching_contexts[:5])
        return "(追加のコンテキストはありません)"
