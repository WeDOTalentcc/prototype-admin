"""
Communication ReAct Agent — Multi-channel candidate communication orchestration.

Replaces any ad-hoc communication dispatch logic with a full ReAct loop that
enforces LGPD compliance (rate limits, opt-out, quarantine) before sending.
Follows the canonical 4-file ReAct pattern: agent | tool_registry | system_prompt | stage_context.

Domain: communication
"""
import logging
import time
from typing import Any, Dict, List, Optional

from app.shared.agents.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from app.shared.agents.enhanced_agent_mixin import EnhancedAgentMixin
from app.shared.agents.langgraph_react_base import LangGraphReActBase
from app.shared.agents.react_loop import ReActConfig, ReActLoop, ReActState
from app.shared.compliance.audit_callback import AuditCallback
from app.shared.agents.working_memory import WorkingMemoryService
from app.shared.agents.observability import ReActObserver

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
    """ReAct agent for multi-channel candidate communications with LGPD compliance.

    Each call to ``process`` runs a full Reason-Act-Observe cycle using the
    communication-specific tools (send_email, send_whatsapp, get_communication_history,
    schedule_message, check_rate_limit).
    """

    def __init__(self) -> None:
        super().__init__()  # inicializa LangGraphBase._checkpointer
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

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Communication (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool

        tool_defs = get_communication_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Communication."""
        return get_communication_system_prompt()

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte MessagesState final em AgentOutput."""
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            if content and not getattr(m, "tool_call_id", None) and not (
                isinstance(m, dict) and m.get("tool_call_id")
            ):
                response = content if isinstance(content, str) else str(content)
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

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=0.90,
            metadata={"source": "langgraph_native", "domain": self.domain_name},
        )

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """Override: adiciona audit SEG-5 após execução LangGraph nativa."""
        output = await super()._process_langgraph(input)

        # SEG-5: AuditService — caminho LangGraph nativo
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

    # ------------------------------------------------------------------
    # Dual-path: LangGraph nativo ou ReActLoop legado
    # ------------------------------------------------------------------

    # Message types that require human approval before sending (LGPD + EU AI Act Art.14)
    _HITL_MESSAGE_TYPES = frozenset({"initial_contact", "rejection_feedback", "offer_letter"})

    async def process(self, input: AgentInput) -> AgentOutput:
        """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou ReActLoop."""
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
                logger.info("[CommunicationReActAgent][AUD-4] HITL solicitado session=%s type=%s", input.session_id, _msg_type)
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
                logger.warning("[CommunicationReActAgent][AUD-4] HITL check failed (fail-open): %s", _hitl_exc)

        try:
            from app.core.config import settings
            if settings.USE_LANGGRAPH_NATIVE:
                return await self._process_langgraph(input)
            return await self._process_react_loop(input)
        except Exception as exc:
            logger.error(f"[CommunicationReActAgent] Unhandled error: {exc}", exc_info=True)
            return AgentOutput(
                message="Erro ao processar comunicação. Tente novamente.",
                confidence=0.0,
                error=str(exc),
            )

    async def _process_react_loop(self, input: AgentInput) -> AgentOutput:
        """Process a communication request through the communication ReAct loop."""
        start_time = time.time()
        session_id = input.session_id
        company_id = input.company_id
        stage = input.context.get("current_stage", "intent-detection")

        logger.info(
            f"[CommunicationReActAgent] process session={session_id} "
            f"stage={stage} company={company_id}"
        )

        try:
            tools = get_stage_tools(stage)
            if not tools:
                tools = get_communication_tools()

            system_prompt = get_communication_system_prompt()
            stage_ctx = get_stage_context(stage)

            # Enrich input with company context for tools
            enriched_message = input.message
            if company_id and "company_id" not in enriched_message:
                enriched_message = f"[company_id: {company_id}] {enriched_message}"

            audit_callback = AuditCallback(
                user_id=str(input.user_id or "system"),
                company_id=str(company_id or ""),
                session_id=str(session_id),
                domain=self.domain_name,
                agent_type="react",
            )

            config = ReActConfig(
                max_iterations=6,
                system_prompt=system_prompt,
                available_tools=tools,
                domain=self.domain_name,
                model_provider="claude",
                temperature=0.3,
                audit_callback=audit_callback,
            )

            loop = ReActLoop(config=config, working_memory_service=self._memory_service)

            observer = None
            try:
                observer = ReActObserver(
                    session_id=session_id,
                    domain="communication",
                    agent_class="CommunicationReActAgent",
                    company_id=company_id,
                    user_id=input.user_id,
                )
            except Exception as obs_err:
                logger.warning(
                    f"[CommunicationReActAgent] Failed to create observer: {obs_err}"
                )

            final_state = await loop.run(
                message=enriched_message,
                context={
                    **input.context,
                    "stage": stage,
                    "stage_description": stage_ctx.get("description", ""),
                    "company_id": company_id,
                    "user_id": input.user_id,
                },
                session_id=session_id,
                observer=observer,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[CommunicationReActAgent] Done session={session_id} "
                f"iterations={final_state.iteration} elapsed={elapsed_ms}ms"
            )

            actions = [
                AgentAction(
                    action_type=a.get("type", "call_tool"),
                    params={"tool": a.get("tool", ""), "args": a.get("args", {})},
                    requires_confirmation=a.get("type") == "guardrail_blocked",
                )
                for a in final_state.actions_taken
            ]

            tool_results = [
                {
                    "tool_name": tc.get("tool_name", ""),
                    "result": tc.get("result", {}),
                    "duration_ms": tc.get("duration_ms", 0),
                }
                for tc in final_state.tool_calls_made
            ]

            confidence = 0.3 if final_state.error else (0.90 if tool_results else 0.7)

            return AgentOutput(
                message=final_state.final_response or "Comunicação processada.",
                actions=actions,
                tool_results=tool_results,
                confidence=confidence,
                error=final_state.error,
                metadata={
                    "stage": stage,
                    "iterations": final_state.iteration,
                    "domain": "communication",
                    "elapsed_ms": elapsed_ms,
                },
            )

        except Exception as exc:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[CommunicationReActAgent] ReActLoop failed: {exc}", exc_info=True
            )
            return AgentOutput(
                message="Erro ao processar comunicação. Tente novamente.",
                confidence=0.0,
                error=str(exc),
                metadata={"elapsed_ms": elapsed_ms},
            )
