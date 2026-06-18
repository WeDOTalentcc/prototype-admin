"""
Kanban Insight Tool Registry — Tools for predictive analytics and pipeline intelligence.

Subset of kanban_tool_registry for KanbanInsightAgent (8 tools).
Focus: analysis, bottleneck detection, risk prediction, aging reports.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.recruiter_assistant.agents.kanban_tool_registry import _TOOL_MAP

_INSIGHT_TOOL_NAMES: list[str] = [
    "analyze_stage",
    "identify_bottlenecks",
    "get_candidate_aging",
    "compare_stages",
    "suggest_movements",
    "get_journey_metrics",
    "get_at_risk_candidates",
    "get_pipeline_prediction",
]


def get_kanban_insight_tools() -> list[ToolDefinition]:
    """Return the 8 analytics/prediction tools for KanbanInsightAgent."""
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
        missing = [n for n in _INSIGHT_TOOL_NAMES if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _INSIGHT_TOOL_NAMES]
