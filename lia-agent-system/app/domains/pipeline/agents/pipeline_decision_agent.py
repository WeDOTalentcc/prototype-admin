"""
Pipeline Decision Agent — Subagent for transition decisions and preference management.

Decomposes PipelineTransitionAgent (20 tools) into a focused subagent with 7 tools.
Handles: validate_transition, suggest_sub_status, extract_preferences,
         request_data_collection, get_recruiter_preferences,
         save_recruiter_preference, schedule_secondary_task.

Sprint Z1-02 — Tool decomposition to improve response quality and reduce cost.
"""
import logging

from app.domains.pipeline.agents.pipeline_decision_tool_registry import (
    get_pipeline_decision_tools,
)
from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("pipeline_decision")
class PipelineDecisionAgent(PipelineTransitionAgent):
    """Decision subagent for validating transitions and managing recruiter preferences.

    Provides access to 7 decision/preference tools. Inherits all HITL,
    fairness, audit, LangGraph, and fallback behaviour from PipelineTransitionAgent.
    Overrides _get_tools() to limit the LLM to the decision subset only.
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_enhanced(domain="pipeline_decision")
        logger.info("[PipelineDecisionAgent] Initialized — 7 decision tools")

    @property
    def domain_name(self) -> str:
        return "pipeline_decision"

    def _get_tools(self) -> list:
        """Return only the 7 decision/preference tools for this subagent."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_pipeline_decision_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
