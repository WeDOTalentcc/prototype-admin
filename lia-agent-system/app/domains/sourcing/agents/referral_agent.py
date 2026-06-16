"""
ReferralAgent — Sub-agente de indicações via colaboradores internos.

Identifica colaboradores com perfil relevante para indicar candidatos,
prepara mensagens personalizadas via email ou WhatsApp, e solicita
aprovação HITL antes de qualquer envio.

HITL OBRIGATÓRIO:
- referral_send_request exige hitl_approved=True
- Nenhuma mensagem é enviada sem aprovação explícita do recrutador

INTEGRAÇÃO:
- CommunicationMatrix (WhatsApp + email) via RabbitMQ
- LGPD: não recolhe dados além do email do colaborador

Tools: referral_identify_connectors, referral_prepare_request,
       referral_send_request
"""
import logging

from app.domains.sourcing.agents.referral_tool_registry import get_referral_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.shared.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("sourcing_referral")  # W1-001 (2026-05-22)
class ReferralAgent(SourcingReActAgent):
    """
    Sub-agente de indicações por colaboradores internos.

    Identifica quem da empresa tem perfil próximo à vaga aberta,
    prepara rascunho de mensagem de solicitação de indicação e
    aguarda aprovação HITL antes do envio.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.info("[ReferralAgent] Initialized (tools=%d)", len(get_referral_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_referral"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_referral_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
