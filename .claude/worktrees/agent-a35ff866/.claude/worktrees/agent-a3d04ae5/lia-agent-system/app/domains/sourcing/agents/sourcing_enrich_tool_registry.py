"""
SourcingEnrichAgent Tool Registry — Z2-02.

Expõe tools das etapas profile-analysis e shortlist-creation:
análise de perfil, scoring WSI, comparação e shortlist.
"""
from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP
from app.shared.agents.react_loop import ToolDefinition
from typing import List

_ENRICH_TOOLS = [
    "analyze_profile",
    "compare_candidates",
    "score_candidate",
    "add_to_shortlist",
    "remove_from_shortlist",
    "rank_candidates",
    "generate_report",
]


def get_enrich_tools() -> List[ToolDefinition]:
    return [_TOOL_MAP[name] for name in _ENRICH_TOOLS if name in _TOOL_MAP]
