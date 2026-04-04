"""
Communication ReAct Agent — Multi-channel candidate communication orchestration.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.

Domain: communication
"""
import logging
from typing import Any, Dict, List, Optional

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.react_loop import ReActConfig, ReActLoop, ReActState
from app.shared.compliance.audit_callback import AuditCallback
from lia_agents_core.working_memory import WorkingMemoryService
from lia_agents_core.observability import ReActObserver
from app.services.confidence_policy_service import confidence_policy_service

from app.domains.communication.agents.communication_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
)
from app.domains.communication.agents.communication_system_prompt import (
    get_communication_system_prompt,
)
from app.domains.communication.agents.communication_tool_registry import (
    get_communication_tools,
    get_stage_tools,
)

logger = logging.getLogger(__name__)


class CommunicationReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """ReAct agent for multi-channel candidate communications with LGPD compliance."""

    # Message types that require human approval before sending (LGPD + EU AI Act Art.14)
    _HITL_MESSAGE_TYPES = frozenset({"initial_contact", "rejection_feedback", "offer_letter"})

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_communication_tools()]
        self._setup_enhanced(domain="communication")
        logger.info("[CommunicationReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "communication"

    @property
    def available_tools(self) -> List[str]:
        return list(self._all_tool_names)

    def _get_tools(self) -> list:
        """Todos os tools do domínio Communication (LangGraph usa set completo)."""
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool

        tool_defs = get_communication_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        return get_communication_system_prompt()

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
        """Override: adiciona audit SEG-5 após execução LangGraph nativa."""
        output = await super()._process_langgraph(input)

        # SEG-5: AuditService
        try:
            from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
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
                except Exception:
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
        if not _hitl_approved and _msg_type in self._HITL_MESSAGE_TYPES:
            try:
                from app.services.hitl_service import hitl_service
                from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
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
