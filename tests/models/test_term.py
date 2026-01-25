"""Tests for Term and TermOccurrence models."""

import pytest

from genglossary.models.term import ClassifiedTerm, Term, TermCategory, TermOccurrence


class TestTermOccurrence:
    """Test cases for TermOccurrence model."""

    def test_create_term_occurrence(self) -> None:
        """Test creating a TermOccurrence with all required fields."""
        occurrence = TermOccurrence(
            document_path="/path/to/file.txt",
            line_number=10,
            context="This is the context where the term appears.",
        )
        assert occurrence.document_path == "/path/to/file.txt"
        assert occurrence.line_number == 10
        assert occurrence.context == "This is the context where the term appears."

    def test_term_occurrence_line_number_positive(self) -> None:
        """Test that line_number must be positive."""
        with pytest.raises(ValueError):
            TermOccurrence(
                document_path="/path/to/file.txt",
                line_number=0,
                context="Context",
            )

    def test_term_occurrence_line_number_negative(self) -> None:
        """Test that line_number cannot be negative."""
        with pytest.raises(ValueError):
            TermOccurrence(
                document_path="/path/to/file.txt",
                line_number=-1,
                context="Context",
            )


class TestTerm:
    """Test cases for Term model."""

    def test_create_term_minimal(self) -> None:
        """Test creating a Term with minimal required fields."""
        term = Term(name="API")
        assert term.name == "API"
        assert term.definition == ""
        assert term.occurrences == []
        assert term.confidence == 0.0

    def test_create_term_full(self) -> None:
        """Test creating a Term with all fields."""
        occurrence = TermOccurrence(
            document_path="/path/to/file.txt",
            line_number=10,
            context="The API handles requests.",
        )
        term = Term(
            name="API",
            definition="Application Programming Interface",
            occurrences=[occurrence],
            confidence=0.85,
        )
        assert term.name == "API"
        assert term.definition == "Application Programming Interface"
        assert len(term.occurrences) == 1
        assert term.occurrences[0].line_number == 10
        assert term.confidence == 0.85

    def test_term_confidence_validation_min(self) -> None:
        """Test that confidence cannot be less than 0.0."""
        with pytest.raises(ValueError):
            Term(name="test", confidence=-0.1)

    def test_term_confidence_validation_max(self) -> None:
        """Test that confidence cannot be greater than 1.0."""
        with pytest.raises(ValueError):
            Term(name="test", confidence=1.1)

    def test_term_confidence_boundary_values(self) -> None:
        """Test confidence at boundary values (0.0 and 1.0)."""
        term_min = Term(name="test", confidence=0.0)
        assert term_min.confidence == 0.0

        term_max = Term(name="test", confidence=1.0)
        assert term_max.confidence == 1.0

    def test_term_add_occurrence(self) -> None:
        """Test adding an occurrence to a term."""
        term = Term(name="API")
        occurrence = TermOccurrence(
            document_path="/path/to/file.txt",
            line_number=5,
            context="Call the API here.",
        )
        term.add_occurrence(occurrence)
        assert len(term.occurrences) == 1
        assert term.occurrences[0].line_number == 5

    def test_term_add_multiple_occurrences(self) -> None:
        """Test adding multiple occurrences to a term."""
        term = Term(name="API")
        for i in range(1, 4):
            occurrence = TermOccurrence(
                document_path=f"/path/to/file{i}.txt",
                line_number=i * 10,
                context=f"Context {i}",
            )
            term.add_occurrence(occurrence)

        assert len(term.occurrences) == 3
        assert term.occurrences[0].line_number == 10
        assert term.occurrences[1].line_number == 20
        assert term.occurrences[2].line_number == 30

    def test_term_occurrence_count(self) -> None:
        """Test occurrence_count property."""
        term = Term(name="API")
        assert term.occurrence_count == 0

        for i in range(3):
            term.add_occurrence(
                TermOccurrence(
                    document_path="/path/to/file.txt",
                    line_number=i + 1,
                    context=f"Context {i}",
                )
            )
        assert term.occurrence_count == 3

    def test_term_name_not_empty(self) -> None:
        """Test that term name cannot be empty."""
        with pytest.raises(ValueError):
            Term(name="")

    def test_term_name_whitespace_stripped(self) -> None:
        """Test that term name is stripped of whitespace."""
        term = Term(name="  API  ")
        assert term.name == "API"


class TestClassifiedTerm:
    """Test cases for ClassifiedTerm model."""

    def test_create_classified_term(self) -> None:
        """Test creating a ClassifiedTerm with term and category."""
        classified = ClassifiedTerm(term="量子ビット", category=TermCategory.TECHNICAL_TERM)
        assert classified.term == "量子ビット"
        assert classified.category == TermCategory.TECHNICAL_TERM

    def test_create_classified_term_person_name(self) -> None:
        """Test creating a ClassifiedTerm with person_name category."""
        classified = ClassifiedTerm(term="太郎", category=TermCategory.PERSON_NAME)
        assert classified.term == "太郎"
        assert classified.category == TermCategory.PERSON_NAME

    def test_create_classified_term_common_noun(self) -> None:
        """Test creating a ClassifiedTerm with common_noun category."""
        classified = ClassifiedTerm(term="コンピュータ", category=TermCategory.COMMON_NOUN)
        assert classified.term == "コンピュータ"
        assert classified.category == TermCategory.COMMON_NOUN

    def test_classified_term_all_categories(self) -> None:
        """Test ClassifiedTerm accepts all TermCategory values."""
        categories = [
            TermCategory.PERSON_NAME,
            TermCategory.PLACE_NAME,
            TermCategory.ORGANIZATION,
            TermCategory.TITLE,
            TermCategory.TECHNICAL_TERM,
            TermCategory.COMMON_NOUN,
        ]
        for category in categories:
            classified = ClassifiedTerm(term="テスト", category=category)
            assert classified.category == category
