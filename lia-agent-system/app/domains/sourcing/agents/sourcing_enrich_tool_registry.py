"""
SourcingEnrichAgent Tool Registry — Z2-02.

Expõe tools das etapas profile-analysis e shortlist-creation:
análise de perfil, scoring WSI, comparação e shortlist.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP

_ENRICH_TOOLS = [
    "analyze_profile",
    "compare_candidates",
    "score_candidate",
    "add_to_shortlist",
    "remove_from_shortlist",
    "rank_candidates",
    "generate_report",
]


def get_enrich_tools() -> list[ToolDefinition]:
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
    missing = [n for n in _ENRICH_TOOLS if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _ENRICH_TOOLS]
