"""
Structured Output Service for LLM responses.

Converts Pydantic model schemas to provider-specific formats and parses
LLM responses into validated Pydantic objects.

Supports:
- Claude: Tool calling with model schema as "respond" tool
- Gemini: response_schema parameter with JSON schema
"""
import json
import logging
from typing import Any, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _get_json_type(python_type: Any) -> str:
    """Convert Python type to JSON schema type."""
    origin = get_origin(python_type)
    
    if origin is Union:
        args = get_args(python_type)
        non_none_args = [a for a in args if a is not type(None)]
        if non_none_args:
            return _get_json_type(non_none_args[0])
        return "string"
    
    if origin is list:
        return "array"
    
    if origin is dict:
        return "object"
    
    if python_type is str:
        return "string"
    elif python_type is int:
        return "integer"
    elif python_type is float:
        return "number"
    elif python_type is bool:
        return "boolean"
    elif python_type is list or origin is list:
        return "array"
    elif python_type is dict or origin is dict:
        return "object"
    elif hasattr(python_type, "__origin__") and python_type.__origin__ is list:
        return "array"
    
    return "string"


def pydantic_to_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Convert a Pydantic model to JSON schema format.
    
    Args:
        model: The Pydantic model class
        
    Returns:
        JSON schema dictionary
    """
    try:
        schema = model.model_json_schema()
        
        if "$defs" in schema:
            defs = schema.pop("$defs")
            
            def resolve_refs(obj: Any) -> Any:
                if isinstance(obj, dict):
                    if "$ref" in obj:
                        ref_path = obj["$ref"]
                        if ref_path.startswith("#/$defs/"):
                            ref_name = ref_path[8:]
                            if ref_name in defs:
                                return resolve_refs(defs[ref_name])
                    return {k: resolve_refs(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [resolve_refs(item) for item in obj]
                return obj
            
            schema = resolve_refs(schema)
        
        return schema
    except Exception as e:
        logger.error(f"Error converting Pydantic model to JSON schema: {e}")
        raise


def pydantic_to_claude_tool(model: type[BaseModel], tool_name: str = "respond") -> dict[str, Any]:
    """
    Convert a Pydantic model to Claude's tool format.
    
    Uses the "respond" pattern where the model schema becomes the input
    schema for a tool that Claude must call to provide structured output.
    
    Args:
        model: The Pydantic model class
        tool_name: Name for the tool (default: "respond")
        
    Returns:
        Claude tool definition dictionary
    """
    schema = pydantic_to_json_schema(model)
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    return {
        "name": tool_name,
        "description": f"Use this tool to respond with structured data matching the {model.__name__} schema. You MUST use this tool to provide your response.",
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
    }


def pydantic_to_gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Convert a Pydantic model to Gemini's response_schema format.
    
    Gemini accepts standard JSON Schema format directly via the response_schema parameter.
    
    Args:
        model: The Pydantic model class
        
    Returns:
        JSON Schema dictionary compatible with Gemini's response_schema
    """
    return model.model_json_schema()


def parse_claude_tool_response(
    response: Any,
    model: type[T],
    tool_name: str = "respond"
) -> T:
    """
    Parse Claude's tool use response into a Pydantic model.
    
    Handles responses that may contain mixed content (text blocks + tool_use blocks).
    Prioritizes tool_use blocks but falls back to extracting JSON from text if needed.
    
    Args:
        response: The raw response from Claude API
        model: The Pydantic model class to parse into
        tool_name: Name of the tool used for structured output
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If parsing fails
    """
    try:
        tool_input = None
        text_parts = []
        
        if hasattr(response, 'content'):
            for block in response.content:
                if hasattr(block, 'type'):
                    if block.type == "tool_use":
                        if block.name == tool_name:
                            tool_input = block.input if isinstance(block.input, dict) else {}
                            break
                    elif block.type == "text":
                        text_parts.append(block.text if hasattr(block, 'text') else str(block))
        
        if tool_input is not None:
            logger.debug(f"Parsing Claude tool response: {json.dumps(tool_input, default=str)[:500]}")
            return model.model_validate(tool_input)
        
        if text_parts:
            combined_text = "".join(text_parts)
            logger.debug(f"No tool_use block found, attempting to extract JSON from text: {combined_text[:200]}")
            
            import re
            patterns = [
                r'```json\s*([\s\S]*?)\s*```',
                r'```\s*([\s\S]*?)\s*```',
                r'\{[\s\S]*\}'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, combined_text)
                for match in matches:
                    try:
                        data = json.loads(match)
                        return model.model_validate(data)
                    except (json.JSONDecodeError, ValidationError):
                        continue
        
        raise ValueError(f"No tool use found for '{tool_name}' and could not extract JSON from response text")
        
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {e}")
        raise ValueError(f"Response validation failed: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to parse Claude tool response: {e}")
        raise ValueError(f"Failed to parse structured response: {e}")


