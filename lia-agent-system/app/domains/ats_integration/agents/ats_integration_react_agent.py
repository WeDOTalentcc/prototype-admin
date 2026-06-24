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
)
from app.domains.ats_integration.agents.ats_integration_tool_registry import (
    get_ats_integration_tools,
)
from app.shared.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer
from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS

@register_agent("ats_integration", aliases=['ats'])
class ATSIntegrationReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    # W4-032 (2026-05-23): ações com side-effect EXTERNO (write para Workday/
    # Greenhouse/etc) requerem aprovação humana inline via HITL.

    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="ats_integration",
        domain_specific=ATS_INTEGRATION_DOMAIN_SPECIFIC,
    ).text

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
                agent_type="ats_integration",
                domain_specific=ATS_INTEGRATION_DOMAIN_SPECIFIC,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[ats_integration] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
            return get_ats_integration_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Todos os tools do domínio ATS Integration (LangGraph usa set completo)."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_ats_integration_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

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

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """Override: injects 3-layer intelligence (P36 Full).

        Layer 1: Few-shot (via YAML prompt — already in system prompt)
        Layer 2: Tenant learning (CalibrationWeight + recruiter preferences)
        Layer 3: Global insights (anonymous cross-tenant ATS integration patterns)
        """
        # --- Camada 2: Tenant learning ---
        try:
            weights = await self.load_calibration_weights(
                company_id=str(input.company_id or ""),
                job_id=input.context.get("job_id"),
            )
            if weights and weights != self._DEFAULT_WEIGHTS:
                input.context["calibration_weights"] = weights
        except Exception as exc:
            logger.debug("[ATSIntegrationReAct] CalibrationWeight skipped: %s", exc)

        # --- Camada 3: Global ATS integration insights ---
        try:
            from app.shared.services.global_insights_service import get_global_insights
            insights_svc = get_global_insights()
            insights = await insights_svc.get_integration_insights()
            snippet = insights_svc.format_integration_for_prompt(insights)
            if snippet:
                existing = input.context.get("extra_instructions", "")
                input.context["extra_instructions"] = f"{existing}\n\n{snippet}" if existing else snippet
        except Exception as exc:
            logger.debug("[ATSIntegrationReAct] GlobalInsights skipped: %s", exc)

        # --- Camada 2: Recruiter personalization ---
        try:
            from app.domains.analytics.services.recruiter_personalization_service import get_recruiter_prompt_context
            recruiter_ctx = await get_recruiter_prompt_context(
                recruiter_id=str(input.user_id or ""),
                company_id=str(input.company_id or ""),
            )
            if recruiter_ctx:
                input.context["recruiter_context"] = recruiter_ctx
        except Exception as exc:
            logger.debug("[ATSIntegrationReAct] RecruiterPersonalization skipped: %s", exc)

        output = await super()._process_langgraph(input)

        # SEG-5: AuditService
        try:
            from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
            await audit_service.log_decision(
                company_id=str(input.company_id or ""),
                agent_name="ats_integration_react_agent",
                decision_type="ats_sync",
                action="ats_integration_langgraph",
                decision="completed",
                reasoning=["ATS integration via LangGraph native"],
                criteria_used=["ats_sync"],
                criteria_ignored=list(PROTECTED_CRITERIA),
                confidence=output.confidence,
            )
        except Exception as _ae:
            logger.debug("[ATSIntegrationReAct][SEG-5] AuditService skipped: %s", _ae)

        return output

    async def process(self, input: AgentInput) -> AgentOutput:
        # W4-032 (2026-05-23): HITL gate antes de side-effect externo ATS
        from app.shared.hitl.agent_gate import maybe_request_hitl_approval
        hitl_response = await maybe_request_hitl_approval(
            agent_input=input,
            domain=self.domain_name,
            action_types=HITL_REQUIRED_ACTIONS,
            agent_name="ats_integration_react_agent",
            description_template=(
                "Confirmar **{action_type}** no ATS externo. Write irreversível em sistema de terceiros."
            ),
        )
        if hitl_response is not None:
            return hitl_response

        try:
            return await self._process_langgraph(input)
        except Exception as exc:
            logger.error("[ATSIntegrationReActAgent] Unhandled error: %s", exc, exc_info=True)
            return AgentOutput(
                message="Erro ao processar integracao ATS. Tente novamente.",
                confidence=0.0,
                error=str(exc),
            )
