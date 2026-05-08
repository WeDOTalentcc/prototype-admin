"""
SourcingPlannerAgent — Z2-02.

Subagente especializado na etapa de planejamento da busca (search-criteria).
Responsabilidades: definir critérios de busca e sugerir skills relevantes.

Tools (2): set_search_criteria, suggest_skills
Modelo: Haiku (baixo custo — tarefa simples e estruturada)
"""
import logging

from app.domains.sourcing.agents.sourcing_planner_tool_registry import get_planner_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("sourcing_planner")
class SourcingPlannerAgent(SourcingReActAgent):
    """Subagente de planejamento de sourcing — define critérios e sugere skills."""

    def __init__(self) -> None:
        super().__init__()
        logger.info("[SourcingPlannerAgent] Initialized (tools=%d)", len(get_planner_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_planner"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_planner_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
