"""
Kanban Action Agent — Subagent for pipeline mutations, communications and recruiter intelligence.

Decomposes KanbanReActAgent (22 tools) into a focused subagent with 8 tools.
Handles: batch_move_candidates, send_batch_communication, start_screening_batch,
         generate_pipeline_report, check_rejection_fairness, find_silver_medalists,
         get_recruiter_backlog, get_recruiter_benchmark.

check_rejection_fairness is MANDATORY in this agent (FairnessGuard compliance).

Sprint Z1-01 — Tool decomposition to improve response quality and reduce cost.
"""
import logging

from app.domains.recruiter_assistant.agents.kanban_action_tool_registry import (
    get_kanban_action_tools,
)
from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("kanban_action")
class KanbanActionAgent(KanbanReActAgent):
    """Action subagent for batch mutations, mass communications and fairness enforcement.

    Provides access to 8 action tools. Inherits all memory, HITL, fairness,
    LangGraph, and fallback behaviour from KanbanReActAgent.
    Overrides _get_tools() to limit the LLM to the action subset only.
    All destructive tools (batch_move, send_batch_communication,
    start_screening_batch) remain in GUARDRAIL_TOOLS — require confirmation.
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_enhanced(domain="kanban_action")
        logger.info("[KanbanActionAgent] Initialized — 8 action tools (3 guarded)")

    @property
    def domain_name(self) -> str:
        return "kanban_action"

    def _get_tools(self) -> list:
        """Return only the 8 action tools for this subagent."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_kanban_action_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
