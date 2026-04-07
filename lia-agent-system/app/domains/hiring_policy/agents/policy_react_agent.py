"""
Policy ReAct Agent - Autonomous agent for hiring policy configuration.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.
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

from app.domains.hiring_policy.agents.policy_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
)
from app.domains.hiring_policy.agents.policy_system_prompt import get_policy_system_prompt
from app.domains.hiring_policy.agents.policy_tool_registry import get_policy_tools
from app.services.confidence_policy_service import confidence_policy_service
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "confirmo", "salva", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "positivo", "vamos",
    "avancar", "continua",
}


class PolicyReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """Autonomous agent for hiring policy configuration via LangGraph nativo."""

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._setup_enhanced(domain="policy")
        self._fairness_guard = FairnessGuard()
        self._all_tool_names = [t.name for t in get_policy_tools()]
        logger.info("[PolicyReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "policy")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__['_domain_name_override'] = value


    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    def _get_tools(self) -> list:
        """Todos os tools do domínio Policy (LangGraph usa set completo)."""
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_policy_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        current_stage = input.context.get("current_stage", "onboarding")
        policy_state = input.context.get("policy_state", {})
        stage_ctx = get_stage_context(current_stage, policy_state)
        return get_policy_system_prompt(
            stage=current_stage,
            context={"stage_context": stage_ctx, "memory_summary": ""},
        )

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Desculpe, não consegui processar sua solicitação."

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
        current_policy: Any = None,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Compatibility wrapper: builds AgentInput, calls process(), maps AgentOutput to legacy dict."""
        policy_state: dict[str, Any] = {}
        if current_policy is not None:
            try:
                policy_state = {
                    k: v for k, v in vars(current_policy).items()
                    if not k.startswith("_")
                } if hasattr(current_policy, "__dict__") else dict(current_policy)
            except Exception:
                pass

        agent_input = AgentInput(
            message=message,
            company_id=company_id,
            session_id=session_id,
            context={
                "policy_state": policy_state,
                "current_stage": policy_state.get("current_stage", "onboarding"),
            },
            conversation_history=conversation_history or [],
        )
        output = await self.process(agent_input)
        updated_fields: dict[str, Any] = {}
        for action in (output.actions or []):
            if action.action_type == "update_policy" and action.params:
                updated_fields.update(action.params)
        state_updates = output.state_updates or {}
        if state_updates:
            updated_fields.update(state_updates)
        return {
            "reply": output.message,
            "updated_fields": updated_fields,
            "answered_field": output.metadata.get("answered_field") if output.metadata else None,
            "current_block": output.metadata.get("current_block") if output.metadata else None,
            "current_question": output.metadata.get("current_question", 0) if output.metadata else 0,
            "total_questions": output.metadata.get("total_questions", 19) if output.metadata else 19,
            "setup_progress": output.metadata.get("setup_progress", 0) if output.metadata else 0,
            "block_completed": output.metadata.get("block_completed", False) if output.metadata else False,
            "all_completed": output.metadata.get("all_completed", False) if output.metadata else False,
            "compliance_blocked": output.metadata.get("fairness_blocked", False) if output.metadata else False,
        }

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
        }
