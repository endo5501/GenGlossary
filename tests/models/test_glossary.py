"""Tests for Glossary and GlossaryIssue models."""

import pytest

from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term, TermOccurrence


class TestGlossaryIssue:
    """Test cases for GlossaryIssue model."""

    def test_create_glossary_issue(self) -> None:
        """Test creating a GlossaryIssue with all fields."""
        issue = GlossaryIssue(
            term_name="API",
            issue_type="unclear",
            description="Definition is vague and needs more context.",
        )
        assert issue.term_name == "API"
        assert issue.issue_type == "unclear"
        assert issue.description == "Definition is vague and needs more context."

    def test_glossary_issue_types(self) -> None:
        """Test valid issue types."""
        valid_types = ["unclear", "contradiction", "missing_relation"]
        for issue_type in valid_types:
            issue = GlossaryIssue(
                term_name="test",
                issue_type=issue_type,
                description="Test description",
            )
            assert issue.issue_type == issue_type

    def test_glossary_issue_invalid_type(self) -> None:
        """Test that invalid issue type raises error."""
        with pytest.raises(ValueError):
            GlossaryIssue(
                term_name="test",
                issue_type="invalid_type",
                description="Test description",
            )

    def test_glossary_issue_unnecessary_type(self) -> None:
        """Test that 'unnecessary' is a valid issue type."""
        issue = GlossaryIssue(
            term_name="一般語",
            issue_type="unnecessary",
            description="一般的な語彙のため不要",
        )
        assert issue.issue_type == "unnecessary"

    def test_glossary_issue_should_exclude_default_false(self) -> None:
        """Test that should_exclude defaults to False."""
        issue = GlossaryIssue(
            term_name="test",
            issue_type="unclear",
            description="Test description",
        )
        assert issue.should_exclude is False
        assert issue.exclusion_reason is None

    def test_glossary_issue_should_exclude_true(self) -> None:
        """Test creating issue with should_exclude=True."""
        issue = GlossaryIssue(
            term_name="一般語",
            issue_type="unnecessary",
            description="一般的な語彙のため不要",
            should_exclude=True,
            exclusion_reason="辞書的な意味で十分理解できる",
        )
        assert issue.should_exclude is True
        assert issue.exclusion_reason == "辞書的な意味で十分理解できる"

    def test_glossary_issue_exclusion_reason_optional(self) -> None:
        """Test that exclusion_reason is optional."""
        issue = GlossaryIssue(
            term_name="test",
            issue_type="unnecessary",
            description="Test",
            should_exclude=True,
        )
        assert issue.exclusion_reason is None


class TestGlossary:
    """Test cases for Glossary model."""

    def test_create_glossary_empty(self) -> None:
        """Test creating an empty Glossary."""
        glossary = Glossary()
        assert glossary.terms == {}
        assert glossary.issues == []
        assert glossary.metadata == {}

    def test_create_glossary_with_metadata(self) -> None:
        """Test creating a Glossary with metadata."""
        glossary = Glossary(metadata={"source": "test_docs", "version": "1.0"})
        assert glossary.metadata["source"] == "test_docs"
        assert glossary.metadata["version"] == "1.0"

    def test_add_term(self) -> None:
        """Test adding a term to the glossary."""
        glossary = Glossary()
        term = Term(name="API", definition="Application Programming Interface")
        glossary.add_term(term)

        assert "API" in glossary.terms
        assert glossary.terms["API"].definition == "Application Programming Interface"

    def test_add_term_overwrite(self) -> None:
        """Test that adding a term with same name overwrites."""
        glossary = Glossary()
        term1 = Term(name="API", definition="First definition")
        term2 = Term(name="API", definition="Second definition")

        glossary.add_term(term1)
        glossary.add_term(term2)

        assert glossary.terms["API"].definition == "Second definition"

    def test_get_term_existing(self) -> None:
        """Test getting an existing term."""
        glossary = Glossary()
        term = Term(name="API", definition="Application Programming Interface")
        glossary.add_term(term)

        retrieved = glossary.get_term("API")
        assert retrieved is not None
        assert retrieved.name == "API"
        assert retrieved.definition == "Application Programming Interface"

    def test_get_term_not_found(self) -> None:
        """Test getting a non-existing term returns None."""
        glossary = Glossary()
        assert glossary.get_term("NonExistent") is None

    def test_has_term(self) -> None:
        """Test checking if term exists."""
        glossary = Glossary()
        term = Term(name="API", definition="Application Programming Interface")
        glossary.add_term(term)

        assert glossary.has_term("API") is True
        assert glossary.has_term("NonExistent") is False

    def test_add_issue(self) -> None:
        """Test adding an issue to the glossary."""
        glossary = Glossary()
        issue = GlossaryIssue(
            term_name="API",
            issue_type="unclear",
            description="Needs more context.",
        )
        glossary.add_issue(issue)

        assert len(glossary.issues) == 1
        assert glossary.issues[0].term_name == "API"

    def test_add_multiple_issues(self) -> None:
        """Test adding multiple issues."""
        glossary = Glossary()
        issues = [
            GlossaryIssue(
                term_name="API", issue_type="unclear", description="Issue 1"
            ),
            GlossaryIssue(
                term_name="REST", issue_type="contradiction", description="Issue 2"
            ),
            GlossaryIssue(
                term_name="API",
                issue_type="missing_relation",
                description="Issue 3",
            ),
        ]
        for issue in issues:
            glossary.add_issue(issue)

        assert len(glossary.issues) == 3

    def test_get_issues_for_term(self) -> None:
        """Test getting all issues for a specific term."""
        glossary = Glossary()
        glossary.add_issue(
            GlossaryIssue(term_name="API", issue_type="unclear", description="Issue 1")
        )
        glossary.add_issue(
            GlossaryIssue(
                term_name="REST", issue_type="contradiction", description="Issue 2"
            )
        )
        glossary.add_issue(
            GlossaryIssue(
                term_name="API", issue_type="missing_relation", description="Issue 3"
            )
        )

        api_issues = glossary.get_issues_for_term("API")
        assert len(api_issues) == 2
        assert all(issue.term_name == "API" for issue in api_issues)

    def test_term_count(self) -> None:
        """Test term_count property."""
        glossary = Glossary()
        assert glossary.term_count == 0

        glossary.add_term(Term(name="API"))
        glossary.add_term(Term(name="REST"))
        assert glossary.term_count == 2

    def test_issue_count(self) -> None:
        """Test issue_count property."""
        glossary = Glossary()
        assert glossary.issue_count == 0

        glossary.add_issue(
            GlossaryIssue(term_name="API", issue_type="unclear", description="Test")
        )
        glossary.add_issue(
            GlossaryIssue(
                term_name="REST", issue_type="contradiction", description="Test"
            )
        )
        assert glossary.issue_count == 2

    def test_all_term_names(self) -> None:
        """Test getting all term names."""
        glossary = Glossary()
        glossary.add_term(Term(name="API"))
        glossary.add_term(Term(name="REST"))
        glossary.add_term(Term(name="HTTP"))

        names = glossary.all_term_names
        assert set(names) == {"API", "REST", "HTTP"}

    def test_remove_term(self) -> None:
        """Test removing a term."""
        glossary = Glossary()
        glossary.add_term(Term(name="API"))
        glossary.add_term(Term(name="REST"))

        removed = glossary.remove_term("API")
        assert removed is True
        assert "API" not in glossary.terms
        assert "REST" in glossary.terms

    def test_remove_term_not_found(self) -> None:
        """Test removing a non-existing term returns False."""
        glossary = Glossary()
        removed = glossary.remove_term("NonExistent")
        assert removed is False
