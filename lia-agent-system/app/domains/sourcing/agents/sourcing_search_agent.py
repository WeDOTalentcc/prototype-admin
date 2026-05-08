"""
SourcingSearchAgent — Z2-02.

Subagente especializado na etapa de busca de talentos (talent-search).
Responsabilidades: executar buscas, aplicar filtros e visualizar perfis.

Tools (3): search_candidates, filter_results, view_candidate
Modelo: Haiku (busca estruturada, sem raciocínio complexo)
"""
import logging

from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.domains.sourcing.agents.sourcing_search_tool_registry import get_search_tools

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("sourcing_search")
class SourcingSearchAgent(SourcingReActAgent):
    """Subagente de busca de candidatos — search, filter, view."""

    def __init__(self) -> None:
        super().__init__()
        logger.info("[SourcingSearchAgent] Initialized (tools=%d)", len(get_search_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_search"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_search_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
