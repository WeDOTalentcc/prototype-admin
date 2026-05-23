"""
NurtureSequenceAgent — Sub-agente de sequências automáticas multi-touch.

Gerencia sequências de até 5 touchpoints automáticos (email + WhatsApp + outros)
com controle HITL antes de cada step. Integra com lgpd_cleanup para expirar
sequências cujo TTL expirou ou onde o candidato fez opt-out.

HITL:
- Cada step requer aprovação antes do envio (communication_matrix.requires_approval)
- nurture_approve_step → nurture_execute_step

LGPD:
- Sequências expiram em 180 dias por padrão
- nurture_expire_sequence com reason=lgpd_cleanup é disparado pelo cleanup job
- Opt-out imediato disponível via reason=opt_out

CANAIS SUPORTADOS: email, whatsapp, linkedin_message, sms

Tools: nurture_create_sequence, nurture_get_sequence_status,
       nurture_approve_step, nurture_execute_step, nurture_expire_sequence
"""
import logging

from app.domains.sourcing.agents.nurture_sequence_tool_registry import get_nurture_sequence_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.shared.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("sourcing_nurture_sequence")  # W1-001 (2026-05-22)
class NurtureSequenceAgent(SourcingReActAgent):
    """
    Sub-agente de sequências de nurture multi-touch.

    Cria, gerencia e executa sequências automáticas de até 5 touchpoints
    para candidatos em fase de engajamento. Controle HITL por step e
    expiração LGPD automática.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.info("[NurtureSequenceAgent] Initialized (tools=%d)", len(get_nurture_sequence_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_nurture_sequence"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_nurture_sequence_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
