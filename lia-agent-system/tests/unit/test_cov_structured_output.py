"""Coverage tests for structured_output.py — pure utility functions for LLM schema conversion."""
import json
import pytest
from typing import Optional, List
from pydantic import BaseModel

from app.domains.ai.services.structured_output import (
    _get_json_type,
    pydantic_to_json_schema,
    pydantic_to_claude_tool,
    pydantic_to_gemini_schema,
    parse_json_from_text,
    StructuredOutputService,
)


# ── Sample Pydantic models for tests ────────────────────────────────────────

class SimplePydanticModel(BaseModel):
    name: str
    age: int
    score: float
    active: bool


class OptionalFieldsModel(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    count: Optional[int] = None


class NestedModel(BaseModel):
    id: str
    metadata: dict


# ── Tests for _get_json_type ─────────────────────────────────────────────────

class TestGetJsonType:
    def test_str_returns_string(self):
        assert _get_json_type(str) == "string"

    def test_int_returns_integer(self):
        assert _get_json_type(int) == "integer"

    def test_float_returns_number(self):
        assert _get_json_type(float) == "number"

    def test_bool_returns_boolean(self):
        assert _get_json_type(bool) == "boolean"

    def test_list_returns_array(self):
        assert _get_json_type(list) == "array"

    def test_dict_returns_object(self):
        assert _get_json_type(dict) == "object"

    def test_optional_str_returns_string(self):
        from typing import Optional
        assert _get_json_type(Optional[str]) == "string"

    def test_list_of_str_returns_array(self):
        from typing import List
        result = _get_json_type(List[str])
        assert result == "array"

    def test_unknown_type_returns_string(self):
        result = _get_json_type(object)
        assert result == "string"


# ── Tests for pydantic_to_json_schema ────────────────────────────────────────

class TestPydanticToJsonSchema:
    def test_returns_dict(self):
        result = pydantic_to_json_schema(SimplePydanticModel)
        assert isinstance(result, dict)

    def test_has_type_object(self):
        result = pydantic_to_json_schema(SimplePydanticModel)
        assert result.get("type") == "object"

    def test_has_properties(self):
        result = pydantic_to_json_schema(SimplePydanticModel)
        assert "properties" in result

    def test_name_field_is_string(self):
        result = pydantic_to_json_schema(SimplePydanticModel)
        assert result["properties"]["name"]["type"] == "string"

    def test_age_field_is_integer(self):
        result = pydantic_to_json_schema(SimplePydanticModel)
        assert result["properties"]["age"]["type"] == "integer"

    def test_score_field_is_number(self):
        result = pydantic_to_json_schema(SimplePydanticModel)
        assert result["properties"]["score"]["type"] == "number"

    def test_required_fields_listed(self):
        result = pydantic_to_json_schema(SimplePydanticModel)
        # SimplePydanticModel has all required fields
        required = result.get("required", [])
        assert "name" in required

    def test_optional_fields_model(self):
        result = pydantic_to_json_schema(OptionalFieldsModel)
        assert "properties" in result

    def test_nested_model_has_properties(self):
        result = pydantic_to_json_schema(NestedModel)
        assert "id" in result["properties"]


# ── Tests for pydantic_to_claude_tool ────────────────────────────────────────

class TestPydanticToClaudeTool:
    def test_returns_dict(self):
        result = pydantic_to_claude_tool(SimplePydanticModel)
        assert isinstance(result, dict)

    def test_has_name_key(self):
        result = pydantic_to_claude_tool(SimplePydanticModel)
        assert "name" in result

    def test_default_name_is_respond(self):
        result = pydantic_to_claude_tool(SimplePydanticModel)
        assert result["name"] == "respond"

    def test_custom_name(self):
        result = pydantic_to_claude_tool(SimplePydanticModel, tool_name="extract_info")
        assert result["name"] == "extract_info"

    def test_has_input_schema(self):
        result = pydantic_to_claude_tool(SimplePydanticModel)
        assert "input_schema" in result

    def test_input_schema_is_json_schema(self):
        result = pydantic_to_claude_tool(SimplePydanticModel)
        schema = result["input_schema"]
        assert schema.get("type") == "object"
        assert "properties" in schema


# ── Tests for pydantic_to_gemini_schema ─────────────────────────────────────

class TestPydanticToGeminiSchema:
    def test_returns_dict(self):
        result = pydantic_to_gemini_schema(SimplePydanticModel)
        assert isinstance(result, dict)

    def test_has_type(self):
        result = pydantic_to_gemini_schema(SimplePydanticModel)
        assert "type" in result


# ── Tests for parse_json_from_text ───────────────────────────────────────────

class TestParseJsonFromText:
    def test_extracts_json_from_code_block(self):
        text = '```json\n{"name": "Ana", "age": 30, "score": 8.5, "active": true}\n```'
        result = parse_json_from_text(text, SimplePydanticModel)
        assert result.name == "Ana"
        assert result.age == 30

    def test_extracts_json_from_plain_code_block(self):
        text = '```\n{"name": "Bruno", "age": 25, "score": 7.0, "active": false}\n```'
        result = parse_json_from_text(text, SimplePydanticModel)
        assert result.name == "Bruno"

    def test_extracts_bare_json_object(self):
        text = 'Here is the response: {"name": "Carlos", "age": 40, "score": 9.0, "active": true}'
        result = parse_json_from_text(text, SimplePydanticModel)
        assert result.name == "Carlos"

    def test_raises_value_error_on_invalid_text(self):
        with pytest.raises(ValueError):
            parse_json_from_text("This is just plain text with no JSON.", SimplePydanticModel)

    def test_raises_value_error_on_empty_string(self):
        with pytest.raises(ValueError):
            parse_json_from_text("", SimplePydanticModel)

    def test_raises_on_invalid_json_for_model(self):
        # Valid JSON but wrong schema for the model
        text = '{"wrong_field": "value"}'
        with pytest.raises(ValueError):
            parse_json_from_text(text, SimplePydanticModel)


# ── Tests for StructuredOutputService ────────────────────────────────────────

class TestStructuredOutputService:
    def setup_method(self):
        self.service = StructuredOutputService()

    def test_get_claude_tool_returns_dict(self):
        result = self.service.get_claude_tool(SimplePydanticModel)
        assert isinstance(result, dict)
        assert result["name"] == "respond"

    def test_get_claude_tool_cached(self):
        result1 = self.service.get_claude_tool(SimplePydanticModel)
        result2 = self.service.get_claude_tool(SimplePydanticModel)
        assert result1 is result2  # same object from cache

    def test_get_claude_tool_custom_name(self):
        result = self.service.get_claude_tool(SimplePydanticModel, tool_name="my_tool")
        assert result["name"] == "my_tool"

    def test_get_gemini_schema_returns_dict(self):
        result = self.service.get_gemini_schema(SimplePydanticModel)
        assert isinstance(result, dict)

    def test_get_gemini_schema_cached(self):
        result1 = self.service.get_gemini_schema(SimplePydanticModel)
        result2 = self.service.get_gemini_schema(SimplePydanticModel)
        assert result1 is result2  # same object from cache

    def test_fresh_service_has_empty_cache(self):
        svc = StructuredOutputService()
        assert svc._schema_cache == {}

    def test_cache_populated_after_call(self):
        svc = StructuredOutputService()
        svc.get_claude_tool(SimplePydanticModel)
        assert len(svc._schema_cache) == 1
