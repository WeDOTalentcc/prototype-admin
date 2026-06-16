"""
Pipeline Context Tool Registry — Tools for reading candidate and job data.

Subset of pipeline_tool_registry for PipelineContextAgent (7 tools).
Focus: read-only queries on candidate profiles, scores, salary and job context.
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.pipeline.agents.pipeline_tool_registry import _TOOL_MAP

_CONTEXT_TOOL_NAMES: list[str] = [
    "get_candidate_profile",
    "get_candidate_wsi_scores",
    "get_candidate_screening_results",
    "get_candidate_salary_info",
    "get_job_context",
    "get_stage_sub_statuses",
    "check_candidate_availability",
]


def get_pipeline_context_tools() -> list[ToolDefinition]:
    """Return the 7 read-only context tools for PipelineContextAgent."""
    return [_TOOL_MAP[name] for name in _CONTEXT_TOOL_NAMES if name in _TOOL_MAP]
