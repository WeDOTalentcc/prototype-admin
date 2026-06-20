"""
Communication ReAct Agent — Multi-channel candidate communication orchestration.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.

Domain: communication
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

from app.domains.communication.agents.communication_system_prompt import (
    COMMUNICATION_DOMAIN_SPECIFIC,
)
from app.domains.communication.agents.communication_tool_registry import (
    get_communication_tools,
)
from app.shared.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer
from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS

@register_agent("communication", aliases=['comms'])
class CommunicationReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="communication",
        domain_specific=COMMUNICATION_DOMAIN_SPECIFIC,
    ).text

    """ReAct agent for multi-channel candidate communications with LGPD compliance."""

    # Message types that require human approval before sending (LGPD + EU AI Act Art.14)

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_communication_tools()]
        self._setup_enhanced(domain="communication")
        logger.info("[CommunicationReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "communication")

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
                agent_type="communication",
                domain_specific=COMMUNICATION_DOMAIN_SPECIFIC,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[communication] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.communication.agents.communication_tool_registry import get_communication_tools
            return get_communication_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Todos os tools do domínio Communication (LangGraph usa set completo)."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool

        tool_defs = get_communication_tools() + self._get_all_enhanced_tools()
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
            response = "Comunicação processada."

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

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """Override: injects 3-layer intelligence + audit SEG-5.

        Layer 1: Few-shot (via YAML prompt — already in system prompt)
        Layer 2: Tenant learning (CalibrationWeight + recruiter preferences)
        Layer 3: Global insights (anonymous cross-tenant patterns)
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
            logger.debug("[CommunicationReAct] CalibrationWeight load skipped: %s", exc)

        # --- Camada 3: Global insights ---
        try:
            from app.shared.services.global_insights_service import get_global_insights
            insights_svc = get_global_insights()
            insights = await insights_svc.get_communication_insights()
            snippet = insights_svc.format_for_prompt(insights)
            if snippet:
                existing = input.context.get("extra_instructions", "")
                input.context["extra_instructions"] = f"{existing}\n\n{snippet}" if existing else snippet
        except Exception as exc:
            logger.debug("[CommunicationReAct] GlobalInsights injection skipped: %s", exc)

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
            logger.debug("[CommunicationReAct] RecruiterPersonalization skipped: %s", exc)

        output = await super()._process_langgraph(input)

        # SEG-5: AuditService
        try:
            from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
            stage = input.context.get("current_stage", "intent-detection")
            await audit_service.log_decision(
                company_id=str(input.company_id or ""),
                agent_name="communication_react_agent",
                decision_type="send_communication",
                action=f"communication_langgraph:{stage}",
                decision="completed",
                reasoning=[f"Comunicação via LangGraph native no stage {stage}"],
                criteria_used=[stage],
                criteria_ignored=list(PROTECTED_CRITERIA),
                confidence=output.confidence,
            )
        except Exception as _audit_exc:
            logger.debug("[CommunicationReActAgent][SEG-5/LG] AuditService skipped: %s", _audit_exc)

        return output

    async def process(self, input: AgentInput) -> AgentOutput:
        # FAR-2: FairnessGuard — bloquear mensagens com linguagem discriminatória
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(input.message)
            if _fg_result.is_blocked:
                logger.warning(
                    "[CommunicationReActAgent][FAR-2] FairnessGuard bloqueou mensagem: "
                    "category=%s terms=%s",
                    _fg_result.category, _fg_result.blocked_terms,
                )
                try:
                    await _fg.log_check(
                        result=_fg_result,
                        context="communication",
                        company_id=str(input.company_id or ""),
                    )
                except Exception:  # ADR-031-R3-EXEMPT: log_check de fairness e opcional; bloqueio ja ocorre antes; falha nao cancela a resposta educativa
                    pass
                return AgentOutput(
                    message=_fg_result.educational_message,
                    confidence=1.0,
                    metadata={"fairness_blocked": True, "fairness_category": _fg_result.category},
                )
        except Exception as _fg_exc:
            logger.debug("[CommunicationReActAgent] FairnessGuard check skipped: %s", _fg_exc)

        # AUD-4: HITL — primeiro contato e feedback de rejeição exigem aprovação humana
        _hitl_approved = input.context.get("hitl_approved", False)
        _msg_type = input.context.get("message_type", "")
        if not _hitl_approved and _msg_type in HITL_REQUIRED_ACTIONS:
            try:
                import app.services.hitl_service as _hitl_svc_mod
                hitl_service = _hitl_svc_mod.hitl_service
                from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
                thread_id = str(input.session_id)
                candidate_id = input.context.get("candidate_id", "")
                pending_id = await hitl_service.request_approval(
                    thread_id=thread_id,
                    action="send_communication",
                    description=f"Enviar comunicação '{_msg_type}' para candidato {candidate_id}",
                    data={
                        "message_type": _msg_type,
                        "candidate_id": candidate_id,
                        "channel": input.context.get("channel", "email"),
                        "company_id": str(input.company_id or ""),
                    },
                    ws_session_id=thread_id,
                    domain="communication",
                    company_id=str(input.company_id or ""),
                )
                await hitl_service.store_resume_info(
                    thread_id=thread_id,
                    domain="communication",
                    session_id=thread_id,
                    agent_input_dict={
                        "message": input.message,
                        "context": {**input.context, "hitl_approved": True, "hitl_pending_id": pending_id},
                        "session_id": str(input.session_id),
                        "company_id": str(input.company_id or ""),
                        "user_id": str(input.user_id or ""),
                        "conversation_history": input.conversation_history or [],
                    },
                    hitl_context="communication_send",
                )
                try:
                    await audit_service.log_decision(
                        company_id=str(input.company_id or ""),
                        agent_name="communication_react_agent",
                        decision_type="send_communication",
                        action=f"hitl_requested:{_msg_type}",
                        decision="pending_review",
                        reasoning=[f"Comunicação '{_msg_type}' requer aprovação HITL (LGPD Art. 7)"],
                        criteria_used=[_msg_type],
                        candidate_id=str(candidate_id),
                        human_review_required=True,
                        criteria_ignored=list(PROTECTED_CRITERIA),
                    )
                except Exception as _ae:
                    logger.debug("[CommunicationReActAgent][AUD-4] AuditService skipped: %s", _ae)
                logger.info(
                    "[CommunicationReActAgent][AUD-4] HITL solicitado session=%s type=%s",
                    input.session_id, _msg_type,
                )
                return AgentOutput(
                    message=(
                        f"Aguardando aprovação para enviar **{_msg_type}** ao candidato. "
                        "Um recrutador precisa confirmar antes do envio."
                    ),
                    confidence=1.0,
                    metadata={
                        "hitl_pending": True,
                        "hitl_pending_id": pending_id,
                        "thread_id": thread_id,
                        "domain": self.domain_name,
                        "message_type": _msg_type,
                    },
                )
            except Exception as _hitl_exc:
                logger.warning(
                    "[CommunicationReActAgent][AUD-4] HITL check failed (fail-open): %s", _hitl_exc
                )

        try:
            return await self._process_langgraph(input)
        except Exception as exc:
            logger.error(f"[CommunicationReActAgent] Unhandled error: {exc}", exc_info=True)
            return AgentOutput(
                message="Erro ao processar comunicação. Tente novamente.",
                confidence=0.0,
                error=str(exc),
            )
