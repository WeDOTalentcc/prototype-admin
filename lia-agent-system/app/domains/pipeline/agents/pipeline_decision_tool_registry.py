"""
Pipeline Decision Tool Registry — Tools for transition decisions and preference management.

Subset of pipeline_tool_registry for PipelineDecisionAgent (7 tools).
Focus: validate transitions, suggest sub-statuses, extract preferences,
       request data collection, manage recruiter preferences.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.pipeline.agents.pipeline_tool_registry import _TOOL_MAP

_DECISION_TOOL_NAMES: list[str] = [
    "validate_transition",
    "suggest_sub_status",
    "extract_preferences",
    "request_data_collection",
    "get_recruiter_preferences",
    "save_recruiter_preference",
    "schedule_secondary_task",
]


def get_pipeline_decision_tools() -> list[ToolDefinition]:
    """Return the 7 decision/preference tools for PipelineDecisionAgent."""
    return [_TOOL_MAP[name] for name in _DECISION_TOOL_NAMES if name in _TOOL_MAP]
