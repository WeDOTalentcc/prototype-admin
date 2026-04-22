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
    # Onda 2.4 Init V (2026-04-21) — Reasoning transparency
    citations: list[dict[str, Any]] = Field(default_factory=list)
    has_citations: bool = False
    # Onda 3.2 G3 (2026-04-21) — HITL checkpoint surfacing
    hitl_checkpoint: dict[str, Any] | None = None

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


def _inject_nav_ui_action(response: "ChatResponse", message: str) -> "ChatResponse":
    """Post-process: add navigate_to ui_action when user intent is navigation (LIA-NAV-01)."""
    if response.ui_action:
        return response  # already set by a domain agent
    try:
        from app.orchestrator.navigation_intent import detect_navigation_intent
        _nav = detect_navigation_intent(message)
        if _nav.page and _nav.confidence >= 0.75:
            response.ui_action = "navigate_to"
            response.ui_action_params = {"page": _nav.page, "hint": _nav.hint}
    except Exception:
        pass
    return response

class MainOrchestrator:
    """
    Entry point único consolidado para todas as mensagens da LIA.

    Recebe UniversalContext (normalizado pelo ContextAdapter) e processa através
    do pipeline unificado, sem delegar para Orchestrator.process_request_with_memory
    como camada intermediária. O Orchestrator permanece como motor de roteamento
    e execução de domínio, mas a gestão de memória e o fluxo de fases são
    controlados aqui.
    """

    def __init__(self, orchestrator: Any) -> None:
        self._orchestrator = orchestrator
        self._fairness_guard = FairnessGuard()
        self._tenant_context_service = TenantContextService()

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
                    _mem_ctx: dict = {}
                    conv, conv_id = await self._setup_conversation_memory(ctx, conv_id, db, _mem_ctx)
                    # Inject loaded history into ctx.extra so agents can access it (Bug: was passing {} and discarding)
                    if _mem_ctx.get("conversation_history"):
                        ctx.extra["conversation_history"] = _mem_ctx["conversation_history"]
                    if _mem_ctx.get("conversation_summary"):
                        ctx.extra["conversation_summary"] = _mem_ctx["conversation_summary"]
                except Exception as e:
                    logger.warning("[LIA-M01] Memory setup failed (non-blocking): %s", e)

            # Onda 4.3 III.B (2026-04-21) — Hydrate recruiter preferences from
            # conversation_summaries.user_preferences (episodic memory Init III MVP).
            # Consumed downstream by persona rendering + routing heuristics.
            try:
                _prefs = await self._hydrate_recruiter_preferences(ctx, db)
                if _prefs:
                    ctx.extra["recruiter_prefs"] = _prefs
                    logger.debug(
                        "[III.B] recruiter prefs hydrated user=%s keys=%s",
                        ctx.user_id, list(_prefs.keys()),
                    )
            except Exception as _hydrate_exc:
                logger.debug(
                    "[III.B] hydrate skipped (non-fatal): %s", _hydrate_exc,
                )

            # Onda 4.4 IV.B (2026-04-21) — Proactive agenda briefing on greeting.
            # When user message is a greeting pattern, fetch daily briefing
            # (cached 5min) and inject summary into extra_instructions so the
            # persona's ## Saudação Inicial section (FIX 29) surfaces it.
            try:
                _briefing_summary = await self._maybe_build_briefing_context(ctx, db)
                if _briefing_summary:
                    ctx.extra["briefing_context"] = _briefing_summary
                    _existing = ctx.extra.get("extra_instructions", "") or ""
                    _suffix = f"\n\nContexto pra saudação: {_briefing_summary}"
                    ctx.extra["extra_instructions"] = (_existing + _suffix).strip()
                    logger.info(
                        "[IV.B] briefing injected user=%s len=%d",
                        ctx.user_id, len(_briefing_summary),
                    )
            except Exception as _briefing_exc:
                logger.debug(
                    "[IV.B] briefing skipped (non-fatal): %s", _briefing_exc,
                )

            # FIX 31 v2 (2026-04-21) — Wire memory_resolver BEFORE all phases.
            # Earlier wiring was inside _process_via_orchestrator (Phase 2) but
            # most chat turns trigger Phase 1.5 Agentic Loop (LIA-A04) which
            # returns before reaching Phase 2. Moving it here ensures every
            # phase's downstream LLM invocation sees enriched messages
            # (pronouns / positional / affirmations / quantifiers resolved).
            try:
                from app.orchestrator.memory_resolver import memory_resolver as _mem_resolver
                _enriched_message, _was_resolved = await _mem_resolver.resolve(
                    ctx.message,
                    session_id=conv_id,
                    conversation_state=getattr(ctx, "conversation_state", None),
                )
                if _was_resolved:
                    logger.info(
                        "[MainOrchestrator] FIX 31 memory enrichment applied: "
                        "conv=%s raw_len=%d enriched_len=%d",
                        conv_id, len(ctx.message), len(_enriched_message),
                    )
                    ctx.message = _enriched_message
                    # Also set extra flag so downstream phases can log/branch
                    ctx.extra["memory_enrichment_applied"] = True
            except Exception as _mr_exc:
                logger.debug(
                    "[MainOrchestrator] FIX 31 memory_resolver skipped (non-fatal): %s",
                    _mr_exc,
                )

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

            # Contexts with dedicated domain agents — skip generic phases (1, 1.5)
            _DOMAIN_SPECIFIC_CONTEXTS = {"company_settings", "settings_config", "hiring_policy"}

            # ── Phase 1: ActionExecutor ────────────────────────────────────
            action_response = None
            if ctx.context_type not in _DOMAIN_SPECIFIC_CONTEXTS:
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

            # ── Phase 1.5: Agentic Tool Calling (LIA-A04) ──────────────────
            # If Phase 1 did not match, let the LLM decide whether to call tools
            # via function calling. Feature-flagged: LIA_AGENTIC_LOOP=true
            _skip_agentic = ctx.context_type in _DOMAIN_SPECIFIC_CONTEXTS
            import os as _os_flag
            if not _skip_agentic and _os_flag.getenv("LIA_AGENTIC_LOOP", "true").lower() not in ("false", "0"):
                try:
                    from app.orchestrator.agentic_loop import agentic_loop

                    # LIA-LLM-1: Respect Choose Your AI — use tenant's chat provider
                    _agentic_provider = "gemini"
                    _loop_company_id = getattr(ctx, "company_id", None)
                    if _loop_company_id:
                        try:
                            from app.shared.tenant_llm_context import get_tenant_llm_config as _get_llm_cfg
                            _tenant_cfg = await _get_llm_cfg(_loop_company_id)
                            if _tenant_cfg:
                                _agentic_provider = (
                                    _tenant_cfg.get("routing", {}).get("chat")
                                    or _tenant_cfg.get("primary_provider")
                                    or "gemini"
                                )
                        except Exception:
                            pass  # Fail-open: use gemini default

                    # D10 — Pre-condition check for proactive assistance
                    _proactive_hints_text = ""
                    _proactive_hints_payload: list[dict] = []
                    _agent_type = "orchestrator"
                    _ONBOARDING_HINT_TYPES = {
                        "missing_company_id",
                        "incomplete_company_profile",
                        "company_website_missing",
                        "culture_profile_missing",
                        "benefits_catalog_empty",
                        "hiring_policy_missing",
                    }
                    try:
                        from app.orchestrator.precondition_checker import precondition_checker
                        _hints = await precondition_checker.check(ctx)
                        if _hints:
                            _proactive_hints_text = (
                                "## Sugestoes Proativas (detectadas pelo sistema)\n"
                                "Voce DEVE mencionar estas proativamente se relevantes ao que o recrutador pediu:\n\n"
                                + "\n".join(f"- [{h.severity}] {h.message}" for h in _hints)
                            )
                            # FIX 14 — Preserve hint signal WITHOUT hijacking agent_type.
                            # Previous behavior forced _agent_type = "company_settings"
                            # whenever any onboarding hint was detected. This broke
                            # multi-turn conversations: "pode sim" after a search turn
                            # was routed to company_settings and responded about
                            # cultural profile instead of continuing search.
                            #
                            # Hints remain visible to the LLM via _proactive_hints_text
                            # (see `extra_instructions` below). The LLM decides whether
                            # to mention onboarding based on CONTEXT RELEVANCE, not a
                            # hard override that ignores the cascade router's decision.
                            _onboarding_hints_detected = [h.type for h in _hints if h.type in _ONBOARDING_HINT_TYPES]
                            if _onboarding_hints_detected:
                                logger.info(
                                    "[PreConditionChecker] Onboarding hints injected (no delegation override)",
                                    extra={
                                        "company_id": _loop_company_id,
                                        "onboarding_hints": _onboarding_hints_detected,
                                        "total_hints": len(_hints),
                                        "agent_type": _agent_type,
                                    },
                                )
                            # Structured payload for frontend rendering (NavigationHintCard / proactive-insight-card)
                            _proactive_hints_payload = [
                                {
                                    "type": h.type,
                                    "message": h.message,
                                    "severity": h.severity,
                                    "action": h.action,
                                    "metadata": h.metadata,
                                }
                                for h in _hints
                            ]
                            # Save for downstream WebSocket emitter
                            ctx.extra["proactive_hints"] = _proactive_hints_payload
                            logger.info("[PreConditionChecker] %d proactive hint(s) generated", len(_hints))
                    except Exception as _pc_exc:
                        logger.debug("[PreConditionChecker] check skipped: %s", _pc_exc)

                    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
                    _system_prompt = SystemPromptBuilder.build(
                        agent_type=_agent_type,
                        company_id=_loop_company_id or "",
                        tenant_context_snippet=getattr(ctx, "tenant_context_snippet", "") or ctx.extra.get("tenant_context", ""),
                        user_name=getattr(ctx, "user_name", ""),
                        user_role=getattr(ctx, "user_role", ""),
                        conversation_history=ctx.extra.get("conversation_history", []),
                        conversation_state=ctx.conversation_state,
                        context_page=getattr(ctx, "context_page", "general") or "general",
                        extra_instructions=_proactive_hints_text,
                    )
                    _agentic_result = await agentic_loop.run(
                        user_message=ctx.message,
                        system_prompt=_system_prompt,
                        conversation_history=ctx.extra.get("conversation_history", []),
                        company_id=_loop_company_id,
                        user_id=getattr(ctx, "user_id", None),
                        provider=_agentic_provider,
                    )

                    if _agentic_result and _agentic_result.get("response"):
                        # Task B (2026-04-21): Removed dead P2#7 onboarding telemetry block
                        # that depended on `_agent_type == "company_settings"`. After FIX 14,
                        # this condition is never True (agent_type hijack removed).
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
                            except Exception:
                                pass

                        # FIX 12 / G8 — Detect pending_hitl_confirmation in any tool_call
                        # and promote to top-level `hitl_pending` in structured_data so the
                        # frontend can render a confirmation prompt.
                        _tool_calls = _agentic_result.get("tool_calls_made", []) or []
                        _hitl_pending: list[dict[str, Any]] = []
                        for _tc in _tool_calls:
                            _tc_result = _tc.get("result") if isinstance(_tc, dict) else None
                            if not isinstance(_tc_result, dict):
                                continue
                            _inner = _tc_result.get("result") if isinstance(_tc_result.get("result"), dict) else _tc_result
                            if isinstance(_inner, dict) and _inner.get("status") == "pending_hitl_confirmation":
                                _hitl_pending.append({
                                    "tool_name": _tc.get("name"),
                                    "parameters": _tc.get("parameters"),
                                    "governance_tags": _inner.get("governance_tags", []),
                                    "message": _inner.get("message"),
                                })
                                # Also emit audit event
                                try:
                                    from app.shared.observability.tool_metrics import emit_hitl_pending
                                    emit_hitl_pending(
                                        tool_name=_tc.get("name"),
                                        company_id=getattr(ctx, "company_id", None) if "ctx" in dir() else None,
                                        governance_tags=_inner.get("governance_tags", []),
                                        conversation_id=conv_id,
                                    )
                                except Exception:
                                    pass

                        _structured_data = {
                            "tool_calls": _tool_calls,
                            "iterations": _agentic_result.get("iterations", 0),
                        }
                        if _hitl_pending:
                            _structured_data["hitl_pending"] = _hitl_pending

                        # Onda 4.5 V.B (2026-04-21) — build citations from tool_calls
                        # for ChatResponse.citations field. Reasoning transparency
                        # producer (Init V) + consumer wiring = complete pipeline.
                        _citations: list[dict[str, Any]] = []
                        try:
                            from app.orchestrator.citation_processor import build_citations_from_tool_calls
                            _citations = build_citations_from_tool_calls(
                                _tool_calls,
                                response_text=_agentic_result.get("response", ""),
                            )
                        except Exception as _cite_exc:
                            logger.debug("[V.B] citation build skipped: %s", _cite_exc)

                        # Onda 4.6 G3.B (2026-04-21) — HITL checkpoint for frontend.
                        # When tool execution surfaced pending_hitl_confirmation,
                        # build canonical checkpoint so frontend renders approval UI.
                        # Takes FIRST pending entry (multiple concurrent HITL rare).
                        _hitl_checkpoint: dict[str, Any] | None = None
                        if _hitl_pending:
                            try:
                                from app.orchestrator.hitl import build_hitl_checkpoint
                                _first = _hitl_pending[0]
                                _hitl_checkpoint = build_hitl_checkpoint(
                                    tool_name=_first.get("tool_name", ""),
                                    tool_params=_first.get("parameters") or {},
                                    governance_tags=_first.get("governance_tags") or [],
                                    reason=_first.get("message"),
                                )
                            except Exception as _hitl_exc:
                                logger.debug("[G3.B] hitl checkpoint skipped: %s", _hitl_exc)

                        _resp = ChatResponse(
                            success=True,
                            content=_agentic_result["response"],
                            intent_detected="agentic_tool_call",
                            conversation_id=conv_id,
                            action_executed=bool(_tool_calls),
                            needs_confirmation=bool(_hitl_pending),
                            structured_data=_structured_data,
                            citations=_citations,
                            has_citations=bool(_citations),
                            hitl_checkpoint=_hitl_checkpoint,
                        )
                        if _soft_warnings:
                            _resp.fairness_warnings = _soft_warnings
                        return _inject_nav_ui_action(_resp, ctx.message)
                except Exception as exc:
                    exc_str = str(exc).lower()
                    if any(kw in exc_str for kw in ("safety", "blocked", "harm", "jailbreak", "policy", "finishreasonrecitation")):
                        return ChatResponse(
                            success=True,
                            content="Minhas diretrizes de funcionamento s\u00e3o confidenciais, mas posso te contar o que sou capaz de fazer. Como posso ajudar com seu recrutamento?",
                            intent_detected="jailbreak_refused",
                            conversation_id=conv_id,
                        )
                    logger.debug("[LIA-A04] Agentic loop skipped: %s", exc)

            # ── Phase 2: Orchestrator completo ─────────────────────────────
            _phase2_response = await self._process_via_orchestrator(ctx, conv_id, db, streaming_callback, conv=conv)
            # Update ConversationState with entity data from Phase 2 result
            if ctx.conversation_state and _phase2_response.structured_data and isinstance(_phase2_response.structured_data, dict):
                try:
                    ctx.conversation_state.update_after_action(
                        _phase2_response.intent_detected or "",
                        _phase2_response.agent_used or "",
                        _phase2_response.structured_data,
                    )
                except Exception:
                    pass
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
            return _inject_nav_ui_action(_phase2_response, ctx.message)

        except Exception as exc:
            logger.error(
                f"[MainOrchestrator] Unhandled error for user={ctx.user_id} "
                f"company={ctx.company_id} channel={ctx.channel}: {exc}",
                exc_info=True,
            )
            # Onda 4.7 VII.B (2026-04-21) — try error_policies first.
            # If apply_policy matches a canonical policy (timeout/empty_result/
            # enum_error/permission_denied/tenant_mismatch), use its PT-BR response
            # template with retry_hint + severity in structured_data.
            # Fallback: existing SystemPromptBuilder.build_error_response.
            try:
                from app.orchestrator.error_policies import apply_policy, resolve_policy
                _matched_policy = resolve_policy(exc)
                if _matched_policy is not None:
                    _applied = apply_policy(exc)
                    return ChatResponse(
                        success=False,
                        content=_applied["response"],
                        intent_detected="error_recovery",
                        conversation_id=conv_id,
                        structured_data={
                            "policy_id": _applied.get("policy_id"),
                            "severity": _applied.get("severity"),
                            "retry_hint": _applied.get("retry_hint"),
                        },
                    )
            except Exception as _pol_exc:
                logger.debug("[VII.B] error_policies apply skipped: %s", _pol_exc)

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

        # Task #726 — meta-question gate. Capability questions like
        # "consegue buscar candidatos?" must NOT execute the underlying action
        # with the question fragment as the query. Intercept and return a
        # deterministic informational reply (no LLM call, no DB hit).
        #
        # Why HERE and not in fast_router: the canonical-fix audit traced the
        # original symptom to `action_executor/utils.py::_detect_intent_from_message`
        # matching `MESSAGE_INTENT_PATTERNS.buscar_candidatos` BEFORE fast_router
        # ever ran. fast_router only handles cross-domain routing; the per-message
        # intent regex lives inside ActionExecutor. Hooking the gate here
        # short-circuits BOTH the regex dispatch and the downstream LLM cascade
        # in a single place — a deeper fix in fast_router would not reach
        # ActionExecutor's local pattern table.
        # FIX 16 — Correction detector (must run BEFORE meta_question_detector).
        # If user is correcting a previous LIA turn ("não, quis dizer X",
        # "estamos falando de X e nao Y"), we must short-circuit with a
        # clarification BEFORE cascade router interprets the correction as
        # a literal search query.
        try:
            from app.orchestrator.correction_detector import detect_user_correction
            _corr = detect_user_correction(ctx.message or "")
            if _corr is not None:
                return ChatResponse(
                    success=True,
                    content=_corr.reply,
                    agent_used="correction_gate",
                    intent_detected="user_correction",
                    confidence=0.9,
                    conversation_id=conv_id,
                    needs_clarification=True if hasattr(ChatResponse, "needs_clarification") else False,
                )
        except Exception as _corr_exc:  # fail-open — never block on detector bugs
            logger.debug("[correction_detector] skipped: %s", _corr_exc)

        try:
            from app.orchestrator.meta_question_detector import (
                detect_meta_capability_question,
            )
            _meta = detect_meta_capability_question(ctx.message or "")
            if _meta is not None:
                return ChatResponse(
                    success=True,
                    content=_meta.reply,
                    agent_used="meta_question_gate",
                    intent_detected="meta_capability_question",
                    confidence=0.95,
                    conversation_id=conv_id,
                )
        except Exception as _meta_exc:  # fail-open — never block on detector bugs
            logger.debug("[meta_question] detector skipped: %s", _meta_exc)

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
                    "entity_id": ctx.entity_id,
                    "entity_type": getattr(ctx, "entity_type", "") or getattr(ctx, "context_type", ""),
                },
            )
        except Exception as exc:
            logger.warning(f"[MainOrchestrator] ActionExecutor error: {exc}")
            return None

        if action_result.status == "not_actionable":
            return None

        if action_result.status in ("needs_params", "needs_confirmation", "pending"):
            if action_result.pending_action_id:
                pass  # PendingActionStore já foi atualizado pelo ActionExecutor
            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
            )

        if action_result.status == "error":
            # Return error message directly — do not fall through to Phase 2
            # Phase 2 would generate a misleading "preciso do ID" response
            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
            )

        if action_result.status == "executed":
            # LIA-A01: LLM interpretation of action results
            # Instead of returning raw action result, ask the LLM to generate a natural response
            try:
                # Skip LLM for direct-response actions (identity) to prevent Gemini identity override
                if action_result.action_type in ("respond_identity",):
                    raise Exception("skip_llm_direct_response")
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

            # Update ConversationState with entity data from action result
            if ctx.conversation_state and action_result.data and isinstance(action_result.data, dict):
                try:
                    ctx.conversation_state.update_after_action(
                        action_result.action_type or "",
                        ctx.context_type or "",
                        action_result.data,
                    )
                except Exception:
                    pass

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

        # Don't cache low-confidence fallback/clarification responses — they cause eval oscillation
        _resp_text = result.get("content", "") or result.get("response", "") or ""
        _is_fallback_resp = (
            "Não tenho certeza" in _resp_text
            or "Pode reformular" in _resp_text
            or "nao tenho certeza" in _resp_text.lower()
        )
        if isinstance(_cache_key, str) and result.get("success") and not _is_fallback_resp:
            await self._write_cache(response_cache_service, _cache_key, result)

        await self._persist_candidate_list(conv_id, result)
        await self._audit_output(ctx, conv_id, result)

        result = await self._inject_module_tasting_hints(ctx, result, db)

        # LIA-NAV-01: Inject navigation ui_action when message targets a platform page.
        # Only fires when the orchestrator did not already set ui_action.
        if not result.get("ui_action"):
            try:
                from app.orchestrator.navigation_intent import detect_navigation_intent
                _nav = detect_navigation_intent(ctx.message)
                if _nav.page and _nav.confidence >= 0.75:
                    result["ui_action"] = "navigate_to"
                    result["ui_action_params"] = {"page": _nav.page, "hint": _nav.hint}
            except Exception as _nav_exc:
                logger.debug("[LIA-NAV-01] Navigation intent detection skipped: %s", _nav_exc)

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
                    structured_data=_cached.get("structured_data"),
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
            logger.warning("[MainOrchestrator] ConversationMemory setup failed — conversation history lost: %s", _mem_exc)
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
                        # Audit task #545 — billing por empresa para
                        # sumarização de conversas do orchestrator.
                        _company_for_summary = getattr(ctx, "company_id", None)
                        await conversation_memory.update_summary(
                            db=db, conversation_id=conv_id,
                            tracking_context={
                                "company_id": str(_company_for_summary),
                                "user_id": getattr(ctx, "user_id", None),
                            } if _company_for_summary else None,
                        )
                    except Exception:
                        pass
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

    async def _hydrate_recruiter_preferences(self, ctx: Any, db: Any) -> dict[str, Any] | None:
        """Onda 4.3 III.B — Read user_preferences from latest ConversationSummary.

        Returns a dict with structured prefs (preferred_top_n, briefing_style,
        communication_channel, etc.) — values filtered through the
        recruiter_preferences get_preference API so PII/schema guards apply.

        Returns None on: no user_id, query failure, empty row.
        Fail-safe: never raises (caller wraps in try/except regardless).
        """
        if not ctx.user_id:
            return None
        try:
            from app.shared.memory.recruiter_preferences import get_preference
            from sqlalchemy import select as _select
            from lia_models.conversation import Conversation, ConversationSummary

            _stmt = (
                _select(ConversationSummary)
                .join(Conversation, ConversationSummary.conversation_id == Conversation.id)
                .where(Conversation.user_id == ctx.user_id)
                .order_by(ConversationSummary.created_at.desc())
                .limit(1)
            )
            _res = await db.execute(_stmt)
            _row = _res.scalar_one_or_none()
            _raw = (_row.user_preferences if _row else {}) or {}
            if not isinstance(_raw, dict):
                return None

            return {
                "preferred_top_n": get_preference(_raw, "preferred_top_n", default=5),
                "briefing_style": get_preference(_raw, "briefing_style", default="short"),
                "communication_channel": get_preference(_raw, "communication_channel", default="email"),
                "locale_preference": get_preference(_raw, "locale_preference", default="pt-BR"),
                "favored_stages": get_preference(_raw, "favored_stages", default=[]),
            }
        except Exception as _e:
            logger.debug("[III.B] _hydrate_recruiter_preferences failed: %s", _e)
            return None

    _GREETING_PATTERNS: set[str] = {
        "oi", "olá", "ola", "hello", "hi",
        "bom dia", "boa tarde", "boa noite",
        "oi lia", "olá lia",
    }

    async def _maybe_build_briefing_context(self, ctx: Any, db: Any) -> str | None:
        """Onda 4.4 IV.B — Return briefing summary when message is a greeting.

        Returns None when:
          - message is not a greeting pattern
          - briefing service unavailable / exception
          - briefing returns empty / formatted string empty
        """
        msg = (ctx.message or "").lower().strip().rstrip("!?.,")
        if not msg:
            return None
        # Match whole-word greeting OR very short (≤12 chars) message containing greeting token
        _is_greeting = (
            msg in self._GREETING_PATTERNS
            or (len(msg) <= 14 and any(g in msg for g in ("oi", "olá", "ola", "bom dia", "boa tarde", "boa noite")))
        )
        if not _is_greeting:
            return None
        try:
            from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
                get_cached_briefing,
                format_briefing_for_greeting,
            )
            _briefing = await get_cached_briefing(
                user_id=str(ctx.user_id) if ctx.user_id else "",
                company_id=str(ctx.company_id) if ctx.company_id else "",
                db=db,
            )
            _summary = format_briefing_for_greeting(_briefing)
            return _summary or None
        except Exception as _e:
            logger.debug("[IV.B] _maybe_build_briefing_context failed: %s", _e)
            return None


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


