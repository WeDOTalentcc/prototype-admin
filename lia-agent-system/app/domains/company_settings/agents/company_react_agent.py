"""
Company Settings ReAct Agent - Autonomous agent for company profile configuration.

Uses LangGraph native (create_react_agent) with PostgresSaver for persistence.
Handles company data, culture, tech stack, benefits, and workforce planning
via conversational interface.
"""
import logging
from typing import Any

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.company_settings.agents.company_system_prompt import (
    get_company_system_prompt,
    COMPANY_DOMAIN_SPECIFIC,
    COMPANY_FEW_SHOT_EXAMPLES,
    COMPANY_REASONING_PROMPT,
)
from app.domains.company_settings.agents.company_tool_registry import get_company_settings_tools
from app.shared.services.confidence_policy_service import confidence_policy_service
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)

from app.shared.agents.agent_registry import register_agent


@register_agent("company_settings")
class CompanySettingsReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = (
        COMPANY_DOMAIN_SPECIFIC + "\n\n" +
        COMPANY_FEW_SHOT_EXAMPLES + "\n\n" +
        COMPANY_REASONING_PROMPT.format(memory_summary="", stage_context="")
    )

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._setup_enhanced(domain="company_settings")
        self._fairness_guard = FairnessGuard()
        self._all_tool_names = [t.name for t in get_company_settings_tools()]
        logger.info("[CompanySettingsReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "company_settings")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__['_domain_name_override'] = value

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    def _get_tools(self) -> list:
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_company_settings_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Desculpe, nao consegui processar sua solicitacao."

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
        return await self._process_langgraph(input)

    async def process_legacy_format(
        self,
        message: str,
        company_id: str,
        session_id: str,
        current_data: Any = None,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        agent_input = AgentInput(
            message=message,
            company_id=company_id,
            session_id=session_id,
            context={
                "company_data": current_data or {},
            },
            conversation_history=conversation_history or [],
        )
        output = await self.process(agent_input)
        updated_fields: dict[str, Any] = {}
        for action in (output.actions or []):
            if action.action_type == "update_company" and action.params:
                updated_fields.update(action.params)
        state_updates = output.state_updates or {}
        if state_updates:
            updated_fields.update(state_updates)
        return {
            "reply": output.message,
            "updated_fields": updated_fields,
            "section": output.metadata.get("section") if output.metadata else None,
        }

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "max_iterations": 5,
            "model_provider": "claude",
        }
