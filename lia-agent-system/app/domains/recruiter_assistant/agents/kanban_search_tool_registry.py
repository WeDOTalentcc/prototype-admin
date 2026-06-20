"""
Kanban Search Tool Registry — Tools for candidate and pipeline data queries.

Subset of kanban_tool_registry for KanbanSearchAgent (6 tools).
Focus: read-only queries on candidates and pipeline state.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.recruiter_assistant.agents.kanban_tool_registry import _TOOL_MAP

_SEARCH_TOOL_NAMES: list[str] = [
    "view_candidate_full_profile",
    "list_stage_candidates",
    "get_pipeline_summary",
    "get_stage_metrics",
    "get_pipeline_benchmarks",
    "get_pipeline_velocity",
]


def get_kanban_search_tools() -> list[ToolDefinition]:
    """Return the 6 read-only search/query tools for KanbanSearchAgent."""
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
    missing = [n for n in _SEARCH_TOOL_NAMES if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _SEARCH_TOOL_NAMES]
