"""
Kanban ReAct Agent - Autonomous agent for strategic pipeline analysis.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.
"""
import logging

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    NavigationCommand,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.recruiter_assistant.agents.kanban_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
)
from app.domains.recruiter_assistant.agents.kanban_system_prompt import get_kanban_system_prompt, KANBAN_DOMAIN_SPECIFIC, KANBAN_FEW_SHOT_EXAMPLES, KANBAN_REASONING_PROMPT
from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
    get_kanban_tools,
)
from app.shared.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "confirmo", "mover", "avanca", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "positivo", "vamos",
}


from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer

@register_agent("kanban")
class KanbanReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    # W4-032 (2026-05-23): bulk operations + reject candidato exigem HITL.
    # Most-used recruiter surface, single point of side-effect concentration.
    _HITL_ACTION_TYPES = frozenset({
        "move_candidate",
        "bulk_move",
        "bulk_reject",
        "bulk_advance",
        "reject_candidate",
    })

    """Autonomous agent for strategic pipeline analysis via LangGraph nativo."""

    # Static class-attr (legacy backward compat — empty placeholders).
    # Runtime substitution via _get_runtime_domain_instructions below
    # (Sprint 2 Phase 4 — fixes Audit G empty-placeholder defect).
    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="kanban",
        domain_specific=KANBAN_DOMAIN_SPECIFIC,
        few_shot_examples=KANBAN_FEW_SHOT_EXAMPLES,
        reasoning_pattern=KANBAN_REASONING_PROMPT.format(memory_summary="", stage_context=""),
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
                agent_type="kanban",
                domain_specific=KANBAN_DOMAIN_SPECIFIC,
                few_shot_examples=KANBAN_FEW_SHOT_EXAMPLES,
                reasoning_template=KANBAN_REASONING_PROMPT,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[KanbanReActAgent] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_kanban_tools()]
        self._setup_enhanced(domain="kanban")
        logger.info("[KanbanReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "kanban")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__['_domain_name_override'] = value


    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)


    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.recruiter_assistant.agents.kanban_tool_registry import get_kanban_tools
            return get_kanban_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Todos os tools do domínio Kanban (LangGraph usa set completo)."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        from app.domains.recruiter_assistant.agents.ui_tool_registry import get_open_ui_tools
        # Grant UI: open_ui (modais/nav). apply_table_state NAO (surface kanban
        # sem ponte FE ainda -> evita ghost; entra em slice F2).
        tool_defs = get_kanban_tools() + get_open_ui_tools() + self._get_all_enhanced_tools()
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

        current_stage = input.context.get("current_stage", "pipeline_overview")
        collected_fields = input.context.get("collected_data", {})
        navigation = None
        try:
            stage_def = STAGE_DEFINITIONS.get(current_stage, {})
            next_stage = stage_def.get("next_stage", "")
            if next_stage and next_stage != "complete":
                criteria = stage_def.get("transition_criteria", {})
                required = criteria.get("required", [])
                missing = [f for f in required if collected_fields.get(f) in (None, "", [])]
                if not missing:
                    user_msgs = [
                        (m.content if hasattr(m, "content") else m.get("content", "")).lower()
                        for m in messages
                        if (getattr(m, "type", "") == "human" or (isinstance(m, dict) and m.get("role") == "user"))
                    ]
                    last_user = user_msgs[-1] if user_msgs else ""
                    if any(w in last_user for w in _CONFIRMATION_WORDS):
                        navigation = NavigationCommand(
                            target_stage=next_stage,
                            reason=criteria.get("description", "Critérios atendidos"),
                            auto_navigate=False,
                        )
        except Exception:
            pass

        _confidence = 0.75
        if actions:
            _confidence = 0.82
        if state.get("error"):
            _confidence = 0.40
        _conf_action = confidence_policy_service.get_action_for_confidence(_confidence)

        return AgentOutput(
            message=response,
            actions=actions,
            navigation=navigation,
            confidence=_confidence,
            metadata={
                "source": "langgraph_native",
                "domain": self.domain_name,
                "confidence_action": _conf_action.value,
            },
        )

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """P36 Full: 3-layer intelligence injection."""
        try:
            weights = await self.load_calibration_weights(str(input.company_id or ""), input.context.get("job_id"))
            if weights and weights != self._DEFAULT_WEIGHTS:
                input.context["calibration_weights"] = weights
        except Exception:
            pass
        try:
            from app.shared.services.global_insights_service import get_global_insights
            svc = get_global_insights()
            snippet = svc.format_kanban_for_prompt(await svc.get_kanban_insights())
            if snippet:
                existing = input.context.get("extra_instructions", "")
                input.context["extra_instructions"] = f"{existing}\n\n{snippet}" if existing else snippet
        except Exception:
            pass
        try:
            from app.domains.analytics.services.recruiter_personalization_service import get_recruiter_prompt_context
            ctx = await get_recruiter_prompt_context(str(input.user_id or ""), str(input.company_id or ""))
            if ctx:
                input.context["recruiter_context"] = ctx
        except Exception:
            pass
        return await super()._process_langgraph(input)

    async def process(self, input: AgentInput) -> AgentOutput:
        # W4-032 (2026-05-23): HITL gate antes de mover/rejeitar candidato
        from app.shared.hitl.agent_gate import maybe_request_hitl_approval
        hitl_response = await maybe_request_hitl_approval(
            agent_input=input,
            domain=self.domain_name,
            action_types=self._HITL_ACTION_TYPES,
            agent_name="kanban_react_agent",
            description_template=(
                "Confirmar **{action_type}** no kanban. "
                "Bulk operations afetam múltiplos candidatos."
            ),
        )
        if hitl_response is not None:
            return hitl_response

        _blocked_msg = await self._fairness_pre_check(input.message or "")
        if _blocked_msg:
            return AgentOutput(
                message=_blocked_msg,
                confidence=1.0,
                metadata={"source": "fairness_guard", "domain": self.domain_name},
            )
        return await self._process_langgraph(input)

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
        }
