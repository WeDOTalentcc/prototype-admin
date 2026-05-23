"""
StackOverflowSourcingAgent — Sub-agente para sourcing via Stack Exchange API.

Especializado na busca de especialistas técnicos por tag de tecnologia,
reputação mínima e localização. Integra FairnessGuard para buscas seguras.
Usa circuit breaker para resiliência em caso de falha da API externa.

Tools: so_search_experts, so_get_user_tags, so_get_user_answers
"""
import logging

from app.domains.sourcing.agents.stackoverflow_tool_registry import get_stackoverflow_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.shared.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("sourcing_stackoverflow")  # W1-001 (2026-05-22)
class StackOverflowSourcingAgent(SourcingReActAgent):
    """
    Sub-agente de sourcing via StackOverflow.

    Acessa perfis de especialistas técnicos por tag (ex: python, react,
    kubernetes), reputação mínima e localização. Obtém top tags de expertise
    e respostas de destaque para avaliar profundidade técnica.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.info("[StackOverflowSourcingAgent] Initialized (tools=%d)", len(get_stackoverflow_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_stackoverflow"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_stackoverflow_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
