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
    # P1-1 sentinel (2026-06-18): fail-fast if spec names missing from parent map
    missing = [n for n in _CONTEXT_TOOL_NAMES if n not in _TOOL_MAP]
    if missing:
        raise RuntimeError(
            f"[P1-1] {__name__}: tools {missing} absent from parent _TOOL_MAP. "
            "Implement in parent registry or remove from spec."
        )
    return [_TOOL_MAP[name] for name in _CONTEXT_TOOL_NAMES]
