"""
Pipeline Action Tool Registry — Tools for candidate field mutations and interview management.

Subset of pipeline_tool_registry for PipelineActionAgent (6 tools).
Focus: update candidate fields, personalize communication, check rejection fairness,
       manage interview scheduling (details, cancel, reschedule).

check_rejection_fairness is MANDATORY in this registry (compliance).
"""

from lia_agents_core.react_loop import ToolDefinition

from app.domains.pipeline.agents.pipeline_tool_registry import _TOOL_MAP

_ACTION_TOOL_NAMES: list[str] = [
    "update_candidate_field",
    "personalize_communication",
    "check_rejection_fairness",   # FairnessGuard — obrigatório em agentes de ação
    "get_interview_details",
    "cancel_interview",
    "reschedule_interview",
]

GUARDRAIL_TOOLS: list[str] = [
    "update_candidate_field",
    "cancel_interview",
    "reschedule_interview",
]


def get_pipeline_action_tools() -> list[ToolDefinition]:
    """Return the 6 action tools for PipelineActionAgent."""
    return [_TOOL_MAP[name] for name in _ACTION_TOOL_NAMES if name in _TOOL_MAP]
