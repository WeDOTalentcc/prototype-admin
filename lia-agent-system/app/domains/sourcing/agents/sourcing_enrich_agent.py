"""
SourcingEnrichAgent — Z2-02.

Subagente especializado nas etapas de enriquecimento e shortlist
(profile-analysis + shortlist-creation).
Responsabilidades: análise de perfil, scoring WSI, comparação, shortlist e ranking.

Tools (7): analyze_profile, compare_candidates, score_candidate,
           add_to_shortlist, remove_from_shortlist, rank_candidates, generate_report
Modelo: Sonnet (análise e raciocínio mais complexos)
"""
import logging

from app.domains.sourcing.agents.sourcing_enrich_tool_registry import get_enrich_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("sourcing_enrich")
class SourcingEnrichAgent(SourcingReActAgent):
    """Subagente de enriquecimento — análise, scoring e shortlist."""

    def __init__(self) -> None:
        super().__init__()
        logger.info("[SourcingEnrichAgent] Initialized (tools=%d)", len(get_enrich_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_enrich"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_enrich_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
