"""
Pipeline Action Tool Registry — Tools for candidate field mutations and interview management.

Subset of pipeline_tool_registry for PipelineActionAgent (6 tools).
Focus: update candidate fields, personalize communication, check rejection fairness,
       manage interview scheduling (details, cancel, reschedule).

check_rejection_fairness is MANDATORY in this registry (compliance).
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.pipeline.agents.pipeline_tool_registry import _TOOL_MAP
from app.shared.compliance.safety_category import SafetyCategory

_ACTION_TOOL_NAMES: list[str] = [
    "update_candidate_field",
    "personalize_communication",
    "check_rejection_fairness",   # FairnessGuard — obrigatório em agentes de ação
    "get_interview_details",
    "cancel_interview",
    "reschedule_interview",
]

GUARDRAIL_TOOLS: dict[str, SafetyCategory] = {
    "update_candidate_field": SafetyCategory.DESTRUCTIVE_WRITE,
    "cancel_interview": SafetyCategory.DESTRUCTIVE_WRITE,
    "reschedule_interview": SafetyCategory.DESTRUCTIVE_WRITE,
}


def get_pipeline_action_tools() -> list[ToolDefinition]:
    """Return the 6 action tools for PipelineActionAgent."""
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
    missing = [n for n in _ACTION_TOOL_NAMES if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _ACTION_TOOL_NAMES]
