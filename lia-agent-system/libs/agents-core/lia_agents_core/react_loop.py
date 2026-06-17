"""
react_loop.py — Shim de compatibilidade pós-migração LangGraph.

O ReActLoop customizado foi removido em favor do create_react_agent nativo do LangGraph.
Este módulo re-exporta interfaces ainda referenciadas por código existente
(tool registries, enhanced_agent_mixin, learning_extractor, testes).

Para novos agentes, use:
    from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool
    from lia_agents_core.langgraph_react_base import LangGraphReActBase
"""
from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool, ReActState, ReActConfig  # noqa: F401

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ReActLoop:
    """Stub de compatibilidade — o ReActLoop real foi removido.

    Instanciar este stub levanta NotImplementedError com instrução de migração.
    Mantido apenas para que imports não quebrem em testes de contrato.
    """

    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError(
            "ReActLoop foi removido. Use LangGraphReActBase com create_react_agent. "
            "Veja libs/agents-core/lia_agents_core/langgraph_react_base.py"
        )

__all__ = [
    "ToolDefinition",
    "tool_definition_to_langchain_tool",
    "ReActState",
    "ReActConfig",
    "ReActLoop",
]
