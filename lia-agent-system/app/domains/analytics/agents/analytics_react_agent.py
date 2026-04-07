"""
Analytics ReAct Agent — KPI analysis, reports and hiring predictions via LangGraph nativo.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.

Domain: analytics
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

from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
from app.domains.analytics.agents.analytics_tool_registry import (
    get_analytics_tools,
)
from app.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)


class AnalyticsReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """ReAct agent for analytics: KPI analysis, reports, predictions and agent monitoring."""

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_analytics_tools()]
        self._setup_enhanced(domain="analytics")
        logger.info("[AnalyticsReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "analytics")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__['_domain_name_override'] = value


    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    def _get_tools(self) -> list:
        """Todos os tools do domínio Analytics (LangGraph usa set completo)."""
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_analytics_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        return get_analytics_system_prompt()

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
            response = "Análise concluída."

        actions = []
        for m in messages:
            for tc in getattr(m, "tool_calls", None) or []:
                name = (
                    tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                )
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
            logger.error(f"[AnalyticsReActAgent] Unhandled error: {exc}", exc_info=True)
            return AgentOutput(
                message="Erro ao processar análise. Tente novamente.",
                confidence=0.0,
                error=str(exc),
            )
