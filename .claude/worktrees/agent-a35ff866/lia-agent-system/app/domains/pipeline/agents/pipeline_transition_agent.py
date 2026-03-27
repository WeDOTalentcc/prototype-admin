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
import json
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

from app.domains.pipeline.agents.pipeline_stage_context import (
    get_stage_capabilities,
    get_allowed_tools_for_behavior,
)
from app.domains.pipeline.agents.pipeline_system_prompt import get_pipeline_system_prompt
from app.domains.pipeline.agents.pipeline_tool_registry import (
    get_pipeline_transition_tools,
    GUARDRAIL_TOOLS,
)

logger = logging.getLogger(__name__)


class PipelineTransitionAgent(LangGraphReActBase, EnhancedAgentMixin):
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
    def available_tools(self) -> List[str]:
        from app.domains.pipeline.agents.pipeline_tool_registry import ALL_TOOLS
        return [t.name for t in ALL_TOOLS]

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Pipeline Transition (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        from app.domains.pipeline.agents.pipeline_tool_registry import ALL_TOOLS
        enhanced = self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in list(ALL_TOOLS) + enhanced]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Pipeline Transition baseado no comportamento."""
        return get_pipeline_system_prompt(
            action_behavior=input.context.get("action_behavior", "passive"),
            candidate_name=input.context.get("candidate_name", ""),
            job_title=input.context.get("job_title", ""),
            from_stage=input.context.get("from_stage", ""),
            to_stage=input.context.get("to_stage", ""),
        )

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
            from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
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

    # ------------------------------------------------------------------
    # Dual-path: LangGraph nativo ou ReActLoop legado
    # ------------------------------------------------------------------

    async def process(self, input: AgentInput) -> AgentOutput:
        """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou ReActLoop.

        HITL: ações de transição de candidato requerem aprovação humana.
        O context.hitl_approved=True bypassa o HITL (já aprovado).
        """
        # SEG-2 / FAR-2/A: FairnessGuard Layer 3 — verificar viés na mensagem do recrutador
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = await _fg.check_with_layer3(
                input.message, action_type="pipeline_move",
            )
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
        except Exception as _fg_exc:
            logger.debug("[PipelineTransitionAgent] FairnessGuard check skipped: %s", _fg_exc)
            _soft_warnings = []

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
                    from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
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

                from app.services.hitl_service import hitl_service
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

        from app.core.config import settings
        if settings.USE_LANGGRAPH_NATIVE:
            _output = await self._process_langgraph(input)
        else:
            _output = await self._process_react_loop(input)

        # FAR-3: propagar soft_warnings ao output para exibição ao recrutador via WS
        if _soft_warnings:
            if _output.metadata is None:
                _output.metadata = {}
            _output.metadata.setdefault("fairness_warnings", _soft_warnings)

        return _output

    async def _process_react_loop(self, input: AgentInput) -> AgentOutput:
        start_time = time.time()

        action_behavior = input.context.get("action_behavior", "passive")
        candidate_name = input.context.get("candidate_name", "")
        candidate_id = input.context.get("candidate_id", "")
        job_title = input.context.get("job_title", "")
        job_id = input.context.get("job_id", "")
        from_stage = input.context.get("from_stage", "")
        to_stage = input.context.get("to_stage", "")

        logger.info(
            f"[PipelineTransitionAgent] Processing message for session={input.session_id} "
            f"behavior={action_behavior} candidate={candidate_name}"
        )

        try:
            memory_summary = ""
            try:
                memory = await self._load_memory(
                    session_id=input.session_id,
                    company_id=input.company_id,
                    user_id=input.user_id,
                )
                memory_summary = await self._memory_service.get_context_summary(
                    session_id=input.session_id,
                    domain=self.domain_name,
                )
            except Exception as mem_err:
                logger.debug(f"[PipelineTransitionAgent] Memory load skipped: {mem_err}")

            extra_context = ""
            try:
                extra_context = await self._get_memory_context(
                    session_id=input.session_id,
                    company_id=input.company_id,
                )
            except Exception:
                pass

            guardrails = []
            try:
                guardrails = await self._resolve_guardrails(input.company_id)
            except Exception:
                guardrails = list(GUARDRAIL_TOOLS)

            tools = get_pipeline_transition_tools(action_behavior)
            enhanced_tools = self._get_all_enhanced_tools()
            all_tools = tools + enhanced_tools

            system_prompt = get_pipeline_system_prompt(
                action_behavior=action_behavior,
                candidate_name=candidate_name,
                job_title=job_title,
                from_stage=from_stage,
                to_stage=to_stage,
                extra_context=extra_context if extra_context else None,
            )

            audit_callback = AuditCallback(
                user_id=str(input.user_id or "system"),
                company_id=str(input.company_id or ""),
                session_id=str(input.session_id),
                domain=self.domain_name,
                agent_type="react",
            )

            config = ReActConfig(
                max_iterations=5,
                system_prompt=system_prompt,
                available_tools=all_tools,
                domain=self.domain_name,
                model_provider="claude",
                temperature=0.3,
                guardrails=guardrails,
                extra_context=extra_context,
                audit_callback=audit_callback,
            )

            loop = ReActLoop(config=config, working_memory_service=self._memory_service)

            observer = None
            try:
                observer = ReActObserver(
                    session_id=input.session_id,
                    domain="pipeline_transition",
                    agent_class="PipelineTransitionAgent",
                    company_id=input.company_id,
                    user_id=input.user_id,
                )
                observer.log.stage_before = from_stage
                observer.log.user_message_length = len(input.message)
                observer.log.model_provider = config.model_provider
            except Exception as obs_err:
                logger.debug(f"[PipelineTransitionAgent] Observer creation skipped: {obs_err}")

            context = {
                "action_behavior": action_behavior,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "job_id": job_id,
                "job_title": job_title,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "company_id": input.company_id,
                "user_id": input.user_id,
                "recruiter_id": input.user_id,
                "conversation_history": [
                    {"role": m.get("role", "user"), "content": m.get("content", "")}
                    for m in input.conversation_history[-10:]
                ],
            }

            state = await loop.run(
                message=input.message,
                context=context,
                session_id=input.session_id,
                observer=observer,
            )

            output = self._build_transition_output(state, action_behavior, context)

            # SEG-5: AuditService — registrar decisão de transição concluída
            try:
                from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
                _hitl_approved = input.context.get("hitl_approved", False)
                await audit_service.log_decision(
                    company_id=str(input.company_id or ""),
                    agent_name="pipeline_transition_agent",
                    decision_type="move_stage",
                    action=f"{action_behavior}:{from_stage}->{to_stage}",
                    decision="approved" if _hitl_approved else "completed",
                    reasoning=[f"Transição de {from_stage} para {to_stage} via {action_behavior}"],
                    criteria_used=[action_behavior, f"stage:{from_stage}"] if action_behavior else [f"stage:{from_stage}"],
                    candidate_id=str(candidate_id) if candidate_id else None,
                    confidence=output.confidence,
                    human_review_required=False,
                    criteria_ignored=list(PROTECTED_CRITERIA),
                )
            except Exception as _audit_exc:
                logger.debug("[PipelineTransitionAgent][SEG-5] AuditService skipped: %s", _audit_exc)

            # E12: Event store — dual write (immutable audit trail)
            try:
                _db = getattr(self, "_db", None) or context.get("db")
                if _db:
                    import asyncio as _asyncio
                    from app.services.event_store_service import event_store_service as _es
                    _asyncio.create_task(_es.append(
                        aggregate_type="candidate",
                        aggregate_id=str(candidate_id),
                        event_type="CandidateMoved",
                        data={
                            "from_stage": from_stage,
                            "to_stage": to_stage,
                            "job_id": str(job_id) if job_id else None,
                        },
                        company_id=str(input.company_id or ""),
                        db=_db,
                        created_by=str(input.user_id) if input.user_id else "system",
                    ))
            except Exception:
                pass

            # D6-G3: ML Feedback Loop — registra sinal quando transição é hired/rejected
            # Best-effort: não bloqueia o fluxo principal
            try:
                _HIRE_STAGES = {"hired", "offer_accepted"}
                _REJECT_STAGES = {"rejected", "offer_rejected"}
                if to_stage in _HIRE_STAGES or to_stage in _REJECT_STAGES:
                    from app.services.ml_feedback_service import ml_feedback_service as _ml_fb
                    _ml_decision = "hire" if to_stage in _HIRE_STAGES else "reject"
                    _db = getattr(self, "_db", None) or getattr(state, "db", None) if hasattr(state, "db") else None
                    if _db is None:
                        _context_db = context.get("db")
                        _db = _context_db
                    if _db:
                        import asyncio as _asyncio
                        _asyncio.create_task(
                            _ml_fb.record_decision(
                                db=_db,
                                company_id=str(input.company_id or ""),
                                job_id=str(job_id or ""),
                                candidate_id=str(candidate_id or ""),
                                lia_score=float(context.get("score") or state.context.get("score", 0) if hasattr(state, "context") else 0),
                                decision=_ml_decision,
                            )
                        )
            except Exception as _ml_exc:
                logger.debug("[D6-G3] ml_feedback record_decision skipped: %s", _ml_exc)

            try:
                await self._post_loop_learning(
                    state=state,
                    company_id=input.company_id,
                    session_id=input.session_id,
                    context={"stage": from_stage, "action_behavior": action_behavior},
                )
            except Exception:
                pass

            try:
                await self._save_memory(
                    state=state,
                    output=output,
                    session_id=input.session_id,
                    current_stage=to_stage,
                )
            except Exception:
                pass

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[PipelineTransitionAgent] Completed in {duration_ms:.0f}ms "
                f"iterations={state.iteration} tools={len(state.tool_calls_made)}"
            )
            output.metadata["duration_ms"] = round(duration_ms, 1)

            try:
                if observer:
                    observer.finalize(
                        confidence=output.confidence,
                        response_length=len(output.message),
                        stage_after=to_stage,
                    )
            except Exception:
                pass

            return output

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[PipelineTransitionAgent] Error: {exc}",
                exc_info=True,
            )
            return self._build_error_output(exc, duration_ms)

    def _build_transition_output(
        self,
        state: ReActState,
        action_behavior: str,
        context: Dict[str, Any],
    ) -> AgentOutput:
        response_text = state.final_response or ""

        extracted_preferences = {}
        tasks = []
        out_of_scope = False
        candidate_info = {}
        learned_suggestions = []
        suggested_sub_status = None
        suggested_action = None
        fairness_result = None

        for tool_call in state.tool_calls_made:
            tool_name = tool_call.get("tool_name", "")
            result = tool_call.get("result", {})

            if not result.get("success", False):
                continue

            if tool_name == "extract_preferences":
                prefs = result.get("extracted_preferences", {})
                extracted_preferences.update(prefs)

            elif tool_name == "suggest_sub_status":
                suggested_sub_status = result.get("suggested_sub_status")

            elif tool_name in ("get_candidate_profile", "get_candidate_salary_info"):
                data = result.get("profile") or result.get("salary_info") or {}
                candidate_info.update(data)

            elif tool_name == "get_candidate_wsi_scores":
                candidate_info["wsi_scores"] = result.get("scores", [])

            elif tool_name == "get_candidate_screening_results":
                candidate_info["screening_results"] = result.get("results", [])

            elif tool_name == "schedule_secondary_task":
                tasks.append({
                    "type": result.get("task_type", ""),
                    "description": result.get("description", ""),
                    "status": "scheduled",
                })

            elif tool_name == "request_data_collection":
                tasks.append({
                    "type": "data_collection",
                    "data_type": result.get("data_type", ""),
                    "description": result.get("description", ""),
                    "status": "scheduled",
                })

            elif tool_name == "check_rejection_fairness":
                fairness_result = {
                    "is_fair": result.get("is_fair", True),
                    "warnings": result.get("warnings", []),
                    "educational_message": result.get("educational_message"),
                }

            elif tool_name == "get_recruiter_preferences":
                prefs = result.get("preferences", [])
                for pref in prefs:
                    if pref.get("frequency", 0) >= 2:
                        learned_suggestions.append({
                            "key": pref.get("preference_key", ""),
                            "value": pref.get("preference_value", ""),
                            "frequency": pref.get("frequency", 0),
                            "source": "recruiter_history",
                        })

        clean_text = response_text.lower().replace("**", "").replace("*", "")
        out_of_scope_markers = [
            "fora do escopo", "fora do meu escopo", "não posso ajudar com isso",
            "use o funil", "use a seção", "acesse o painel",
            "meu escopo nesta conversa", "escopo nesta conversa é",
            "não consigo comparar", "não posso comparar",
        ]
        if any(marker in clean_text for marker in out_of_scope_markers):
            out_of_scope = True

        caps = get_stage_capabilities(action_behavior)
        if not suggested_action:
            suggested_action = caps.get("default_action", "lia_auto")

        actions = []
        if extracted_preferences:
            actions.append(AgentAction(
                action_type="update_field",
                params={"preferences": extracted_preferences},
            ))
        for task in tasks:
            actions.append(AgentAction(
                action_type="call_tool",
                params=task,
            ))

        confidence = 0.85
        if state.error:
            confidence = 0.3
        elif out_of_scope:
            confidence = 0.95
        elif fairness_result and not fairness_result.get("is_fair"):
            confidence = 0.99
        elif len(state.tool_calls_made) == 0:
            confidence = 0.6

        return AgentOutput(
            message=response_text,
            actions=actions,
            state_updates={
                "suggested_sub_status": suggested_sub_status,
                "suggested_action": suggested_action,
                "extracted_preferences": extracted_preferences,
                "tasks": tasks,
                "out_of_scope": out_of_scope,
                "candidate_info": candidate_info if candidate_info else None,
                "learned_suggestions": learned_suggestions if learned_suggestions else None,
                "fairness_result": fairness_result,
            },
            confidence=confidence,
            reasoning_steps=[obs for obs in state.observations],
            tool_results=[
                {
                    "tool": tc.get("tool_name"),
                    "success": tc.get("result", {}).get("success", False),
                    "duration_ms": tc.get("duration_ms"),
                }
                for tc in state.tool_calls_made
            ],
            metadata={
                "action_behavior": action_behavior,
                "iterations": state.iteration,
                "tools_called": len(state.tool_calls_made),
                "layer": 3,
            },
        )

    def _build_error_output(self, exc: Exception, duration_ms: float) -> AgentOutput:
        return AgentOutput(
            message="",
            actions=[],
            state_updates={},
            confidence=0.0,
            reasoning_steps=[],
            tool_results=[],
            metadata={"duration_ms": round(duration_ms, 1), "layer": 3},
            error=str(exc),
        )

    async def _load_memory(self, session_id: str, company_id: str, user_id: str):
        return await self._memory_service.get_or_create_memory(
            session_id=session_id,
            domain=self.domain_name,
            company_id=company_id,
            user_id=user_id,
        )

    async def _save_memory(
        self,
        state: ReActState,
        output: AgentOutput,
        session_id: str,
        current_stage: str,
    ):
        updates = {
            "current_stage": current_stage,
            "last_intent": "pipeline_transition",
            "last_confidence": output.confidence,
        }
        if output.state_updates.get("extracted_preferences"):
            updates["collected_fields"] = output.state_updates["extracted_preferences"]

        await self._memory_service.update_memory(
            session_id=session_id,
            domain=self.domain_name,
            updates=updates,
        )


_agent_instance: Optional[PipelineTransitionAgent] = None


def get_pipeline_transition_agent() -> PipelineTransitionAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = PipelineTransitionAgent()
    return _agent_instance
