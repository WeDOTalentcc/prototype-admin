"""
SourcingPlannerAgent Tool Registry — Z2-02.

Expõe tools da etapa search-criteria: definição de critérios e sugestão de skills.
"""
from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP
from app.shared.agents.react_loop import ToolDefinition
from typing import List

_PLANNER_TOOLS = ["set_search_criteria", "suggest_skills"]


def get_planner_tools() -> List[ToolDefinition]:
    return [_TOOL_MAP[name] for name in _PLANNER_TOOLS if name in _TOOL_MAP]
