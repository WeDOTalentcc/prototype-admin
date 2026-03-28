"""
Kanban Action Tool Registry — Tools for pipeline actions, fairness and recruiter intelligence.

Subset of kanban_tool_registry for KanbanActionAgent (8 tools).
Focus: batch mutations, communications, fairness check, recruiter metrics.
check_rejection_fairness is MANDATORY in this registry (compliance).
"""
from typing import List

from app.shared.agents.react_loop import ToolDefinition
from app.domains.recruiter_assistant.agents.kanban_tool_registry import _TOOL_MAP

_ACTION_TOOL_NAMES: List[str] = [
    "batch_move_candidates",
    "send_batch_communication",
    "start_screening_batch",
    "generate_pipeline_report",
    "check_rejection_fairness",   # FairnessGuard — obrigatório em agentes de ação
    "find_silver_medalists",
    "get_recruiter_backlog",
    "get_recruiter_benchmark",
]

GUARDRAIL_TOOLS: List[str] = [
    "batch_move_candidates",
    "send_batch_communication",
    "start_screening_batch",
]


def get_kanban_action_tools() -> List[ToolDefinition]:
    """Return the 8 action tools for KanbanActionAgent."""
    return [_TOOL_MAP[name] for name in _ACTION_TOOL_NAMES if name in _TOOL_MAP]
