"""Tests for TermListResponseBase generic type."""

from pydantic import BaseModel

from genglossary.api.schemas.term_base_schemas import TermListResponseBase


class DummyItem(BaseModel):
    """Dummy item for testing generic type."""

    id: int
    name: str


class TestTermListResponseBaseGeneric:
    """Test that TermListResponseBase uses generic typing for items."""

    def test_items_field_accepts_generic_type_parameter(self) -> None:
        """TermListResponseBase[DummyItem] should enforce items as list[DummyItem]."""
        response = TermListResponseBase[DummyItem](
            items=[DummyItem(id=1, name="test")],
            total=1,
        )
        assert len(response.items) == 1
        assert isinstance(response.items[0], DummyItem)
        assert response.items[0].name == "test"

    def test_items_field_validates_type(self) -> None:
        """TermListResponseBase[DummyItem] should validate items type."""
        import pytest

        with pytest.raises(Exception):
            TermListResponseBase[DummyItem](
                items=[{"invalid": "data"}],
                total=1,
            )

    def test_openapi_schema_includes_item_type(self) -> None:
        """OpenAPI schema should reference the concrete item type."""
        schema = TermListResponseBase[DummyItem].model_json_schema()
        items_schema = schema["properties"]["items"]
        # Should reference DummyItem, not just "array"
        assert "items" in items_schema
        assert "$ref" in items_schema["items"] or "properties" in items_schema["items"]
