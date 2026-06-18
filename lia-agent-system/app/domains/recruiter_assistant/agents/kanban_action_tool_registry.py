"""
Kanban Action Tool Registry — Tools for pipeline actions, fairness and recruiter intelligence.

Subset of kanban_tool_registry for KanbanActionAgent (8 tools).
Focus: batch mutations, communications, fairness check, recruiter metrics.
check_rejection_fairness is MANDATORY in this registry (compliance).
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.recruiter_assistant.agents.kanban_tool_registry import _TOOL_MAP
from app.shared.compliance.safety_category import SafetyCategory

_ACTION_TOOL_NAMES: list[str] = [
    "batch_move_candidates",
    "send_batch_communication",
    "start_screening_batch",
    "generate_pipeline_report",
    "check_rejection_fairness",   # FairnessGuard — obrigatório em agentes de ação
    "find_silver_medalists",
    "get_recruiter_backlog",
    "get_recruiter_benchmark",
]

GUARDRAIL_TOOLS: dict[str, SafetyCategory] = {
    "batch_move_candidates": SafetyCategory.BULK_ACTION,
    "send_batch_communication": SafetyCategory.OUTREACH,
    "start_screening_batch": SafetyCategory.BULK_ACTION,
}


def get_kanban_action_tools() -> list[ToolDefinition]:
    """Return the 8 action tools for KanbanActionAgent."""
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
        missing = [n for n in _ACTION_TOOL_NAMES if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _ACTION_TOOL_NAMES]
