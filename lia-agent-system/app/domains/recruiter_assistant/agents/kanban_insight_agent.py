"""
Kanban Insight Agent — Subagent for predictive analytics and pipeline intelligence.

Decomposes KanbanReActAgent (22 tools) into a focused subagent with 8 tools.
Handles: analyze_stage, identify_bottlenecks, get_candidate_aging, compare_stages,
         suggest_movements, get_journey_metrics, get_at_risk_candidates,
         get_pipeline_prediction.

Sprint Z1-01 — Tool decomposition to improve response quality and reduce cost.
"""
import logging

from app.domains.recruiter_assistant.agents.kanban_insight_tool_registry import (
    get_kanban_insight_tools,
)
from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("kanban_insight")
class KanbanInsightAgent(KanbanReActAgent):
    """Analytics subagent for bottleneck detection, aging reports and risk prediction.

    Provides access to 8 analytics/prediction tools. Inherits all memory,
    fairness, LangGraph, and fallback behaviour from KanbanReActAgent.
    Overrides _get_tools() to limit the LLM to the insight subset only.
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_enhanced(domain="kanban_insight")
        logger.info("[KanbanInsightAgent] Initialized — 8 insight tools")

    @property
    def domain_name(self) -> str:
        return "kanban_insight"

    def _get_tools(self) -> list:
        """Return only the 8 analytics/prediction tools for this subagent."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_kanban_insight_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
