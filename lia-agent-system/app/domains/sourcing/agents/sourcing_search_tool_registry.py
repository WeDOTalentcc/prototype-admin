"""
SourcingSearchAgent Tool Registry — Z2-02.

Expõe tools da etapa talent-search: busca, filtros e visualização de perfil.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP

_SEARCH_TOOLS = ["search_candidates", "filter_results", "view_candidate"]


def get_search_tools() -> list[ToolDefinition]:
    return [_TOOL_MAP[name] for name in _SEARCH_TOOLS if name in _TOOL_MAP]
