"""
Automation ReAct Agent — Task decomposition and planning via LangGraph nativo.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.

Domain: automation
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

from app.domains.automation.agents.automation_system_prompt import AUTOMATION_DOMAIN_SPECIFIC
from app.domains.automation.agents.automation_tool_registry import (
    get_automation_tools,
)
from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.services.confidence_policy_service import confidence_policy_service
from app.shared.prompts.prompt_composer import PromptComposer

logger = logging.getLogger(__name__)


@register_agent("automation")
class AutomationReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    # W4-032 (2026-05-23): automation rules disparam side-effects sem human-in-loop
    # por design — gate HITL aplica APENAS em activate/deactivate/destructive ops.
    _HITL_ACTION_TYPES = frozenset({
        "activate_automation",
        "deactivate_automation",
        "delete_automation",
        "bulk_trigger_automation",
        "schedule_recurring_task",
    })

    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="automation",
        domain_specific=AUTOMATION_DOMAIN_SPECIFIC,
    ).text

    """ReAct agent for task decomposition, DAG planning and execution orchestration."""

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_automation_tools()]
        self._setup_enhanced(domain="automation")
        logger.info("[AutomationReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "automation")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__['_domain_name_override'] = value


    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)


    
    def _get_runtime_domain_instructions(self, input: "AgentInput") -> str:  # type: ignore[override]
        """Phase 3.4: runtime compliance injection (LGPD/fairness/memory).

        Fixes the empty-placeholder defect (Audit G): static DOMAIN_INSTRUCTIONS
        bakes empty {memory_summary}/{stage_context} at class-load time.
        Sprint 2 Phase 4 canonical — see PromptComposer.for_domain_runtime.
        """
        try:
            ctx = input.context or {}
            return self._compose_runtime_prompt(
                input,
                agent_type="automation",
                domain_specific=AUTOMATION_DOMAIN_SPECIFIC,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[automation] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.automation.agents.automation_tool_registry import get_automation_tools
            return get_automation_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Todos os tools do domínio Automation (LangGraph usa set completo)."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_automation_tools() + self._get_all_enhanced_tools()
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
            response = "Planejamento concluído."

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

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """P36 Full: 3-layer intelligence injection."""
        try:
            weights = await self.load_calibration_weights(str(input.company_id or ""), input.context.get("job_id"))
            if weights and weights != self._DEFAULT_WEIGHTS:
                input.context["calibration_weights"] = weights
        except Exception:  # ADR-031-R3-EXEMPT: carregamento opcional de calibration weights; falha nao bloqueia agente
            pass
        try:
            from app.shared.services.global_insights_service import get_global_insights
            svc = get_global_insights()
            snippet = svc.format_automation_for_prompt(await svc.get_automation_insights())
            if snippet:
                existing = input.context.get("extra_instructions", "")
                input.context["extra_instructions"] = f"{existing}\n\n{snippet}" if existing else snippet
        except Exception:  # ADR-031-R3-EXEMPT: enriquecimento opcional de insights globais; falha nao bloqueia agente
            pass
        try:
            from app.domains.analytics.services.recruiter_personalization_service import get_recruiter_prompt_context
            ctx = await get_recruiter_prompt_context(str(input.user_id or ""), str(input.company_id or ""))
            if ctx:
                input.context["recruiter_context"] = ctx
        except Exception:  # ADR-031-R3-EXEMPT: carregamento opcional de contexto de recrutador; falha nao bloqueia agente
            pass
        return await super()._process_langgraph(input)

    async def process(self, input: AgentInput) -> AgentOutput:
        # W4-032 (2026-05-23): HITL gate em activate/deactivate/delete de automation
        from app.shared.hitl.agent_gate import maybe_request_hitl_approval
        _hitl_response = await maybe_request_hitl_approval(
            agent_input=input,
            domain=self.domain_name,
            action_types=self._HITL_ACTION_TYPES,
            agent_name="automation_react_agent",
            description_template=(
                "Confirmar **{action_type}** na regra de automação. "
                "Mudança afeta fluxos disparados automaticamente em produção."
            ),
        )
        if _hitl_response is not None:
            return _hitl_response

        return await self._process_langgraph(input)

    async def decompose_task(
        self,
        task_description: str,
        company_id: str | None = None,
        goal_id: str | None = None,
        parent_task_id: str | None = None,
        deadline: Any = None,
        persist: bool = True,
        additional_context: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Direct call for API endpoints — bypasses ReAct loop for deterministic results."""
        from app.domains.automation.agents.automation_tool_registry import _wrap_decompose_task
        return await _wrap_decompose_task(
            task_description=task_description,
            company_id=company_id,
            goal_id=goal_id,
            parent_task_id=parent_task_id,
            deadline=deadline,
            persist=persist,
            user_id=user_id,
        )

    async def prioritize_tasks(
        self,
        task_ids: list[str] | None = None,
        goal_id: str | None = None,
    ) -> dict[str, Any]:
        """Direct call for API endpoints — bypasses ReAct loop for deterministic results."""
        from app.domains.automation.agents.automation_tool_registry import _wrap_prioritize_tasks
        return await _wrap_prioritize_tasks(task_ids=task_ids or [], goal_id=goal_id)
