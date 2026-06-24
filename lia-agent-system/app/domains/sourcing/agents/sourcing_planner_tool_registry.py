"""
SourcingPlannerAgent Tool Registry — Z2-02.

Expõe tools da etapa search-criteria: definição de critérios e sugestão de skills.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP

_PLANNER_TOOLS = ["set_search_criteria", "suggest_skills"]


def get_planner_tools() -> list[ToolDefinition]:
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
    missing = [n for n in _PLANNER_TOOLS if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _PLANNER_TOOLS]
