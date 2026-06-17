"""
Pipeline Transition ReAct Agent — Autonomous agent for candidate stage transitions.

Layer 3 of the interpret-context endpoint. Uses a ReAct loop with 17 tools
to understand recruiter intent, extract preferences, consult candidate data,
validate fairness, and provide contextual, actionable responses.

Follows the 4-file pattern:
  - pipeline_transition_agent.py (this file) — Agent class
  - pipeline_tool_registry.py — Tool definitions
  - pipeline_system_prompt.py — System prompt builder
  - pipeline_stage_context.py — Stage-specific context
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

from app.domains.pipeline.agents.pipeline_system_prompt import get_pipeline_system_prompt

logger = logging.getLogger(__name__)


from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

@register_agent("pipeline_transition")
class PipelineTransitionAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    """Autonomous agent for intelligent candidate stage transitions.

    Processes recruiter messages during pipeline transitions using a ReAct
    loop. Extracts preferences, consults candidate data, validates fairness,
    learns recruiter patterns, and generates actionable confirmation messages.
    """

    def __init__(self) -> None:
        super().__init__()  # inicializa LangGraphBase._checkpointer
        self._memory_service = WorkingMemoryService()
        self._setup_enhanced(domain="pipeline_transition")
        logger.info("[PipelineTransitionAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "pipeline_transition"

    @property
    def available_tools(self) -> list[str]:
        from app.domains.pipeline.agents.pipeline_tool_registry import ALL_TOOLS
        return [t.name for t in ALL_TOOLS]

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para PipelineTransitionAgent."""
        try:
            from app.domains.pipeline.agents.pipeline_tool_registry import get_pipeline_transition_tools
            return get_pipeline_transition_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Todos os tools do domínio Pipeline Transition (LangGraph usa set completo)."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool

        from app.domains.pipeline.agents.pipeline_tool_registry import ALL_TOOLS
        enhanced = self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in list(ALL_TOOLS) + enhanced]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Pipeline Transition baseado no comportamento.

        T-D: prepende ``tenant_context_snippet`` resolvido pelo
        ``TenantAwareAgentMixin`` (lido de ``input.context`` — populado
        async em ``_process_langgraph`` antes do prompt ser montado).
        Sem isso, a LIA respondia "qual a empresa?" no fluxo de transição.
        """
        base = get_pipeline_system_prompt(
            action_behavior=input.context.get("action_behavior", "passive"),
            candidate_name=input.context.get("candidate_name", ""),
            job_title=input.context.get("job_title", ""),
            from_stage=input.context.get("from_stage", ""),
            to_stage=input.context.get("to_stage", ""),
        )
        snippet = (input.context or {}).get("tenant_context_snippet", "") or ""
        if snippet:
            return f"{snippet}\n\n{base}"
        return base

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte MessagesState final em AgentOutput."""
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = self._extract_text_content(content)
                break

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        return AgentOutput(
            message=response,
            actions=actions,
            state_updates={
                "action_behavior": input.context.get("action_behavior", "passive"),
                "suggested_action": "lia_auto",
            },
            confidence=0.85,
            metadata={"source": "langgraph_native", "domain": self.domain_name, "layer": 3},
        )

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """Override: adiciona audit SEG-5 após execução LangGraph nativa."""
        output = await super()._process_langgraph(input)

        # SEG-5: AuditService — caminho LangGraph nativo
        try:
            from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
            action_behavior = input.context.get("action_behavior", "passive")
            from_stage = input.context.get("from_stage", "")
            to_stage = input.context.get("to_stage", "")
            candidate_id = str(input.context.get("candidate_id", "") or "")
            _hitl_approved = input.context.get("hitl_approved", False)
            await audit_service.log_decision(
                company_id=str(input.company_id or ""),
                agent_name="pipeline_transition_agent",
                decision_type="move_stage",
                action=f"langgraph:{action_behavior}:{from_stage}->{to_stage}",
                decision="approved" if _hitl_approved else "completed",
                reasoning=[f"Transição via LangGraph native: {from_stage} → {to_stage}"],
                criteria_used=[action_behavior, f"stage:{from_stage}"] if action_behavior else [f"stage:{from_stage}"],
                candidate_id=candidate_id or None,
                confidence=output.confidence,
                criteria_ignored=list(PROTECTED_CRITERIA),
            )
        except Exception as _audit_exc:
            logger.debug("[PipelineTransitionAgent][SEG-5/LG] AuditService skipped: %s", _audit_exc)

        return output

    async def process(self, input: AgentInput) -> AgentOutput:
        """Processa transição de candidato via LangGraph nativo.

        HITL: ações de transição de candidato requerem aprovação humana.
        O context.hitl_approved=True bypassa o HITL (já aprovado).
        """
        # SEG-2 / FAR-2/A: FairnessGuard Layer 3 — verificar viés na mensagem do recrutador
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            try:
                _fg_result = await _fg.check_with_layer3(
                    input.message, action_type="pipeline_move",
                )
            except TypeError:
                _fg_result = _fg.check(input.message)
            if _fg_result.is_blocked:
                logger.warning(
                    "[PipelineTransitionAgent][SEG-2] FairnessGuard bloqueou mensagem "
                    "session=%s category=%s terms=%s",
                    input.session_id, _fg_result.category, _fg_result.blocked_terms,
                )
                await _fg.log_check(
                    result=_fg_result,
                    context="pipeline_transition",
                    company_id=str(input.company_id or ""),
                )
                return AgentOutput(
                    message=_fg_result.educational_message or (
                        "Esta solicitação não pode ser processada pois contém critérios "
                        "que podem ser discriminatórios. Transições de candidatos devem ser "
                        "baseadas em competências e resultados de avaliação."
                    ),
                    confidence=1.0,
                    metadata={
                        "fairness_blocked": True,
                        "fairness_category": _fg_result.category,
                        "domain": self.domain_name,
                    },
                )
            # FAR-3: soft_warnings já estão em _fg_result.soft_warnings
            _soft_warnings = _fg_result.soft_warnings or []
            if _soft_warnings:
                logger.info(
                    "[PipelineTransitionAgent][FAR-3] FairnessGuard soft warnings session=%s count=%d",
                    input.session_id, len(_soft_warnings),
                )
                await _fg.log_check(
                    result=_fg_result,
                    context="pipeline_transition",
                    company_id=str(input.company_id or ""),
                )
        except ImportError as _fg_exc:
            logger.debug("[PipelineTransitionAgent] FairnessGuard not available: %s", _fg_exc)
            _soft_warnings = []
        except Exception as _fg_exc:
            logger.error(
                "[LIA-FG-04] FairnessGuard error on HIGH_IMPACT pipeline_move — blocking: %s",
                _fg_exc,
            )
            from app.shared.compliance.fairness_guard import FairnessCheckResult
            return AgentOutput(
                message=(
                    "Não foi possível verificar conformidade de fairness para esta transição. "
                    "Por precaução, a ação foi bloqueada. Tente novamente."
                ),
                confidence=1.0,
                metadata={
                    "fairness_blocked": True,
                    "fairness_error": str(_fg_exc),
                    "domain": self.domain_name,
                },
            )

        # ── HITL pre-check: transição de candidato requer aprovação ──────────
        action_behavior = input.context.get("action_behavior", "passive")
        hitl_already_approved = input.context.get("hitl_approved", False)

        _ACTIVE_BEHAVIORS = {"active", "move", "transition", "advance", "reject", "offer"}
        # COMP-8: Bypass Gate 1 para candidatos de inscrição web/ATS automática
        # Candidatos que chegaram via website ou ATS já passaram por validação automática
        # e não precisam de HITL para a primeira transição (triagem → avaliação)
        _source = input.context.get("source", "")
        _is_web_or_ats_source = _source in {"web", "ats", "website", "ats_import", "gupy", "pandape", "merge"}
        _first_transition = input.context.get("from_stage", "") in {"", "aplicado", "inscrito", "new", "sourcing"}
        _bypass_gate1 = _is_web_or_ats_source and _first_transition

        needs_hitl = (
            action_behavior in _ACTIVE_BEHAVIORS
            and not hitl_already_approved
            and not _bypass_gate1  # COMP-8: bypass para web/ATS na primeira transição
            and input.context.get("to_stage")  # só quando há transição real
        )
        if _bypass_gate1 and action_behavior in _ACTIVE_BEHAVIORS:
            logger.info(
                "[PipelineTransitionAgent][COMP-8] Gate 1 bypass: source=%s from_stage=%s session=%s",
                _source, input.context.get("from_stage", ""), input.session_id,
            )

        if needs_hitl:
            try:
                # SEG-5: AuditService — registrar decisão de solicitar aprovação HITL
                try:
                    from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
                    await audit_service.log_decision(
                        company_id=str(input.company_id or ""),
                        agent_name="pipeline_transition_agent",
                        decision_type="move_stage",
                        action=f"hitl_requested:{action_behavior}",
                        decision="pending_review",
                        reasoning=[f"Transição {input.context.get('from_stage','')} → {input.context.get('to_stage','')} requer aprovação HITL"],
                        criteria_used=[action_behavior],
                        candidate_id=str(input.context.get("candidate_id", "") or ""),
                        human_review_required=True,
                        criteria_ignored=list(PROTECTED_CRITERIA),
                    )
                except Exception as _audit_exc:
                    logger.debug("[PipelineTransitionAgent][SEG-5] AuditService skipped: %s", _audit_exc)

                from app.domains.cv_screening.services.hitl_service import hitl_service
                thread_id = str(input.session_id)
                candidate_name = input.context.get("candidate_name", "candidato")
                from_stage = input.context.get("from_stage", "")
                to_stage = input.context.get("to_stage", "")
                pending_id = await hitl_service.request_approval(
                    thread_id=thread_id,
                    action="pipeline_transition",
                    description=(
                        f"Mover {candidate_name} de '{from_stage}' para '{to_stage}'"
                    ),
                    data={
                        "candidate_name": candidate_name,
                        "candidate_id": input.context.get("candidate_id", ""),
                        "from_stage": from_stage,
                        "to_stage": to_stage,
                        "job_title": input.context.get("job_title", ""),
                        "action_behavior": action_behavior,
                    },
                    ws_session_id=str(input.session_id),
                    domain="pipeline_transition",
                    company_id=str(input.company_id or ""),
                )
                # Armazena contexto para resume após aprovação
                agent_input_dict = {
                    "message": input.message,
                    "context": {**input.context, "hitl_approved": True, "hitl_pending_id": pending_id},
                    "session_id": str(input.session_id),
                    "company_id": str(input.company_id or ""),
                    "user_id": str(input.user_id or ""),
                    "conversation_history": input.conversation_history or [],
                }
                await hitl_service.store_resume_info(
                    thread_id=thread_id,
                    domain="pipeline_transition",
                    session_id=str(input.session_id),
                    agent_input_dict=agent_input_dict,
                    hitl_context="pipeline_transition",
                )
                logger.info(
                    "[PipelineTransitionAgent] HITL solicitado session=%s from=%s to=%s",
                    input.session_id, from_stage, to_stage,
                )
                return AgentOutput(
                    message=(
                        f"Aguardando aprovação para mover **{candidate_name}** "
                        f"de _{from_stage}_ para _{to_stage}_."
                    ),
                    confidence=1.0,
                    metadata={
                        "hitl_pending": True,
                        "hitl_pending_id": pending_id,
                        "thread_id": thread_id,
                        "domain": self.domain_name,
                    },
                )
            except Exception as _hitl_exc:
                logger.warning(
                    "[PipelineTransitionAgent] HITL request_approval falhou, prosseguindo: %s",
                    _hitl_exc,
                )
                # Falha silenciosa: prossegue sem aprovação

        _output = await self._process_langgraph(input)

        # FAR-3: propagar soft_warnings ao output para exibição ao recrutador via WS
        if _soft_warnings:
            if _output.metadata is None:
                _output.metadata = {}
            _output.metadata.setdefault("fairness_warnings", _soft_warnings)

        return _output


_agent_instance: PipelineTransitionAgent | None = None


def get_pipeline_transition_agent() -> PipelineTransitionAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = PipelineTransitionAgent()
    return _agent_instance
