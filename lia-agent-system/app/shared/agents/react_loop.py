"""Backwards-compatibility shim — migração LangGraph completa.

Re-exporta interfaces necessárias pelos tool registries, mixins e testes
que ainda importam deste módulo.
"""
from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool  # noqa: F401
from lia_agents_core.react_loop import ReActConfig, ReActState, ReActLoop  # noqa: F401

__all__ = [
    "ToolDefinition",
    "tool_definition_to_langchain_tool",
    "ReActConfig",
    "ReActState",
    "ReActLoop",
]
