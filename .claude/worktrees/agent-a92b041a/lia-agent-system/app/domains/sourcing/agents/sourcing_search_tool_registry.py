"""
SourcingSearchAgent Tool Registry — Z2-02.

Expõe tools da etapa talent-search: busca, filtros e visualização de perfil.
"""
from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP
from app.shared.agents.react_loop import ToolDefinition
from typing import List

_SEARCH_TOOLS = ["search_candidates", "filter_results", "view_candidate"]


def get_search_tools() -> List[ToolDefinition]:
    return [_TOOL_MAP[name] for name in _SEARCH_TOOLS if name in _TOOL_MAP]
