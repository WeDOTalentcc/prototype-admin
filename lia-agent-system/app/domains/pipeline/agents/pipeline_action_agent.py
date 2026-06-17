"""
Pipeline Action Agent — Subagent for candidate mutations and interview management.

Decomposes PipelineTransitionAgent (20 tools) into a focused subagent with 6 tools.
Handles: update_candidate_field, personalize_communication, check_rejection_fairness,
         get_interview_details, cancel_interview, reschedule_interview.

check_rejection_fairness is MANDATORY in this agent (FairnessGuard compliance).

Sprint Z1-02 — Tool decomposition to improve response quality and reduce cost.
"""
import logging

from app.domains.pipeline.agents.pipeline_action_tool_registry import (
    get_pipeline_action_tools,
)
from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("pipeline_action")
class PipelineActionAgent(PipelineTransitionAgent):
    """Action subagent for candidate field updates, communication and interview management.

    Provides access to 6 action tools. Inherits all HITL, fairness (including
    pre-process FairnessGuard), audit, LangGraph, and fallback behaviour from
    PipelineTransitionAgent.
    Overrides _get_tools() to limit the LLM to the action subset only.
    update_candidate_field, cancel_interview and reschedule_interview remain
    in GUARDRAIL_TOOLS — require recruiter confirmation before execution.
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_enhanced(domain="pipeline_action")
        logger.info("[PipelineActionAgent] Initialized — 6 action tools (3 guarded)")

    @property
    def domain_name(self) -> str:
        return "pipeline_action"

    def _get_tools(self) -> list:
        """Return only the 6 action tools for this subagent."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_pipeline_action_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