def parse_gemini_json_response(
    response: Any,
    model: type[T]
) -> T:
    """
    Parse Gemini's JSON response into a Pydantic model.
    
    Args:
        response: The raw response from Gemini API
        model: The Pydantic model class to parse into
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If parsing fails
    """
    try:
        text_content = ""
        if hasattr(response, 'text'):
            text_content = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        text_content += part.text
        
        if not text_content:
            raise ValueError("No text content in Gemini response")
        
        text_content = text_content.strip()
        if text_content.startswith("```json"):
            text_content = text_content[7:]
        if text_content.startswith("```"):
            text_content = text_content[3:]
        if text_content.endswith("```"):
            text_content = text_content[:-3]
        text_content = text_content.strip()
        
        logger.debug(f"Parsing Gemini JSON response: {text_content[:500]}")
        
        data = json.loads(text_content)
        
        return model.model_validate(data)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode failed: {e}, content: {text_content[:200]}")
        raise ValueError(f"Failed to parse JSON from response: {e}")
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {e}")
        raise ValueError(f"Response validation failed: {e}")
    except Exception as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        raise ValueError(f"Failed to parse structured response: {e}")


def parse_json_from_text(
    text: str,
    model: type[T]
) -> T:
    """
    Fallback parser to extract JSON from text response.
    
    Attempts to find and parse JSON embedded in text.
    
    Args:
        text: Text that may contain JSON
        model: The Pydantic model class to parse into
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If parsing fails
    """
    import re
    
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                data = json.loads(match)
                return model.model_validate(data)
            except (json.JSONDecodeError, ValidationError):
                continue
    
    raise ValueError("Could not extract valid JSON from text response")


class StructuredOutputService:
    """
    Service for generating structured outputs from LLMs.
    
    Handles schema conversion and response parsing for different providers.
    """
    
    def __init__(self):
        self._schema_cache: dict[str, dict[str, Any]] = {}
    
    def get_claude_tool(
        self,
        model: type[BaseModel],
        tool_name: str = "respond"
    ) -> dict[str, Any]:
        """Get Claude tool definition for a Pydantic model."""
        cache_key = f"claude_{model.__name__}_{tool_name}"
        if cache_key not in self._schema_cache:
            self._schema_cache[cache_key] = pydantic_to_claude_tool(model, tool_name)
        return self._schema_cache[cache_key]
    
    def get_gemini_schema(self, model: type[BaseModel]) -> dict[str, Any]:
        """Get Gemini response schema for a Pydantic model."""
        cache_key = f"gemini_{model.__name__}"
        if cache_key not in self._schema_cache:
            self._schema_cache[cache_key] = pydantic_to_gemini_schema(model)
        return self._schema_cache[cache_key]
    
    def parse_response(
        self,
        response: Any,
        model: type[T],
        provider: str,
        tool_name: str = "respond"
    ) -> T:
        """
        Parse LLM response into Pydantic model.
        
        Args:
            response: Raw LLM response
            model: Target Pydantic model class
            provider: LLM provider ("claude" or "gemini")
            tool_name: Tool name for Claude responses
            
        Returns:
            Validated Pydantic model instance
        """
        if provider == "claude":
            return parse_claude_tool_response(response, model, tool_name)
        elif provider == "gemini":
            return parse_gemini_json_response(response, model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


structured_output_service = StructuredOutputService()