# FIX 25 (2026-04-21) — Enum-aware parameter normalizers.
# Maps param_name → normalizer fn. When a pending action collects a param
# with an entry here, the raw user message is coerced to the canonical
# enum value (e.g. "orçamento" → "budget") BEFORE being stored in
# collected_params. This ensures downstream tool calls + LLM context
# always see normalized values.
_PARAM_NORMALIZERS: dict[str, Any] = {}
try:
    from app.domains.job_management.tools.job_tools import _normalize_close_reason
    _PARAM_NORMALIZERS["reason"] = _normalize_close_reason
except Exception:  # pragma: no cover — defensive for partial imports
    pass


async def _extract_param_value(
    message: str, param_name: str, candidates: list[dict[str, Any]]
) -> str | None:
    """Extração simples de parâmetro da mensagem do usuário.

    FIX 25 (2026-04-21): quando o param tem um normalizer registrado em
    _PARAM_NORMALIZERS, coerce o valor cru para o enum canônico antes de
    devolver. Isso impede que collected_params guarde variantes soltas
    (ex.: "orçamento") enquanto downstream espera canônico ("budget").
    """
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

    # FIX 25: enum-aware coercion when a normalizer exists for this param.
    normalizer = _PARAM_NORMALIZERS.get(param_name)
    if normalizer is not None:
        coerced = normalizer(msg)
        if coerced is not None:
            return coerced
        # Normalizer said unknown → fall through to raw passthrough.
        # Higher-level caller (close_job entry) will reject with enum-hint
        # message if the tool is eventually invoked with invalid value.

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
