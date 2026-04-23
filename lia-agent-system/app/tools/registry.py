"""
Tool Registry — execution router, NOT an authoring surface.

This module owns the in-memory index that ``ActionExecutor``, ``agentic_loop``
and the orchestrator consult by name to obtain ``ToolDefinition.handler`` +
schema. It is **not** the place to author new tools.

Author tools with the ``@tool_handler`` decorator under
``app/domains/<domain>/tools/`` and expose them via ``get_<domain>_tools()``
in ``app/domains/<domain>/agents/<thing>_tool_registry.py``. The only file
allowed to call ``tool_registry.register(...)`` is
``app/tools/__init__.py:initialize_tools()``, which aggregates the
``get_*_tools()`` from each domain.

See ADR-016 (``docs/specs/ai/ADR-016-tool-registration-canonical.md``) and the
``S7.5`` guard (``scripts/check_tool_authoring_surface.py``).
"""
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by LLM agents."""
    name: str
    description: str
    parameters_schema: dict[str, Any]
    handler: Callable[..., Awaitable[dict[str, Any]]]
    allowed_agents: list[str] = field(default_factory=list)
    
    def to_claude_schema(self) -> dict[str, Any]:
        """Convert to Claude's tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters_schema
        }
    
    def to_gemini_schema(self) -> dict[str, Any]:
        """Convert to Gemini's function declaration format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema
        }


class ToolRegistry:
    """
    Central registry for all available tools.
    
    Manages tool registration, retrieval, and access control
    based on agent types.
    """
    
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register(self, tool: ToolDefinition) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: The tool definition to register
        """
        if tool.name in self._tools:
            self.logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        self._tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> ToolDefinition | None:
        """
        Get a tool by name.
        
        Args:
            name: The tool name
            
        Returns:
            The tool definition or None if not found
        """
        return self._tools.get(name)
    
    def get_tools_for_agent(self, agent_type: str) -> list[ToolDefinition]:
        """
        Get all tools available to a specific agent type.
        
        Args:
            agent_type: The agent type (e.g., "job_planner", "sourcing")
            
        Returns:
            List of tool definitions the agent can use
        """
        available_tools = []
        for tool in self._tools.values():
            if not tool.allowed_agents or agent_type in tool.allowed_agents:
                available_tools.append(tool)
        return available_tools
    
    def get_all_schemas(self, format: str = "claude") -> list[dict[str, Any]]:
        """
        Get all tool schemas in the specified format.
        
        Args:
            format: Either "claude" or "gemini"
            
        Returns:
            List of tool schemas
        """
        schemas = []
        for tool in self._tools.values():
            if format == "gemini":
                schemas.append(tool.to_gemini_schema())
            else:
                schemas.append(tool.to_claude_schema())
        return schemas
    
    def get_schemas_for_agent(
        self, 
        agent_type: str, 
        format: str = "claude"
    ) -> list[dict[str, Any]]:
        """
        Get tool schemas available to a specific agent.
        
        Args:
            agent_type: The agent type
            format: Either "claude" or "gemini"
            
        Returns:
            List of tool schemas
        """
        tools = self.get_tools_for_agent(agent_type)
        schemas = []
        for tool in tools:
            if format == "gemini":
                schemas.append(tool.to_gemini_schema())
            else:
                schemas.append(tool.to_claude_schema())
        return schemas
    
    def list_tools(self) -> list[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self.logger.info("Cleared all tools from registry")

    def export_to_yaml(self, path=None) -> str:
        """
        Serialize registry to YAML (Sprint G5).

        Args:
            path: optional pathlib.Path to write the file.

        Returns:
            YAML string representation of all registered tools.
        """
        from app.tools.tool_registry_loader import export_registry_to_yaml
        return export_registry_to_yaml(list(self._tools.values()), path=path)

    def validate_yaml(self, path=None) -> dict:
        """
        Validate registry against YAML metadata snapshot (Sprint G5).

        Returns:
            Validation report dict with ok, missing_in_yaml, missing_in_registry, etc.
        """
        from app.tools.tool_registry_loader import validate_registry_against_yaml
        return validate_registry_against_yaml(list(self._tools.values()), path=path)


tool_registry = ToolRegistry()
