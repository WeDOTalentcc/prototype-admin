"""
Pipeline Context Agent — Subagent for reading candidate and job data.

Decomposes PipelineTransitionAgent (20 tools) into a focused subagent with 7 tools.
Handles: get_candidate_profile, get_candidate_wsi_scores, get_candidate_screening_results,
         get_candidate_salary_info, get_job_context, get_stage_sub_statuses,
         check_candidate_availability.

Sprint Z1-02 — Tool decomposition to improve response quality and reduce cost.
"""
import logging

from app.domains.pipeline.agents.pipeline_context_tool_registry import (
    get_pipeline_context_tools,
)
from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("pipeline_context")
class PipelineContextAgent(PipelineTransitionAgent):
    """Read-only subagent for candidate profiles, scores, salary and job context.

    Provides access to 7 focused context/query tools. Inherits all HITL,
    fairness, audit, LangGraph, and fallback behaviour from PipelineTransitionAgent.
    Overrides _get_tools() to limit the LLM to the context subset only.
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_enhanced(domain="pipeline_context")
        logger.info("[PipelineContextAgent] Initialized — 7 context tools")

    @property
    def domain_name(self) -> str:
        return "pipeline_context"

    def _get_tools(self) -> list:
        """Return only the 7 read-only context tools for this subagent."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_pipeline_context_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
