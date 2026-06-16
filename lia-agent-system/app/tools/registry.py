"""
Tool Registry - Manages tool definitions for LLM function calling.

Provides a central registry for all tools that LLM agents can invoke,
including schema definitions and access control per agent type.
"""
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by LLM agents.

    W3-026 (2026-05-23): `version` field accepted via DI ou
    `tool_registry_metadata.yaml`. Default = "1.0". Phase A = field
    aceito + log na registration. Phase B (enforcement) defer.
    """
    name: str
    description: str
    parameters_schema: dict[str, Any]
    handler: Callable[..., Awaitable[dict[str, Any]]]
    allowed_agents: list[str] = field(default_factory=list)
    version: str = "1.0"  # W3-026 (2026-05-23): semver canonical do tool
    # Sprint 3 (2026-05-24): canonical category for capability discovery.
    # Auto-populated by ToolRegistry.register() via TOOL_TO_CATEGORY map.
    # Default OTHER → sensor J flags any new tool that hasn't been mapped.
    category: str = "OTHER"
    # HITL (AUD-4, 2026-06-06): tool sensivel exige aprovacao humana pre-flight.
    requires_confirmation: bool = False
    
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

        W3-026 (2026-05-23): logs tool.version pra observability +
        Phase B enforcement (detecta version drift entre registrations).
        """
        # W3-026 full enforcement: detect version drift se re-registro
        # ocorrer com versão diferente da já cadastrada (deveria ser intencional).
        existing = self._tools.get(tool.name)
        if existing is not None and existing.version != tool.version:
            self.logger.warning(
                "[ToolRegistry W3-026] version drift detected for tool %s: "
                "registered=%s, new=%s. Mantendo new — verificar se intencional.",
                tool.name, existing.version, tool.version,
            )
        if tool.name in self._tools:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            self.logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        # Sprint 3 (2026-05-24): populate canonical category at register time.
        # Source of truth: app/tools/categories.TOOL_TO_CATEGORY.
        # Defaults to "OTHER" if name unmapped — sensor J blocks PRs that add
        # new tools to OTHER without updating the canonical map.
        if tool.category == "OTHER":
            try:
                from app.tools.categories import category_for_tool
                tool.category = category_for_tool(tool.name)
            except Exception as _cat_exc:
                # Fail-loud in log; tool remains in OTHER which sensor J catches
                self.logger.warning(
                    "[ToolRegistry] failed to resolve category for %s: %s",
                    tool.name, _cat_exc,
                )
        self._tools[tool.name] = tool
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Registered tool: {tool.name} (category={tool.category})")
    
    def get_tools_by_category(self) -> dict[str, list[ToolDefinition]]:
        """Sprint 3 (2026-05-24): group all registered tools by canonical category.

        Used by SystemPromptBuilder._build_capabilities_section to render the
        G6 capabilities prompt dynamically — replaces the previous hardcoded
        list. Single source of truth: app/tools/categories.TOOL_TO_CATEGORY.

        Returns:
            dict mapping category name (str) → list of ToolDefinition,
            sorted by tool name within each category for deterministic output.
        """
        from collections import defaultdict
        groups: dict[str, list[ToolDefinition]] = defaultdict(list)
        for tool in self._tools.values():
            groups[tool.category].append(tool)
        for cat in groups:
            groups[cat].sort(key=lambda t: t.name)
        return dict(groups)

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
