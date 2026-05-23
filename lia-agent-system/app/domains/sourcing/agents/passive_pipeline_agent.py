"""
PassivePipelineAgent — Sub-agente de reativação de candidatos frios.

Consulta candidatos anteriores com status archived ou rejected_by_candidate,
recalcula score de fit para nova vaga e verifica TTL LGPD antes de reengajar.

CONFORMIDADE LGPD:
- TTL padrão: 2 anos (730 dias) desde último contato
- Candidatos fora do TTL não são exibidos sem novo consentimento
- Penalidade de recência no score de fit para candidatos inativos > 1 ano

Tools: passive_search_archived, passive_calculate_fit_score, passive_check_lgpd_ttl
"""
import logging

from app.domains.sourcing.agents.passive_pipeline_tool_registry import get_passive_pipeline_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.shared.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("sourcing_passive_pipeline")  # W1-001 (2026-05-22)
class PassivePipelineAgent(SourcingReActAgent):
    """
    Sub-agente de pipeline passivo — reativa candidatos frios.

    Busca candidatos com status archived/rejected_by_candidate, recalcula
    seu score de fit para novas vagas e verifica conformidade LGPD antes
    de iniciar qualquer reengajamento.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.info("[PassivePipelineAgent] Initialized (tools=%d)", len(get_passive_pipeline_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_passive_pipeline"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_passive_pipeline_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
