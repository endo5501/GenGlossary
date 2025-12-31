"""Glossary and GlossaryIssue models for representing the complete glossary."""

from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field, field_validator

from genglossary.models.term import Term


IssueType = Literal["unclear", "contradiction", "missing_relation"]


class GlossaryIssue(BaseModel):
    """Represents an issue found during glossary review.

    Attributes:
        term_name: The name of the term this issue relates to.
        issue_type: The type of issue (unclear, contradiction, missing_relation).
        description: A description of the issue.
    """

    term_name: str
    issue_type: IssueType
    description: str

    @field_validator("issue_type")
    @classmethod
    def validate_issue_type(cls, v: str) -> str:
        """Validate that issue_type is one of the allowed values."""
        valid_types = {"unclear", "contradiction", "missing_relation"}
        if v not in valid_types:
            raise ValueError(
                f"issue_type must be one of {valid_types}, got '{v}'"
            )
        return v


class Glossary(BaseModel):
    """Represents a complete glossary with terms and issues.

    Attributes:
        terms: Dictionary mapping term names to Term objects.
        issues: List of issues found during review.
        metadata: Additional metadata about the glossary.
    """

    terms: dict[str, Term] = Field(default_factory=dict)
    issues: list[GlossaryIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def term_count(self) -> int:
        """Return the number of terms in the glossary."""
        return len(self.terms)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def issue_count(self) -> int:
        """Return the number of issues in the glossary."""
        return len(self.issues)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_term_names(self) -> list[str]:
        """Return a list of all term names in the glossary."""
        return list(self.terms.keys())

    def add_term(self, term: Term) -> None:
        """Add a term to the glossary.

        If a term with the same name exists, it will be overwritten.

        Args:
            term: The Term object to add.
        """
        self.terms[term.name] = term

    def get_term(self, name: str) -> Term | None:
        """Get a term by name.

        Args:
            name: The term name to look up.

        Returns:
            The Term object if found, None otherwise.
        """
        return self.terms.get(name)

    def has_term(self, name: str) -> bool:
        """Check if a term exists in the glossary.

        Args:
            name: The term name to check.

        Returns:
            True if the term exists, False otherwise.
        """
        return name in self.terms

    def remove_term(self, name: str) -> bool:
        """Remove a term from the glossary.

        Args:
            name: The term name to remove.

        Returns:
            True if the term was removed, False if it didn't exist.
        """
        if name in self.terms:
            del self.terms[name]
            return True
        return False

    def add_issue(self, issue: GlossaryIssue) -> None:
        """Add an issue to the glossary.

        Args:
            issue: The GlossaryIssue object to add.
        """
        self.issues.append(issue)

    def get_issues_for_term(self, term_name: str) -> list[GlossaryIssue]:
        """Get all issues related to a specific term.

        Args:
            term_name: The term name to filter by.

        Returns:
            A list of issues for the specified term.
        """
        return [issue for issue in self.issues if issue.term_name == term_name]
