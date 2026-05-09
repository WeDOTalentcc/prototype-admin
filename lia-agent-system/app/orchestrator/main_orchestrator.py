"""
MainOrchestrator — entry point único para todas as mensagens da LIA.

Pipeline unificado (eliminando a dupla delegação MainOrchestrator → Orchestrator):

  UniversalContext
    → FairnessGuard (pré-check bloqueio + soft warnings)
    → TenantContext enrichment
    → Phase 0: PendingAction (multi-turn / confirmação)
    → Phase 1: ActionExecutor (ações fechadas detectadas por intent)
    → Phase 2: ConversationMemory + CascadedRouter → DomainWorkflow → ReAct Agent

Consolida a lógica que antes estava espalhada em:
- orchestrated_talent_chat.py (500 linhas, 7 fases)
- orchestrated_job_chat.py
- pipeline_orchestrator.py
- agent_chat_ws.py
- Orchestrator.process_request_with_memory() (intermediário eliminado)
"""
from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from app.orchestrator.action_executor import (
    ACTIONABLE_INTENTS,
    ActionResult,
    action_executor,
    is_confirmation,
    is_rejection,
    resolve_candidate_from_context,
)
from app.orchestrator.context_adapter import UniversalContext
from app.orchestrator.pending_action import pending_action_store
from app.shared.services.tenant_context_service import TenantContextService
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.robustness.security_patterns import check_input_security, get_block_response
from app.shared.memory.candidate_list_store import candidate_list_store

from app.shared.providers.llm_factory import get_provider_for_tenant
from app.shared.tenant_llm_context import get_current_llm_tenant, get_tenant_llm_config

logger = logging.getLogger(__name__)

_CACHEABLE_DOMAINS: set[str] = {
    "analytics", "kanban_search", "kanban_insight", "recruiter_assistant",
    "pipeline_context",
}
_CACHE_TTL_BY_DOMAIN: dict[str, int] = {
    "analytics": 90,
    "kanban_search": 60,
    "kanban_insight": 120,
    "recruiter_assistant": 300,
    "pipeline_context": 60,
}

_perf_metrics: dict[str, list[float]] = {}


def get_perf_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for domain, times in _perf_metrics.items():
        recent = times[-100:]
        summary[domain] = {
            "count": len(recent),
            "avg_ms": round(sum(recent) / len(recent), 1) if recent else 0,
            "p95_ms": round(sorted(recent)[int(len(recent) * 0.95)] if recent else 0, 1),
        }
    return summary


# ---------------------------------------------------------------------------
# Response schema unificado
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# UC-P3-14: LIA_V2_USE_PLAN_SERVICE feature flag
# ---------------------------------------------------------------------------
def _is_plan_service_enabled() -> bool:
    """Check if the new PlanService orchestration path is enabled.

    # UC-P3-14: task_planner active via LIA_V2_USE_PLAN_SERVICE flag.
    # Promotion to production without flag: 2026-07-01
    # To promote: set LIA_V2_USE_PLAN_SERVICE=true in production env
    # and remove this gate once stable for 2 weeks.

    Default: False (backward-compatible). Set LIA_V2_USE_PLAN_SERVICE=true
    to enable PlanService-based orchestration (Sprint III-B rollout).
    """
    import os as _os
    raw = _os.environ.get("LIA_V2_USE_PLAN_SERVICE", "false").lower()
    return raw in ("1", "true", "yes")

class ChatResponse(BaseModel):
    success: bool
    content: str
    agent_used: str = "main_orchestrator"
    agents_consulted: list[str] = Field(default_factory=list)
    intent_detected: str = "general"
    confidence: float = 1.0
    structured_data: dict[str, Any] | None = None
    suggested_prompts: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    conversation_id: str | None = None
    ui_action: str | None = None
    ui_action_params: dict[str, Any] | None = None
    action_executed: bool = False
    action_result: dict[str, Any] | None = None
    action_type: str | None = None
    needs_confirmation: bool = False
    needs_params: bool = False
    pending_action_id: str | None = None
    fairness_warnings: list[str] = Field(default_factory=list)
    from_cache: bool = False

    @classmethod
    def from_orchestrator_result(cls, result: dict[str, Any], conv_id: str) -> ChatResponse:
        """Converte o dict retornado por Orchestrator.process_request()."""
        # Se o resultado tem score_breakdown, incluir em structured_data
        _structured = result.get("structured_data", result.get("data")) or {}
        if result.get("score_breakdown"):
            _structured["score_breakdown"] = result["score_breakdown"]
        return cls(
            success=result.get("success", True),
            content=result.get("response", result.get("message", result.get("content", ""))),
            agent_used=result.get("agent_used", result.get("domain_id", "orchestrator")),
            agents_consulted=result.get("agents_consulted", []),
            intent_detected=result.get("intent_detected", result.get("intent", "general")),
            confidence=result.get("confidence", 1.0),
            structured_data=_structured or None,
            suggested_prompts=result.get("suggested_prompts", result.get("suggestions", [])),
            actions=result.get("actions", []),
            conversation_id=conv_id,
            ui_action=result.get("ui_action"),
            ui_action_params=result.get("ui_action_params"),
        )

    @classmethod
    def from_action_result(
        cls,
        action_result: ActionResult,
        intent: str,
        conv_id: str,
        suggested_prompts: list[str] | None = None,
    ) -> ChatResponse:
        return cls(
            success=True,
            content=action_result.message,
            agent_used="ActionExecutor",
            agents_consulted=["ActionExecutor"],
            intent_detected=intent,
            confidence=1.0,
            structured_data=action_result.data,
            suggested_prompts=suggested_prompts or [],
            conversation_id=conv_id,
            action_executed=action_result.status == "executed",
            action_result=action_result.data,
            action_type=action_result.action_type,
            needs_confirmation=action_result.status == "needs_confirmation",
            needs_params=action_result.status == "needs_params",
            pending_action_id=action_result.pending_action_id,
        )


# ---------------------------------------------------------------------------
# MainOrchestrator
# ---------------------------------------------------------------------------

