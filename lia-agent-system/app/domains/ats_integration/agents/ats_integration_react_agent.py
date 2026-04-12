"""
ATS Integration ReAct Agent — Bidirectional ATS sync via LangGraph nativo.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.

Domain: ats_integration
"""
import logging

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.ats_integration.agents.ats_integration_system_prompt import (
    ATS_INTEGRATION_DOMAIN_SPECIFIC,
    get_ats_integration_system_prompt,
)
from app.domains.ats_integration.agents.ats_integration_tool_registry import (
    get_ats_integration_tools,
)
from app.shared.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)


class ATSIntegrationReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = ATS_INTEGRATION_DOMAIN_SPECIFIC

    """ReAct agent for bidirectional ATS synchronization via LangGraph nativo.

    Supports Gupy, Pandapé and Merge providers.
    """

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_ats_integration_tools()]
        self._setup_enhanced(domain="ats_integration")
        logger.info("[ATSIntegrationReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "ats_integration")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__['_domain_name_override'] = value


    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    def _get_tools(self) -> list:
        """Todos os tools do domínio ATS Integration (LangGraph usa set completo)."""
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_ats_integration_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    # Legacy method — preserved for rollback
    def _get_system_prompt_legacy(self, input: AgentInput) -> str:
        return get_ats_integration_system_prompt()

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            if content and not getattr(m, "tool_call_id", None) and not (
                isinstance(m, dict) and m.get("tool_call_id")
            ):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Sincronização com ATS processada."

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        _confidence = 0.75
        if actions:
            _confidence = 0.82
        if state.get("error"):
            _confidence = 0.40
        _conf_action = confidence_policy_service.get_action_for_confidence(_confidence)

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=_confidence,
            metadata={
                "source": "langgraph_native",
                "domain": self.domain_name,
                "confidence_action": _conf_action.value,
            },
        )

    async def process(self, input: AgentInput) -> AgentOutput:
        try:
            return await self._process_langgraph(input)
        except Exception as exc:
            logger.error(f"[ATSIntegrationReActAgent] Unhandled error: {exc}", exc_info=True)
            return AgentOutput(
                message="Erro ao processar integração ATS. Tente novamente.",
                confidence=0.0,
                error=str(exc),
            )
