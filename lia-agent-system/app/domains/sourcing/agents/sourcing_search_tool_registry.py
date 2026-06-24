"""
SourcingSearchAgent Tool Registry — Z2-02.

Expõe tools da etapa talent-search: busca, filtros e visualização de perfil.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP

_SEARCH_TOOLS = ["search_candidates", "filter_results", "view_candidate"]


def get_search_tools() -> list[ToolDefinition]:
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
    missing = [n for n in _SEARCH_TOOLS if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _SEARCH_TOOLS]
