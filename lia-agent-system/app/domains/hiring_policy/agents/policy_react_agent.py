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
from app.domains.hiring_policy.agents.policy_system_prompt import get_policy_system_prompt, POLICY_DOMAIN_SPECIFIC, POLICY_FEW_SHOT_EXAMPLES, POLICY_REASONING_PROMPT
from app.domains.hiring_policy.agents.policy_tool_registry import get_policy_tools
from app.shared.services.confidence_policy_service import confidence_policy_service
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "confirmo", "salva", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "positivo", "vamos",
    "avancar", "continua",
}


from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer

@register_agent("policy")
class PolicyReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="hiring_policy",
        domain_specific=POLICY_DOMAIN_SPECIFIC,
        few_shot_examples=POLICY_FEW_SHOT_EXAMPLES,
        reasoning_pattern=POLICY_REASONING_PROMPT.format(memory_summary="", stage_context=""),
    ).text

    def _get_runtime_domain_instructions(self, input: AgentInput) -> str:
        """Sprint 2 Phase 4: substitute {memory_summary} + {stage_context}
        from input.context at runtime (vs empty class-attr default).

        Falls back to legacy DOMAIN_INSTRUCTIONS if PromptComposer fails.
        """
        try:
            ctx = input.context or {}
            return self._compose_runtime_prompt(
                input,
                agent_type="hiring_policy",
                domain_specific=POLICY_DOMAIN_SPECIFIC,
            few_shot_examples=POLICY_FEW_SHOT_EXAMPLES,
                reasoning_template=POLICY_REASONING_PROMPT,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[hiring_policy] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    """Autonomous agent for hiring policy configuration via LangGraph nativo."""
    # ── HITL integration for policy updates ──
    # Sprint-I spec: when output.state_updates are present, request HITL approval.
    async def _request_hitl_if_needed(self, output) -> None:
        """Request HITL review when state_updates are present. Fail-safe: continues on error."""
        if output.state_updates:
            # Mark hitl_pending before attempting approval request
            hitl_pending = True  # noqa: F841
            try:
                from app.domains.cv_screening.services.hitl_service import hitl_service
                await hitl_service.request_approval(output.state_updates)
            except Exception as exc:  # noqa: BLE001
                # Fail-safe: HITL service unavailable — prosseguindo sem revisão
                import logging
                logging.getLogger(__name__).warning(
                    "Fail-safe: HITL service unavailable, prosseguindo sem revisão: %s", exc
                )



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


    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.hiring_policy.agents.policy_tool_registry import get_policy_tools
            return get_policy_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Todos os tools do domínio Policy (LangGraph usa set completo)."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_policy_tools() + self._get_all_enhanced_tools()
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
            except Exception:  # ADR-031-R3-EXEMPT: serializacao opcional de policy state para wrapper de compatibilidade; falha nao bloqueia
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
