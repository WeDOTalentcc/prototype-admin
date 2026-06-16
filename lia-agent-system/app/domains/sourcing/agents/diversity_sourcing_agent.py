"""
DiversitySourcingAgent — Sub-agente de sourcing afirmativo com FairnessGuard.

Aplica critérios afirmativos de diversidade na busca de candidatos,
priorizando (não excluindo) grupos subrepresentados dentro do pool qualificado.

Grupos suportados: PCD, mulheres, negros/pardos, LGBTQIA+, 50+, refugiados,
baixa renda / primeira geração.

CONFORMIDADE:
- FairnessGuard Layer 3 verificado em todas as buscas
- Four-Fifths Rule (FAR-4): nenhuma seleção adversa > 20% contra qualquer grupo
- Lei 8.213/91 (cotas PCD), Lei 9.029/95 (anti-discriminação), CF Art. 5º

Tools: diversity_search_candidates, diversity_get_pool_metrics, diversity_check_goals
"""
import logging

from app.domains.sourcing.agents.diversity_tool_registry import get_diversity_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.shared.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("sourcing_diversity")  # W1-001 (2026-05-22)
class DiversitySourcingAgent(SourcingReActAgent):
    """
    Sub-agente de sourcing com foco em diversidade e inclusão.

    Prioriza candidatos de grupos subrepresentados dentro do pool qualificado,
    sem penalizar candidatos fora das metas. Verifica métricas de diversidade
    e conformidade com Four-Fifths Rule.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.info("[DiversitySourcingAgent] Initialized (tools=%d)", len(get_diversity_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_diversity"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_diversity_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
