"""
SourcingEngagementAgent — Z2-02.

Subagente especializado na etapa de abordagem (outreach).
Responsabilidades: gerar mensagens personalizadas, enviar abordagens (com HITL)
e rastrear respostas.

Tools (3): send_outreach (GUARDRAIL/HITL), generate_message, track_response
Modelo: Sonnet (personalização de mensagens requer qualidade)
"""
import logging

from app.domains.sourcing.agents.sourcing_engagement_tool_registry import (
    GUARDRAIL_TOOLS,
    get_engagement_tools,
)
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent

@register_agent("sourcing_engagement")
class SourcingEngagementAgent(SourcingReActAgent):
    """Subagente de engajamento — outreach com HITL, geração e rastreamento."""

    # AUD-4: tools que requerem aprovação HITL antes de executar
    _GUARDRAIL_TOOLS = GUARDRAIL_TOOLS

    def __init__(self) -> None:
        super().__init__()
        logger.info(
            "[SourcingEngagementAgent] Initialized (tools=%d, guardrails=%s)",
            len(get_engagement_tools()),
            self._GUARDRAIL_TOOLS,
        )

    @property
    def domain_name(self) -> str:
        return "sourcing_engagement"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_engagement_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