class MainOrchestrator:
    """
    Entry point único consolidado para todas as mensagens da LIA.

    Recebe UniversalContext (normalizado pelo ContextAdapter) e processa através
    do pipeline unificado, sem delegar para Orchestrator.process_request_with_memory
    como camada intermediária. O Orchestrator permanece como motor de roteamento
    e execução de domínio, mas a gestão de memória e o fluxo de fases são
    controlados aqui.
    """

    def __init__(
        self,
        orchestrator: Any,
        *,
        plan_service=None,
        fallback_react_service=None,
        policy_gate_service=None,
    ) -> None:
        self._orchestrator = orchestrator
        self._fairness_guard = FairnessGuard()
        self._tenant_context_service = TenantContextService()
        self._plan_service = plan_service
        self._fallback_react_service = fallback_react_service
        self._policy_gate_service = policy_gate_service

    async def process(
        self,
        ctx: UniversalContext,
        db: Any,
        streaming_callback: Callable | None = None,
    ) -> ChatResponse:
        # LIA-P05: streaming_callback enables streaming output through the full compliance pipeline.
        # Callers should pass an async generator callback that receives chunks.
        # This is the preferred way to add streaming without bypassing compliance.
        # All security checks (SecurityPatterns, FairnessGuard, memory persistence)
        # run before any tokens are emitted, ensuring full pipeline compliance.
        """
        Processa uma mensagem através do pipeline unificado.

        Phase 0: PendingAction — se há ação pendente aguardando confirmação/params
        Phase 1: ActionExecutor — ações fechadas detectáveis por padrão
        Phase 2: Orchestrator completo — CascadedRouter → DomainWorkflow → ReAct Agent

        LIA-A03: Agentic interpretation is controlled by LIA_AGENTIC_INTERPRET env var.
        Set to "false" to disable LLM interpretation of action results (falls back to raw).
        Default: "true" — LLM interprets all action results for natural responses.
        """
        conv_id = ctx.conversation_id or str(uuid.uuid4())
        _t0 = time.monotonic()

        try:
            # ── Pré-check SecurityPatterns — antes de qualquer processamento ──
            message_text = ctx.message or ""
            _security_result = check_input_security(message_text)
            if _security_result.is_blocked:
                logger.warning(
                    "[MainOrchestrator] SecurityPatterns blocked input: "
                    "user=%s company=%s risk=%s categories=%s",
                    ctx.user_id, ctx.company_id,
                    _security_result.risk_level, _security_result.threat_categories,
                )
                return ChatResponse(
                    success=False,
                    content=get_block_response(_security_result, language="pt"),
                    agent_used="security_patterns",
                    confidence=_security_result.confidence,
                    intent_detected="blocked_security",
                    conversation_id=conv_id,
                )

            # ── Pré-check FairnessGuard — antes de qualquer fase de processamento ──
            message_text = ctx.message or ""
            _fairness_result = self._fairness_guard.check(message_text)
            if _fairness_result.is_blocked:
                logger.warning(
                    "[MainOrchestrator] FairnessGuard blocked input: "
                    "user=%s company=%s category=%s",
                    ctx.user_id, ctx.company_id, getattr(_fairness_result, "category", "unknown"),
                )
                return ChatResponse(
                    success=False,
                    content=_fairness_result.educational_message or (
                        "Não posso processar essa solicitação pois viola critérios de equidade e compliance."
                    ),
                    agent_used="fairness_guard",
                    confidence=1.0,
                    intent_detected="blocked_bias",
                    conversation_id=conv_id,
                )
            # Camada 2 — soft warnings (advisory, não bloqueia — propagados no response)
            _soft_warnings: list[str] = list(getattr(_fairness_result, "soft_warnings", None) or [])
            try:
                _implicit_warnings = self._fairness_guard.check_implicit_bias(message_text)
                if _implicit_warnings:
                    for _w in _implicit_warnings:
                        if _w not in _soft_warnings:
                            _soft_warnings.append(_w)
                    logger.info(
                        "[MainOrchestrator] FairnessGuard soft warnings: user=%s count=%d",
                        ctx.user_id, len(_soft_warnings),
                    )
            except Exception as _fg_exc:
                logger.debug("[MainOrchestrator] FairnessGuard implicit check skipped: %s", _fg_exc)

            # Enriquecer contexto com informações do tenant
            try:
                _job_id = ctx.entity_id if getattr(ctx, "entity_type", None) == "job" else None
                _tenant_ctx = await self._tenant_context_service.get_context(
                    company_id=str(ctx.company_id), db=db, job_id=_job_id,
                )
                ctx.tenant_context_snippet = _tenant_ctx.to_prompt_snippet()
            except Exception as _tc_exc:
                logger.debug("[MainOrchestrator] TenantContext skipped: %s", _tc_exc)

            # Enriquecer contexto com personalização do recrutador
            try:
                from app.domains.analytics.services.recruiter_personalization_service import RecruiterPersonalizationService
                _perso_svc = RecruiterPersonalizationService()
                _perso_ctx = await _perso_svc.get_or_create_profile(ctx.user_id, db)
                if _perso_ctx and hasattr(_perso_ctx, 'settings') and _perso_ctx.settings:
                    _prefs = []
                    if getattr(_perso_ctx.settings, 'communication_style', ''):
                        _prefs.append(f"Estilo de comunicação: {_perso_ctx.settings.communication_style}")
                    if getattr(_perso_ctx.settings, 'verbosity_preference', ''):
                        _prefs.append(f"Verbosidade: {_perso_ctx.settings.verbosity_preference}")
                    if getattr(_perso_ctx.settings, 'focus_areas', None):
                        _prefs.append(f"Foco principal: {', '.join(_perso_ctx.settings.focus_areas)}")
                    if _prefs:
                        ctx.extra["recruiter_context"] = "\n".join(_prefs)
            except Exception as _perso_exc:
                logger.debug("[MainOrchestrator] Recruiter personalization skipped: %s", _perso_exc)

            # Enriquecer contexto do usuário (nome e role)
            if not ctx.user_name and ctx.user_id:
                try:
                    from sqlalchemy import select as sa_select
                    from app.auth.models import User
                    _user_result = await db.execute(
                        sa_select(User).where(User.id == ctx.user_id)
                    )
                    _user = _user_result.scalar_one_or_none()
                    if _user:
                        ctx.user_name = getattr(_user, "name", "") or getattr(_user, "full_name", "") or ""
                        ctx.user_role = getattr(_user, "role", "") or ""
                except Exception as _user_exc:
                    logger.debug("[MainOrchestrator] User lookup skipped: %s", _user_exc)

            # LIA-M01: Setup conversation memory BEFORE any phase
            # This ensures every user message is persisted regardless of which phase handles it
            conv, conv_id = None, conv_id
            if not ctx.skip_memory_persist:
                try:
                    conv, conv_id = await self._setup_conversation_memory(ctx, conv_id, db, {})
                except Exception as e:
                    logger.warning("[LIA-M01] Memory setup failed (non-blocking): %s", e)

            # ── Phase 0.5: Rail A capability gate (PR-J) ──────────────────
            # Computational guide: check capability_map BEFORE pending action or LLM.
            # Non-chat-executable intents (add_candidate, interview_scheduling) return
            # ui_action immediately — no LLM call needed.
            try:
                from app.orchestrator.rail_a_capability_check import check_rail_a_capability
                _cap_result = await check_rail_a_capability(
                    context=ctx.extra or {},
                    message=message_text,
                    company_id=str(ctx.company_id or ""),
                    db=db,
                )
                if _cap_result is not None:
                    return ChatResponse(
                        success=_cap_result.get("success", True),
                        content=_cap_result.get("content", ""),
                        agent_used=_cap_result.get("domain", "capability_map"),
                        confidence=float(_cap_result.get("confidence", 1.0)),
                        intent_detected=_cap_result.get("intent_hint", ""),
                        conversation_id=conv_id,
                        ui_action=_cap_result.get("ui_action"),
                        ui_action_params=_cap_result.get("ui_action_params"),
                        fairness_warnings=_soft_warnings,
                    )
            except Exception as _cap_exc:
                logger.debug("[MainOrchestrator] Rail A capability gate skipped: %s", _cap_exc)

            # ── Phase 0: PendingAction ──────────────────────────────────────
            pending_response = await self._handle_pending_action(ctx, conv_id)
            if pending_response is not None:
                # LIA-M02: Persist Phase 0 response to conversation memory
                if conv and not ctx.skip_memory_persist:
                    try:
                        await self._persist_response(ctx, conv_id, conv, {"response": pending_response.content}, db)
                    except Exception as e:
                        logger.warning("[LIA-M02] Phase 0 memory persist failed: %s", e)
                if _soft_warnings and not pending_response.fairness_warnings:
                    pending_response.fairness_warnings = _soft_warnings
                return pending_response

            # ── Phase 1: ActionExecutor ────────────────────────────────────
            action_response = await self._try_action_executor(ctx, conv_id)
            if action_response is not None:
                # LIA-M02: Persist Phase 1 response to conversation memory
                if conv and not ctx.skip_memory_persist:
                    try:
                        await self._persist_response(ctx, conv_id, conv, {"response": action_response.content}, db)
                    except Exception as e:
                        logger.warning("[LIA-M02] Phase 1 memory persist failed: %s", e)
                if _soft_warnings and not action_response.fairness_warnings:
                    action_response.fairness_warnings = _soft_warnings
                return action_response

            # ── Phase 1.3: Plan & Execute (LIA-P&E / UC-P3-14) ─────────────────
            # Feature-flagged: LIA_V2_USE_PLAN_SERVICE=true
            # Sits between ActionExecutor (closed actions) and AgenticLoop (open LLM).
            # Handles multi-step coordinated plans ("buscar e comparar", templates, etc.)
            # Promotion to production without flag: 2026-07-01
            if _is_plan_service_enabled():
                try:
                    from app.shared.execution.plan_detector import PlanDetector
                    from app.shared.execution.plan_executor import PlanExecutor
                    from app.shared.execution.plan_templates import PlanTemplateRegistry

                    # ── Template Discovery ────────────────────────────────
                    # Respond to "que planos tem?" / "listar templates" / etc.
                    import re as _re_plan
                    _DISCOVERY_RE = _re_plan.compile(
                        r"(que\s+planos|quais\s+planos|listar?\s+planos|listar?\s+templates?|"
                        r"que\s+automações|o\s+que\s+você\s+pode\s+automatizar|"
                        r"mostrar?\s+planos|planos\s+disponíveis)",
                        _re_plan.IGNORECASE,
                    )
                    if _DISCOVERY_RE.search(ctx.message or ""):
                        _tmpls = PlanTemplateRegistry.TEMPLATES
                        _lines = ["📋 **Planos disponíveis** — diga qual quer executar:\n"]
                        for _key, _info in _tmpls.items():
                            _lines.append("\u2022 **" + _info['name'] + "** \u2014 " + _info['description'])
                        _discovery_text = "\n".join(_lines)
                        _disc_resp = ChatResponse(
                            success=True,
                            content=_discovery_text,
                            intent_detected="plan_template_discovery",
                            conversation_id=conv_id,
                            action_executed=False,
                            structured_data={"templates": list(_tmpls.keys())},
                        )
                        if _soft_warnings:
                            _disc_resp.fairness_warnings = _soft_warnings
                        return _disc_resp

                    _plan_detector = PlanDetector()
                    _detected_plan = _plan_detector.detect(ctx.message)

                    if _detected_plan is not None:
                        _plan_executor = PlanExecutor()
                        _pe_company_id = getattr(ctx, "company_id", None)
                        _pe_user_id = str(getattr(ctx, "user_id", "system") or "system")

                        _completed_plan = await _plan_executor.execute(
                            _detected_plan,
                            user_id=_pe_user_id,
                            session_id=conv_id or "",
                            tenant_id=str(_pe_company_id) if _pe_company_id else None,
                        )

                        _plan_domain_resp = _plan_executor.build_consolidated_response(_completed_plan)
                        _plan_text = _plan_domain_resp.message

                        if conv and not ctx.skip_memory_persist:
                            try:
                                await self._persist_response(
                                    ctx, conv_id, conv, {"response": _plan_text}, db
                                )
                            except Exception as _pe_exc:
                                logger.warning("[LIA-P&E] memory persist failed: %s", _pe_exc)

                        _plan_resp = ChatResponse(
                            success=True,
                            content=_plan_text,
                            intent_detected="plan_execute",
                            conversation_id=conv_id,
                            action_executed=True,
                            structured_data={
                                "plan_id": _completed_plan.plan_id,
                                "pattern": _completed_plan.detected_pattern,
                                "tasks": len(_completed_plan.tasks),
                                "status": _completed_plan.status.value,
                            },
                        )
                        if _soft_warnings:
                            _plan_resp.fairness_warnings = _soft_warnings

                        logger.info(
                            "[LIA-P&E] plan executed: pattern=%s tasks=%d status=%s",
                            _completed_plan.detected_pattern,
                            len(_completed_plan.tasks),
                            _completed_plan.status.value,
                        )
                        return _plan_resp

                except Exception as _pe_err:
                    logger.warning(
                        "[LIA-P&E] plan detection/execution failed — falling through to Phase 1.5: %s",
                        _pe_err,
                    )

            # ── Phase 1.5: Agentic Tool Calling (LIA-A04) ──────────────────
            # If Phase 1 did not match, let the LLM decide whether to call tools
            # via function calling. Feature-flagged: LIA_AGENTIC_LOOP=true
            import os as _os_flag
            if _os_flag.getenv("LIA_AGENTIC_LOOP", "true").lower() not in ("false", "0"):
                try:
                    from app.orchestrator.agentic_loop import agentic_loop

                    # LIA-LLM-1: Respect Choose Your AI — use tenant's chat provider
                    _agentic_provider = "claude"
                    _loop_company_id = getattr(ctx, "company_id", None)
                    if _loop_company_id:
                        try:
                            from app.shared.tenant_llm_context import get_tenant_llm_config as _get_llm_cfg
                            _tenant_cfg = await _get_llm_cfg(_loop_company_id)
                            if _tenant_cfg:
                                _agentic_provider = (
                                    _tenant_cfg.get("routing", {}).get("chat")
                                    or _tenant_cfg.get("primary_provider")
                                    or "claude"
                                )
                        except Exception:
                            pass  # Fail-open: use claude default

                    _agentic_result = await agentic_loop.run(
                        user_message=ctx.message,
                        system_prompt="",
                        conversation_history=ctx.extra.get("conversation_history", []),
                        company_id=_loop_company_id,
                        user_id=getattr(ctx, "user_id", None),
                        provider=_agentic_provider,
                    )

                    if _agentic_result and _agentic_result.get("response"):
                        logger.info(
                            "[LIA-A04] Agentic loop resolved in %d iterations with %d tool calls",
                            _agentic_result.get("iterations", 0),
                            len(_agentic_result.get("tool_calls_made", [])),
                        )
                        # Persist to conversation memory
                        if conv and not ctx.skip_memory_persist:
                            try:
                                await self._persist_response(
                                    ctx, conv_id, conv,
                                    {"response": _agentic_result["response"]}, db,
                                )
                            except Exception as exc:
                                logger.warning(
                                    "[main_orchestrator] _persist_response failed (message lost) conv_id=%s: %s",
                                    conv_id, exc, exc_info=True,
                                )

                        _resp = ChatResponse(
                            success=True,
                            content=_agentic_result["response"],
                            intent_detected="agentic_tool_call",
                            conversation_id=conv_id,
                            action_executed=bool(_agentic_result.get("tool_calls_made")),
                            structured_data={
                                "tool_calls": _agentic_result.get("tool_calls_made", []),
                                "iterations": _agentic_result.get("iterations", 0),
                            },
                        )
                        if _soft_warnings:
                            _resp.fairness_warnings = _soft_warnings
                        return _resp
                except Exception as exc:
                    logger.debug("[LIA-A04] Agentic loop skipped: %s", exc)

            # ── Phase 2: Orchestrator completo ─────────────────────────────
            _phase2_response = await self._process_via_orchestrator(ctx, conv_id, db, streaming_callback, conv=conv)
            if _soft_warnings and not _phase2_response.fairness_warnings:
                _phase2_response.fairness_warnings = _soft_warnings

            _elapsed_ms = (time.monotonic() - _t0) * 1000
            _domain = _phase2_response.agent_used or "unknown"
            _perf_metrics.setdefault(_domain, []).append(_elapsed_ms)
            if len(_perf_metrics[_domain]) > 200:
                _perf_metrics[_domain] = _perf_metrics[_domain][-100:]
            logger.info(
                "[MainOrchestrator] response_time=%.1fms domain=%s intent=%s cache_hit=%s user=%s",
                _elapsed_ms, _domain, _phase2_response.intent_detected,
                getattr(_phase2_response, 'from_cache', False), ctx.user_id,
            )
            return _phase2_response

        except Exception as exc:
            logger.error(
                f"[MainOrchestrator] Unhandled error for user={ctx.user_id} "
                f"company={ctx.company_id} channel={ctx.channel}: {exc}",
                exc_info=True,
            )
            from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
            _error_msg = SystemPromptBuilder.build_error_response(
                user_name=getattr(ctx, "user_name", ""),
            )
            return ChatResponse(
                success=False,
                content=_error_msg,
                intent_detected="error",
                conversation_id=conv_id,
            )

    # ------------------------------------------------------------------
    # Phase 0 — PendingAction
    # ------------------------------------------------------------------

    async def _handle_pending_action(
        self, ctx: UniversalContext, conv_id: str
    ) -> ChatResponse | None:
        pending = pending_action_store.get(conv_id)
        if not pending:
            return None

        candidates = ctx.candidates or []
        candidates_count = len(candidates)

        # ── Aguardando confirmação ──
        if pending.awaiting_confirmation:
            if is_confirmation(ctx.message):
                config = ACTIONABLE_INTENTS.get(pending.intent, {})
                exec_result = await action_executor._execute_action(
                    pending.intent,
                    config,
                    pending.collected_params,
                    {"conversation_id": conv_id, "user_id": ctx.user_id},
                )
                pending_action_store.remove(conv_id)
                # LIA-A01: Interpret Phase 0 confirmation action results
                if exec_result and exec_result.status == "executed":
                    try:
                        _phase0_ctx = {
                            "user_name": getattr(ctx, "user_name", "") or "",
                            "user_role": getattr(ctx, "user_role", "") or "",
                        }
                        _interpreted = await self._interpret_action_result(ctx, exec_result, _phase0_ctx)
                        if _interpreted:
                            exec_result = ActionResult(
                                status=exec_result.status,
                                action_type=exec_result.action_type,
                                message=_interpreted,
                                data=exec_result.data,
                                candidates=getattr(exec_result, "candidates", None),
                            )
                    except Exception as e:
                        logger.debug("[LIA-A01] Phase 0 confirmation interpretation skipped: %s", e)
                return ChatResponse.from_action_result(
                    exec_result,
                    intent=pending.intent,
                    conv_id=conv_id,
                    suggested_prompts=_get_suggested_prompts(pending.intent, candidates_count, 0),
                )

            if is_rejection(ctx.message):
                pending_action_store.remove(conv_id)
                return ChatResponse(
                    success=True,
                    content="Ok, ação cancelada. Como posso te ajudar?",
                    agent_used="ActionExecutor",
                    intent_detected="cancelamento",
                    suggested_prompts=["Quem são os melhores candidatos?", "Busque perfis similares"],
                    conversation_id=conv_id,
                )

            # Mensagem não é confirmação nem rejeição — cancela e continua
            pending_action_store.remove(conv_id)
            return None

        # ── Coletando parâmetros faltantes ──
        if pending.missing_params:
            next_param = pending.next_missing_param()
            if next_param:
                extracted = await _extract_param_value(ctx.message, next_param, candidates)
                if extracted:
                    pending.add_param(next_param, extracted)

                    # Resolve contexto de candidato se necessário
                    if next_param == "candidate_id":
                        resolved = resolve_candidate_from_context(None, extracted, candidates)
                        if resolved:
                            pending.collected_params["candidate_name"] = resolved.get("name", "")
                            pending.collected_params["candidate_email"] = resolved.get("email", "")
                            if resolved.get("stage"):
                                pending.collected_params["from_stage"] = resolved["stage"]

                    if pending.is_complete:
                        config = ACTIONABLE_INTENTS.get(pending.intent, {})
                        if config.get("requires_confirmation", False):
                            summary = action_executor._build_confirmation_summary(
                                pending.intent, config, pending.collected_params
                            )
                            pending.awaiting_confirmation = True
                            pending.confirmation_summary = summary
                            pending_action_store.save(conv_id, pending)
                            return ChatResponse(
                                success=True,
                                content=summary["message"],
                                agent_used="ActionExecutor",
                                intent_detected=pending.intent,
                                conversation_id=conv_id,
                                needs_confirmation=True,
                                pending_action_id=pending.pending_id,
                            )
                        else:
                            exec_result = await action_executor._execute_action(
                                pending.intent,
                                config,
                                pending.collected_params,
                                {"conversation_id": conv_id, "user_id": ctx.user_id},
                            )
                            pending_action_store.remove(conv_id)
                            # LIA-A01: Interpret Phase 0 param-complete action results
                            if exec_result and exec_result.status == "executed":
                                try:
                                    _phase0_ctx = {
                                        "user_name": getattr(ctx, "user_name", "") or "",
                                        "user_role": getattr(ctx, "user_role", "") or "",
                                    }
                                    _interpreted = await self._interpret_action_result(ctx, exec_result, _phase0_ctx)
                                    if _interpreted:
                                        exec_result = ActionResult(
                                            status=exec_result.status,
                                            action_type=exec_result.action_type,
                                            message=_interpreted,
                                            data=exec_result.data,
                                            candidates=getattr(exec_result, "candidates", None),
                                        )
                                except Exception as e:
                                    logger.debug("[LIA-A01] Phase 0 param-complete interpretation skipped: %s", e)
                            return ChatResponse.from_action_result(
                                exec_result,
                                intent=pending.intent,
                                conv_id=conv_id,
                                suggested_prompts=_get_suggested_prompts(pending.intent, candidates_count, 0),
                            )
                    else:
                        # Ainda faltam params
                        pending_action_store.save(conv_id, pending)
                        next_param2 = pending.next_missing_param()
                        config = ACTIONABLE_INTENTS.get(pending.intent, {})
                        prompt_label = config.get("param_labels", {}).get(next_param2, next_param2)
                        return ChatResponse(
                            success=True,
                            content=f"Entendido. Agora preciso de: **{prompt_label}**",
                            agent_used="ActionExecutor",
                            intent_detected=pending.intent,
                            conversation_id=conv_id,
                            needs_params=True,
                            pending_action_id=pending.pending_id,
                        )

        pending_action_store.remove(conv_id)
        return None

    # ------------------------------------------------------------------
    # Phase 1 — ActionExecutor
    # ------------------------------------------------------------------

    async def _try_action_executor(
        self, ctx: UniversalContext, conv_id: str
    ) -> ChatResponse | None:
        candidates = ctx.candidates or []

        try:
            action_result: ActionResult = await action_executor.try_execute(
                message=ctx.message,
                context={
                    "candidates": candidates,
                    "selected_candidate_ids": ctx.selected_candidate_ids,
                    "job_context": ctx.job_context,
                    "conversation_id": conv_id,
                    "user_id": ctx.user_id,
                    "company_id": ctx.company_id,
                    "conversation_history": ctx.extra.get("conversation_history", []),
                },
            )
        except Exception as exc:
            logger.warning(f"[MainOrchestrator] ActionExecutor error: {exc}")
            return None

        if action_result.status == "not_actionable":
            return None

        if action_result.status in ("needs_params", "needs_confirmation"):
            if action_result.pending_action_id:
                pass  # PendingActionStore já foi atualizado pelo ActionExecutor
            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
            )

        if action_result.status == "executed":
            # LIA-A01: LLM interpretation of action results
            # Instead of returning raw action result, ask the LLM to generate a natural response
            try:
                # FIX-2: Build minimal context for interpretation (full orchestrator_context
                # is only available in Phase 2; here we extract what we can from ctx)
                _phase1_context = {
                    "user_name": getattr(ctx, "user_name", "") or "",
                    "user_role": getattr(ctx, "user_role", "") or "",
                    "tenant_id": getattr(ctx, "company_id", "") or "",
                }
                _interpreted = await self._interpret_action_result(ctx, action_result, _phase1_context)
                if _interpreted:
                    action_result = ActionResult(
                        status=action_result.status,
                        action_type=action_result.action_type,
                        message=_interpreted,
                        data=action_result.data,
                        candidates=action_result.candidates,
                    )
            except Exception as e:
                logger.debug("[LIA-A01] LLM interpretation skipped (fail-open): %s", e)

            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
                suggested_prompts=_get_suggested_prompts(
                    action_result.action_type or "", len(candidates), 0
                ),
            )

        return None

    # ------------------------------------------------------------------
    # LIA-A01 — LLM interpretation of action results
    # ------------------------------------------------------------------

    async def _interpret_action_result(
        self, ctx: UniversalContext, action_result: ActionResult, orchestrator_context: dict
    ) -> str | None:
        """LIA-A01: Use LLM to generate natural response from action result.

        Uses a direct prompt instead of SystemPromptBuilder to keep interpretation
        lightweight and avoid signature coupling. FIX-9: LLMService() is instantiated
        fresh here -- MainOrchestrator delegates LLM to Orchestrator/DomainWorkflow
        in Phase 2, so there is no shared instance available in Phases 0/1.
        """
        import asyncio
        import os as _os
        if _os.getenv("LIA_AGENTIC_INTERPRET", "true").lower() not in ("true", "1"):
            return None

        try:
            # FIX-1: Direct prompt -- no SystemPromptBuilder dependency
            user_name = orchestrator_context.get("user_name", "") or getattr(ctx, "user_name", "") or ""
            greeting = f"O usuario {user_name}" if user_name else "O usuario"

            interpretation_prompt = (
                "Voce e a LIA, assistente inteligente da WeDOTalent.\n"
                f"{greeting} pediu: {ctx.message}\n\n"
                f"A acao '{action_result.action_type}' foi executada com sucesso.\n"
                f"Resultado: {action_result.message}\n"
            )

            if action_result.data:
                import json
                try:
                    data_str = json.dumps(action_result.data, ensure_ascii=False, default=str)[:2000]
                    interpretation_prompt += f"Dados retornados: {data_str}\n"
                except Exception:
                    pass

            interpretation_prompt += (
                "\nGere uma resposta natural e contextualizada para o usuario. "
                "Seja conciso. Nao repita o que o usuario disse. "
                "Se houver dados, apresente-os de forma organizada."
            )

            from app.domains.ai.services.llm import LLMService
            llm_svc = LLMService()

            # FIX-7: Timeout to prevent slow LLM calls from blocking the response
            response = await asyncio.wait_for(
                llm_svc.generate(
                    prompt=interpretation_prompt,
                    provider="gemini",
                    max_tokens=500,
                ),
                timeout=10.0,
            )

            if response and response.strip():
                return response.strip()
        except asyncio.TimeoutError:
            logger.debug("[LIA-A01] Interpretation timed out after 10s")
        except Exception as e:
            logger.debug("[LIA-A01] Interpretation failed: %s", e)

        return None

        # ------------------------------------------------------------------
    async def _try_plan_via_service(
        self,
        ctx,
        conv_id: str,
        orchestrator_context: dict,
    ) -> "dict | None":
        """Sprint III.B — delegate to injected plan_service.

        Returns a V1-compatible response dict on success, or None so the caller
        falls through to V1 delegation (graceful degradation).

        Multi-tenancy: tenant_id from ctx.company_id, never from payload (LGPD/CLAUDE.md #1).
        """
        if self._plan_service is None:
            return None
        try:
            detected = self._plan_service.detect(ctx.message)
            if detected is None:
                return None

            tenant_id = str(ctx.company_id) if getattr(ctx, "company_id", None) else None
            user_id = str(getattr(ctx, "user_id", "system") or "system")

            plan_result = await self._plan_service.execute(
                detected,
                user_id=user_id,
                session_id=conv_id or "",
                tenant_id=tenant_id,
            )

            return {
                "success": plan_result.success,
                "message": plan_result.message,
                "intent": "plan:" + str(plan_result.pattern),
                "agent": "plan_executor",
                "agent_type": "execution_plan",
                "conversation_id": conv_id,
                "execution_plan": plan_result.summary,
                "suggested_prompts": list(plan_result.suggestions or []),
                "data": plan_result.data or {},
            }
        except Exception as exc:
            logger.warning(
                "[MainOrchestrator] _try_plan_via_service failed — falling through to V1: %s",
                exc,
            )
            return None

    # Phase 2 — Pipeline consolidado (sem delegação intermediária)
    # ------------------------------------------------------------------

    async def _process_via_orchestrator(
        self,
        ctx: UniversalContext,
        conv_id: str,
        db: Any,
        streaming_callback: Callable | None,
        conv: Any = None,
    ) -> ChatResponse:
        """
        Pipeline consolidado: ConversationMemory → CascadedRouter → DomainWorkflow.

        Elimina a delegação intermediária para Orchestrator.process_request_with_memory,
        inlining a gestão de memória diretamente aqui enquanto usa o Orchestrator
        somente para process_request (roteamento + execução de domínio).
        """
        from app.domains.ai.services.response_cache_service import response_cache_service

        orchestrator_context = ctx.to_orchestrator_context()

        _cache_key = await self._try_cache_lookup(ctx, conv_id, streaming_callback)
        if isinstance(_cache_key, ChatResponse):
            return _cache_key
        if streaming_callback:
            orchestrator_context["streaming_callback"] = streaming_callback

        # LIA-M01: Memory already setup in process() — only setup here if running standalone
        if conv is None and not ctx.skip_memory_persist:
            conv, conv_id = await self._setup_conversation_memory(ctx, conv_id, db, orchestrator_context)
        elif conv is not None and not ctx.skip_memory_persist:
            # Memory already setup — just enrich orchestrator_context with conversation data
            try:
                from app.domains.recruiter_assistant.services.conversation_memory import conversation_memory
                llm_ctx = await conversation_memory.get_context_for_llm(db=db, conversation_id=conv_id, max_messages=20)
                orchestrator_context.update({
                    "conversation_history": llm_ctx.get("messages", []),
                    "conversation_summary": llm_ctx.get("summary"),
                    "context_type": ctx.context_type,
                    "context_id": ctx.entity_id,
                })
            except Exception as _enrich_exc:
                logger.debug("[LIA-M01] Context enrichment skipped: %s", _enrich_exc)

        result = await self._route_with_tenant_llm(ctx, conv_id, db, orchestrator_context)

        if not ctx.skip_memory_persist:
            await self._persist_response(ctx, conv_id, conv, result, db)

        result.update({"conversation_id": conv_id})

        if isinstance(_cache_key, str) and result.get("success"):
            await self._write_cache(response_cache_service, _cache_key, result)

        await self._persist_candidate_list(conv_id, result)
        await self._audit_output(ctx, conv_id, result)

        result = await self._inject_module_tasting_hints(ctx, result, db)

        return ChatResponse.from_orchestrator_result(result, conv_id=conv_id)

    async def _try_cache_lookup(
        self,
        ctx: UniversalContext,
        conv_id: str,
        streaming_callback: Callable | None,
    ) -> str | ChatResponse | None:
        """Check response cache. Returns cache_key (str), ChatResponse (hit), or None."""
        if streaming_callback:
            return None
        try:
            from app.domains.ai.services.response_cache_service import response_cache_service
            from app.orchestrator.fast_router import FastRouter
            _fast = FastRouter()
            _fast_match = _fast.match(ctx.message or "")
            _detected_domain = _fast_match.domain_id if _fast_match else None
            if not (_detected_domain and _detected_domain in _CACHEABLE_DOMAINS):
                return None
            _cache_context = {
                "company_id": str(ctx.company_id or ""),
                "user_id": str(ctx.user_id or ""),
                "job_id": str(ctx.entity_id or "") if ctx.context_type == "job" else "",
                "candidate_id": str(ctx.entity_id or "") if ctx.context_type == "candidate" else "",
                "conversation_id": str(conv_id or ""),
            }
            _cache_key = response_cache_service.generate_cache_key(
                _detected_domain, _cache_context, ctx.message or "",
                company_id=str(ctx.company_id or ""),
            )
            _cached = await response_cache_service.get_cached_response(_cache_key)
            if _cached:
                logger.info("[MainOrchestrator] Cache HIT domain=%s key=%s", _detected_domain, _cache_key[:40])
                resp = ChatResponse(
                    success=True,
                    content=_cached.get("content", ""),
                    agent_used=_cached.get("agent_used", _detected_domain),
                    intent_detected=_cached.get("intent_detected", _detected_domain),
                    confidence=_cached.get("confidence", 1.0),
                    structured_data=StructuredDataAdapter.unwrap(_cached.get("structured_data")),
                    suggested_prompts=_cached.get("suggested_prompts", []),
                    conversation_id=conv_id,
                )
                resp.from_cache = True
                return resp
            return _cache_key
        except Exception as _cache_exc:
            logger.debug("[MainOrchestrator] Cache lookup skipped: %s", _cache_exc)
            return None

    async def _setup_conversation_memory(
        self,
        ctx: UniversalContext,
        conv_id: str,
        db: Any,
        orchestrator_context: dict[str, Any],
    ) -> tuple[Any, str]:
        """Load or create conversation, add user message, enrich context. Returns (conv, conv_id)."""
        from app.domains.recruiter_assistant.services.conversation_memory import conversation_memory
        try:
            if conv_id:
                conv = await conversation_memory.get_conversation(db=db, conversation_id=conv_id, include_messages=True)
                if not conv:
                    conv = await conversation_memory.get_or_create_conversation(
                        db=db, user_id=ctx.user_id, context_type=ctx.context_type, context_id=ctx.entity_id,
                    )
                    conv_id = str(conv.id)
            else:
                conv = await conversation_memory.get_or_create_conversation(
                    db=db, user_id=ctx.user_id, context_type=ctx.context_type, context_id=ctx.entity_id,
                )
                conv_id = str(conv.id)

            await conversation_memory.add_message(db=db, conversation_id=conv_id, role="user", content=ctx.message)
            llm_ctx = await conversation_memory.get_context_for_llm(db=db, conversation_id=conv_id, max_messages=20)
            orchestrator_context.update({
                "conversation_history": llm_ctx.get("messages", []),
                "conversation_summary": llm_ctx.get("summary"),
                "context_type": ctx.context_type,
                "context_id": ctx.entity_id,
            })
            return conv, conv_id
        except Exception as _mem_exc:
            logger.debug("[MainOrchestrator] ConversationMemory setup skipped: %s", _mem_exc)
            return None, conv_id

    async def _route_with_tenant_llm(
        self,
        ctx: UniversalContext,
        conv_id: str,
        db: Any,
        orchestrator_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Inject tenant LLM provider, route via orchestrator, then restore."""
        _llm_svc = getattr(self._orchestrator, "llm_service", None)
        _original_container = getattr(_llm_svc, "_tenant_container", None) if _llm_svc else None
        _original_tenant = getattr(_llm_svc, "_current_tenant", "") if _llm_svc else ""
        _tenant_id = str(ctx.company_id) if ctx.company_id else get_current_llm_tenant()

        if _tenant_id and _llm_svc:
            try:
                _tenant_config = await get_tenant_llm_config(_tenant_id)
                if _tenant_config:
                    _providers_cfg = _tenant_config.get("providers", {})
                    _api_keys = {
                        name: prov.get("api_key")
                        for name, prov in _providers_cfg.items()
                        if prov.get("api_key")
                    }
                    from app.shared.providers.llm_factory import ProviderContainer, TenantProviderRegistry
                    _registry = TenantProviderRegistry.get_instance()
                    _registry.remove_container(_tenant_id)
                    _container = ProviderContainer(
                        tenant_id=_tenant_id,
                        primary_provider=_tenant_config.get("primary_provider"),
                        fallback_order=_tenant_config.get("fallback_order"),
                        provider_api_keys=_api_keys if _api_keys else None,
                    )
                    _registry.register_container(_tenant_id, _container)
                    _llm_svc._tenant_container = _container
                    _llm_svc._current_tenant = _tenant_id
                    logger.info(
                        "[MainOrchestrator] Tenant LLM provider set: tenant=%s primary=%s",
                        _tenant_id, _container.primary_provider,
                    )
                else:
                    logger.debug("[MainOrchestrator] No tenant LLM config for %s — using global", _tenant_id)
            except Exception as _tenant_exc:
                logger.debug("[MainOrchestrator] Tenant LLM resolution failed for %s: %s — using global", _tenant_id, _tenant_exc)

        try:
            result = await self._orchestrator.process_request(
                user_id=ctx.user_id, message=ctx.message,
                conversation_id=conv_id, context=orchestrator_context,
            )
        finally:
            if _llm_svc:
                _llm_svc._tenant_container = _original_container
                _llm_svc._current_tenant = _original_tenant

        return result

    async def _persist_response(
        self, ctx: UniversalContext, conv_id: str, conv: Any, result: dict[str, Any], db: Any
    ) -> None:
        """Persist assistant response to conversation memory and commit."""
        from app.core.config import settings
        from app.domains.recruiter_assistant.services.conversation_memory import conversation_memory
        try:
            if result.get("success") and conv is not None:
                # M2 Item 1: Build rich metadata matching ChatRepository format
                _msg_metadata = {
                    "intent": result.get("intent", ""),
                    "entities": (result.get("result") or {}).get("data", {}).get("entities", {}),
                    "agent_used": result.get("agent", ""),
                    "confidence": result.get("confidence", 0),
                }
                _structured = (result.get("result") or {}).get("data", {})
                if _structured and (_structured.get("search_results") or _structured.get("response_plan")):
                    _msg_metadata["context_data"] = _structured
                if result.get("action_result"):
                    _msg_metadata["action_result"] = result["action_result"]
                if result.get("pending_action_id"):
                    _msg_metadata["pending_action"] = {
                        "pending_id": result.get("pending_action_id"),
                        "awaiting_confirmation": result.get("needs_confirmation", False),
                    }

                await conversation_memory.add_message(
                    db=db, conversation_id=conv_id, role="assistant",
                    content=result.get("message", result.get("content", "")),
                    intent=result.get("intent"),
                    metadata=_msg_metadata,
                )

                # M2 Item 2: Update conversation title, intent, workflow_data
                try:
                    from sqlalchemy import update as sa_update
                    from lia_models.conversation import Conversation as ConvModel
                    from uuid import UUID as _UUID
                    _conv_uuid = _UUID(conv_id) if isinstance(conv_id, str) else conv_id
                    _updates = {"updated_at": __import__("datetime").datetime.utcnow()}
                    if result.get("intent"):
                        _updates["intent"] = result["intent"]
                    _wf_data = (result.get("result") or {}).get("data", {})
                    if _wf_data:
                        _updates["workflow_data"] = _wf_data
                    if not getattr(conv, "title", None):
                        _updates["title"] = ctx.message[:100]
                    if _updates:
                        await db.execute(
                            sa_update(ConvModel).where(ConvModel.id == _conv_uuid).values(**_updates)
                        )
                except Exception as _upd_exc:
                    logger.warning("[MainOrchestrator] Conv update FAILED: %s", _upd_exc, exc_info=True)

                if (
                    getattr(conv, "message_count", None)
                    and conv.message_count % settings.ROUTER_SUMMARY_EVERY_N_MESSAGES == 0
                ):
                    try:
                        await conversation_memory.update_summary(
                            db=db, conversation_id=conv_id, llm_service=self._orchestrator.llm_service,
                        )
                    except Exception as exc:
                        logger.warning(
                            "[main_orchestrator] update_summary failed (memory lost) conv_id=%s: %s",
                            conv_id, exc, exc_info=True,
                        )
            await db.commit()
        except Exception as _persist_exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning("[MainOrchestrator] Memory persist FAILED: %s", _persist_exc, exc_info=True)

    async def _write_cache(self, cache_service: Any, cache_key: str, result: dict[str, Any]) -> None:
        """Write successful result to response cache."""
        try:
            _domain_for_ttl = result.get("agent_used") or result.get("domain_id") or ""
            _ttl = _CACHE_TTL_BY_DOMAIN.get(_domain_for_ttl, 300)
            await cache_service.cache_response(
                cache_key,
                {
                    "content": result.get("response", result.get("message", result.get("content", ""))),
                    "agent_used": result.get("agent_used", ""),
                    "intent_detected": result.get("intent_detected", result.get("intent", "")),
                    "confidence": result.get("confidence", 1.0),
                    "structured_data": result.get("structured_data"),
                    "suggested_prompts": result.get("suggested_prompts", []),
                },
                ttl=_ttl,
            )
        except Exception as _cw_exc:
            logger.debug("[MainOrchestrator] Cache write failed: %s", _cw_exc)

    async def _persist_candidate_list(self, conv_id: str, result: dict[str, Any]) -> None:
        """Persist candidate list to Redis (TTL 30min)."""
        _structured = result.get("structured_data") or {}
        candidates_in_result = (
            result.get("candidates")
            or (_structured.get("candidates") if isinstance(_structured, dict) else None)
            or []
        )
        if candidates_in_result:
            try:
                await candidate_list_store.set(conv_id, candidates_in_result)
            except Exception as exc:
                logger.debug("[MainOrchestrator] CandidateListStore set error: %s", exc)

    async def _audit_output(self, ctx: UniversalContext, conv_id: str, result: dict[str, Any]) -> None:
        """Audit output for high-impact actions (candidate/job mutations)."""
        _should_audit = bool(
            result.get("candidate_id") or result.get("job_id") or result.get("job_vacancy_id")
        )
        if _should_audit:
            try:
                from app.shared.compliance.audit_service import AuditService
                _audit_svc = AuditService()
                await _audit_svc.log_output(
                    company_id=str(ctx.company_id or ""),
                    session_id=conv_id,
                    agent_used=result.get("agent_used", "unknown"),
                    input_text=ctx.message or "",
                    output_text=result.get("content") or result.get("message", ""),
                    action_executed=result.get("action_executed"),
                    candidate_id=result.get("candidate_id"),
                    job_vacancy_id=result.get("job_id") or result.get("job_vacancy_id"),
                    fairness_flags=result.get("fairness_flags", []),
                )
            except Exception as _audit_err:
                logger.warning("Output audit failed (non-blocking): %s", _audit_err)

    _MODULE_TASTING_INTENTS: dict[str, list[str]] = {
        "talent_intelligence_pro": [
            "talent", "skills", "skill_analysis", "gap_analysis",
            "ontology", "market_intelligence", "busca", "sourcing",
        ],
        "internal_mobility": ["internal_mobility", "mobilidade_interna", "talent"],
        "interview_intelligence": ["interview", "entrevista", "screening"],
        "workforce_planning": ["workforce", "planning", "analytics", "previsão"],
        "candidate_nurture": [
            "nurture", "reengagement", "engagement", "crm",
            "candidato_passivo", "communication",
        ],
    }

    _MODULE_TASTING_SUGGESTIONS: dict[str, str] = {
        "talent_intelligence_pro": (
            "💡 **Talent Intelligence Pro** — Analise skills com ontologia de grafos, "
            "identifique gaps e obtenha market intelligence em tempo real."
        ),
        "internal_mobility": (
            "💡 **Internal Mobility** — Descubra talentos internos com matching "
            "por skills adjacentes e readiness scoring."
        ),
        "interview_intelligence": (
            "💡 **Interview Intelligence** — Análise de entrevistas com detecção "
            "de viés, mapeamento de competências e sentimento."
        ),
        "workforce_planning": (
            "💡 **Workforce Planning** — Previsão de contratação baseada em "
            "turnover, pipeline e cenários de crescimento."
        ),
        "candidate_nurture": (
            "💡 **Candidate Nurture** — Sequências automatizadas de engajamento "
            "para candidatos passivos com métricas de conversão."
        ),
    }

    async def _inject_module_tasting_hints(
        self,
        ctx: UniversalContext,
        result: dict[str, Any],
        db: Any,
    ) -> dict[str, Any]:
        if not result.get("success") or not ctx.company_id:
            return result

        try:
            from app.orchestrator.tasting_engine import tasting_engine, format_tasting_block

            detected_intent = result.get("intent_detected", result.get("intent", "")) or ""
            detected_domain = result.get("agent_used", result.get("domain_id", "")) or ""

            insights = await tasting_engine.generate_insights(
                ctx_company_id=str(ctx.company_id),
                ctx_message=ctx.message or "",
                ctx_intent=detected_intent,
                ctx_domain=detected_domain,
                ctx_entity_id=ctx.entity_id,
                ctx_entity_type=ctx.entity_type,
                ctx_candidates=ctx.candidates,
                ctx_job_context=ctx.job_context,
                result=result,
                db=db,
            )

            if insights:
                tasting_block = format_tasting_block(insights)
                primary_field = "response" if "response" in result else ("message" if "message" in result else "content")
                existing_text = result.get(primary_field, "")
                result[primary_field] = existing_text + tasting_block
                result["tasting_insights"] = [
                    {
                        "module_name": ins.module_name,
                        "module_label": ins.module_label,
                        "insight_type": ins.insight_type,
                        "summary": ins.summary,
                        "cta": ins.cta,
                        "badge": ins.badge,
                    }
                    for ins in insights
                ]
        except Exception as exc:
            logger.debug("[MainOrchestrator] Module tasting hints skipped: %s", exc)

        return result

    async def _try_fallback_react_substitute(
        self,
        v1_result: "dict",
        ctx: "Any",
        extra_kwargs: "dict",
    ) -> "dict":
        """Late-intercept: if V1 emits a technical stub message, ask
        ``_fallback_react_service`` for a natural-language substitute.

        Behaviour (Sprint III.D / ADR-019):
        - Non-technical V1 response → return v1_result unchanged.
        - No service injected → return v1_result unchanged.
        - Service raises / returns success=False → return v1_result (graceful).
        - Service succeeds → merge natural message + ``_fallback_substituted=True``,
          preserve V1 metadata (intent, conversation_id, etc.).
        """
        from app.orchestrator.heuristics import is_technical_response

        message = v1_result.get("message", "")
        if not is_technical_response(message):
            return v1_result

        svc = self._fallback_react_service
        if svc is None:
            return v1_result

        try:
            intent = v1_result.get("intent") or "general_chat"
            entities = (
                (v1_result.get("result") or {})
                .get("data", {})
                .get("entities", {})
            )
            company_id = extra_kwargs.get("company_id", "")

            fb_result = await svc.handle_directly(
                intent=intent,
                entities=entities,
                company_id=company_id,
                context=ctx,
            )

            if not (fb_result or {}).get("success"):
                return v1_result

            # Merge: replace message, add marker, keep V1 metadata
            merged = dict(v1_result)
            merged["message"] = fb_result.get("message", message)
            merged["_fallback_substituted"] = True
            return merged

        except Exception as exc:
            logger.debug(
                "[MainOrchestrator] _try_fallback_react_substitute exception (graceful): %s", exc
            )
            return v1_result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_suggested_prompts(intent: str, candidates_count: int, selected_count: int) -> list[str]:
    base_prompts = {
        "mover_candidato": ["Ver pipeline completo", "Quem mais está pronto para avançar?"],
        "reprovar_candidato": ["Ver outros candidatos", "Buscar perfis similares"],
        "enviar_email": ["Agendar entrevista", "Ver histórico de comunicações"],
        "agendar_entrevista": ["Ver agenda disponível", "Enviar confirmação ao candidato"],
        "create_job": ["Ver vagas abertas", "Configurar pipeline de triagem"],
    }
    if candidates_count > 0:
        return base_prompts.get(intent, ["Quem são os melhores candidatos?", "Comparar top 3"])
    return base_prompts.get(intent, ["Como posso te ajudar?"])


async def _extract_param_value(
    message: str, param_name: str, candidates: list[dict[str, Any]]
) -> str | None:
    """Extração simples de parâmetro da mensagem do usuário."""
    msg = message.strip()
    if not msg:
        return None

    # Candidato por nome na lista disponível
    if param_name == "candidate_id" and candidates:
        msg_lower = msg.lower()
        for c in candidates:
            name = c.get("name", "")
            if name and name.lower() in msg_lower:
                return str(c.get("id", ""))

    # Fallback: retorna a mensagem bruta como valor
    return msg if len(msg) <= 200 else msg[:200]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_main_orchestrator_instance: MainOrchestrator | None = None


def get_main_orchestrator(orchestrator: Any = None) -> MainOrchestrator:
    global _main_orchestrator_instance
    if _main_orchestrator_instance is None:
        if orchestrator is None:
            from app.api.orchestrator_routes import get_orchestrator
            orchestrator = get_orchestrator()
        _main_orchestrator_instance = MainOrchestrator(orchestrator)
    return _main_orchestrator_instance




# ---------------------------------------------------------------------------
# _is_fallback_react_enabled — feature flag for LIA_V2_USE_FALLBACK_REACT
# ---------------------------------------------------------------------------

def _is_fallback_react_enabled() -> bool:
    """Check the ``LIA_V2_USE_FALLBACK_REACT`` feature flag.

    Reads the environment variable and returns ``True`` only when it is set
    to a recognised truthy value.  The check is case-insensitive.

    Returns:
        True when the env var is one of ``{"1", "true", "yes", "on"}``,
        False in all other cases (absent, empty, "false", "0", …).
    """
    import os

    val = os.getenv("LIA_V2_USE_FALLBACK_REACT", "").lower().strip()
    return val in {"1", "true", "yes", "on"}
