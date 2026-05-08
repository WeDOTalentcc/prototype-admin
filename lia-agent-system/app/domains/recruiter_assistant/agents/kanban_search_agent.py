"""
Kanban Search Agent — Subagent for candidate and pipeline data queries.

Decomposes KanbanReActAgent (22 tools) into a focused subagent with 6 tools.
Handles: view_candidate_full_profile, list_stage_candidates, get_pipeline_summary,
         get_stage_metrics, get_pipeline_benchmarks, get_pipeline_velocity.

Sprint Z1-01 — Tool decomposition to improve response quality and reduce cost.
"""
import logging

from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
from app.domains.recruiter_assistant.agents.kanban_search_tool_registry import (
    get_kanban_search_tools,
)

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("kanban_search")
class KanbanSearchAgent(KanbanReActAgent):
    """Read-only subagent for candidate queries and pipeline state retrieval.

    Provides access to 6 focused search/query tools. Inherits all memory,
    fairness, LangGraph, and fallback behaviour from KanbanReActAgent.
    Overrides _get_tools() to limit the LLM to the search subset only.
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_enhanced(domain="kanban_search")
        logger.info("[KanbanSearchAgent] Initialized — 6 search tools")

    @property
    def domain_name(self) -> str:
        return "kanban_search"

    def _get_tools(self) -> list:
        """Return only the 6 search/query tools for this subagent."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_kanban_search_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
