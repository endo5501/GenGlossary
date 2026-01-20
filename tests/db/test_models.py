"""Tests for database model serialization."""

import json

from genglossary.db.models import deserialize_occurrences, serialize_occurrences
from genglossary.models.term import TermOccurrence


class TestSerializeOccurrences:
    """Test serialize_occurrences function."""

    def test_serialize_empty_list(self) -> None:
        """Test serializing an empty occurrence list."""
        occurrences: list[TermOccurrence] = []

        result = serialize_occurrences(occurrences)

        assert result == "[]"
        assert json.loads(result) == []

    def test_serialize_single_occurrence(self) -> None:
        """Test serializing a single occurrence."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=42, context="Context text"
            )
        ]

        result = serialize_occurrences(occurrences)

        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["document_path"] == "/path/to/doc.txt"
        assert data[0]["line_number"] == 42
        assert data[0]["context"] == "Context text"

    def test_serialize_multiple_occurrences(self) -> None:
        """Test serializing multiple occurrences."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=1, context="First"
            ),
            TermOccurrence(
                document_path="/path/to/doc.txt", line_number=10, context="Second"
            ),
            TermOccurrence(
                document_path="/path/to/other.txt", line_number=5, context="Third"
            ),
        ]

        result = serialize_occurrences(occurrences)

        data = json.loads(result)
        assert len(data) == 3
        assert data[0]["line_number"] == 1
        assert data[1]["line_number"] == 10
        assert data[2]["document_path"] == "/path/to/other.txt"

    def test_serialize_preserves_unicode(self) -> None:
        """Test that serialization preserves Unicode characters."""
        occurrences = [
            TermOccurrence(
                document_path="/path/to/doc.txt",
                line_number=1,
                context="量子コンピュータは量子力学の原理を利用する",
            )
        ]

        result = serialize_occurrences(occurrences)

        data = json.loads(result)
        assert "量子コンピュータ" in data[0]["context"]


class TestDeserializeOccurrences:
    """Test deserialize_occurrences function."""

    def test_deserialize_empty_json(self) -> None:
        """Test deserializing an empty JSON array."""
        json_str = "[]"

        result = deserialize_occurrences(json_str)

        assert result == []

    def test_deserialize_single_occurrence(self) -> None:
        """Test deserializing a single occurrence."""
        json_str = json.dumps(
            [
                {
                    "document_path": "/path/to/doc.txt",
                    "line_number": 42,
                    "context": "Context text",
                }
            ]
        )

        result = deserialize_occurrences(json_str)

        assert len(result) == 1
        assert isinstance(result[0], TermOccurrence)
        assert result[0].document_path == "/path/to/doc.txt"
        assert result[0].line_number == 42
        assert result[0].context == "Context text"

    def test_deserialize_multiple_occurrences(self) -> None:
        """Test deserializing multiple occurrences."""
        json_str = json.dumps(
            [
                {
                    "document_path": "/path/to/doc.txt",
                    "line_number": 1,
                    "context": "First",
                },
                {
                    "document_path": "/path/to/doc.txt",
                    "line_number": 10,
                    "context": "Second",
                },
            ]
        )

        result = deserialize_occurrences(json_str)

        assert len(result) == 2
        assert result[0].line_number == 1
        assert result[1].line_number == 10

    def test_deserialize_preserves_unicode(self) -> None:
        """Test that deserialization preserves Unicode characters."""
        json_str = json.dumps(
            [
                {
                    "document_path": "/path/to/doc.txt",
                    "line_number": 1,
                    "context": "量子コンピュータは量子力学の原理を利用する",
                }
            ]
        )

        result = deserialize_occurrences(json_str)

        assert len(result) == 1
        assert "量子コンピュータ" in result[0].context

    def test_deserialize_validates_schema(self) -> None:
        """Test that deserialization validates against TermOccurrence schema."""
        # Missing required field
        invalid_json = json.dumps(
            [{"document_path": "/path/to/doc.txt", "context": "Missing line_number"}]
        )

        try:
            deserialize_occurrences(invalid_json)
            assert False, "Should have raised validation error"
        except Exception as e:
            # Pydantic raises ValidationError
            assert "validation" in str(type(e)).lower()


class TestRoundTrip:
    """Test serialization and deserialization round trips."""

    def test_roundtrip_preserves_data(self) -> None:
        """Test that serialization followed by deserialization preserves data."""
        original = [
            TermOccurrence(
                document_path="/path/to/doc.txt",
                line_number=1,
                context="量子コンピュータ",
            ),
            TermOccurrence(
                document_path="/path/to/other.txt",
                line_number=42,
                context="Another occurrence",
            ),
        ]

        # Serialize then deserialize
        json_str = serialize_occurrences(original)
        result = deserialize_occurrences(json_str)

        # Check equality
        assert len(result) == len(original)
        for orig, res in zip(original, result):
            assert res.document_path == orig.document_path
            assert res.line_number == orig.line_number
            assert res.context == orig.context
