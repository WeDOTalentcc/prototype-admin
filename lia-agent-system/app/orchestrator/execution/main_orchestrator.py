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

from app.shared.observability.tracing import trace_span
from app.shared.chat_types import StructuredDataAdapter
from app.orchestrator.action_executor import (
    ACTIONABLE_INTENTS,
    ActionResult,
    action_executor,
    is_confirmation,
    is_rejection,
    resolve_candidate_from_context,
)
from app.orchestrator.context.context_adapter import UniversalContext
from app.orchestrator.execution.pending_action import pending_action_store
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
# ---------------------------------------------------------------------------
# Task #811 — severity-based delegation to company_settings agent
# Task #817 — canonical contract: exported for audit tests
# ---------------------------------------------------------------------------

#: Intents that route the turn to the company_settings/onboarding agent.
#: Stored in LOWERCASE so they never collide with IntentType/EnhancedIntentType
#: (which emit UPPERCASE values).
_COMPANY_SETTINGS_INTENTS: frozenset[str] = frozenset({
    "company_settings",
    "configure_company",
    "settings_config",
    "hiring_policy",
})


def _decide_agent_type_from_hints(
    hints: list,
    intent: str = "",
) -> "tuple[str, list, list]":
    """Decide which agent should handle a turn based on pre-condition hints.

    Args:
        hints: List of hint objects with ``.severity`` attribute.
        intent: Normalized or raw intent string from the classifier.

    Returns:
        Tuple of (agent_type, blocking_hints, informational_hints) where:
          - ``agent_type``: "company_settings" or "orchestrator"
          - ``blocking_hints``: hints with severity "warning" or "critical"
          - ``informational_hints``: hints with severity "info" or lower

    Routing rules (Task #811):
      1. If the intent (post-lower/strip) is in _COMPANY_SETTINGS_INTENTS,
         route to company_settings regardless of hints.
      2. If any hint has severity "warning" or "critical", route to
         company_settings so the recruiter can resolve the blocker first.
      3. Otherwise, route to "orchestrator" (normal flow).
    """
    normalized = (intent or "").strip().lower()
    if normalized in _COMPANY_SETTINGS_INTENTS:
        return ("company_settings", [], [])

    blocking = [h for h in hints if getattr(h, "severity", "info") in ("warning", "critical")]
    informational = [h for h in hints if getattr(h, "severity", "info") not in ("warning", "critical")]

    if blocking:
        return ("company_settings", blocking, informational)

    return ("orchestrator", [], informational)


def _is_plan_service_enabled() -> bool:
    """Check if the new PlanService orchestration path is enabled.

    # UC-P3-14: task_planner active via LIA_V2_USE_PLAN_SERVICE flag.
    # Promotion to production without flag: 2026-07-01
    # To promote: set LIA_V2_USE_PLAN_SERVICE=true in production env
    # and remove this gate once stable for 2 weeks.

    Default: False (backward-compatible). Set LIA_V2_USE_PLAN_SERVICE=true
    to enable PlanService-based orchestration (Sprint III-B rollout).
    """
    # W3-023 (2026-05-23): canary log pra Plan&Execute promotion.
    # Pre-flip telemetry: detect quem está usando LIA_V2_USE_PLAN_SERVICE=true.
    # Quando count em prod estabilizar >0 por 1 sprint, flip default safe.
    import os as _os_w3023
    _flag_v3 = _os_w3023.environ.get("LIA_V2_USE_PLAN_SERVICE", "").lower() in ("true", "1", "yes")
    _env_w3023 = _os_w3023.environ.get("APP_ENV", "development")
    if _flag_v3 and _env_w3023 in ("production", "prod", "staging"):
        # Emit em log.info pra Sentry breadcrumb visibility
        import logging as _log_w3023
        _log_w3023.getLogger(__name__).info(
            "[W3-023 CANARY] LIA_V2_USE_PLAN_SERVICE=true ativo em %s · Plan&Execute path",
            _env_w3023,
        )
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
    # CLAUDE.md REGRA 4 (anti-silent-fallback) canonical fields.
    # When success=False, these populate to expose the real error to
    # observability while the UX-facing `content` can remain friendly.
    error_code: str | None = None
    error_category: str | None = None
    request_id: str | None = None

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

        # WT-2022 P3.1 (2026-05-21): PolicyGateService default canonical = V2.
        # Antes: se policy_gate_service is None, Phase 0.5 ficava desligada.
        # Agora: instancia PolicyGateService(PolicyEngineService()) — V2 engine
        # é stateless (cache interno + AsyncSessionLocal por chamada), seguro
        # como singleton no orchestrator.
        if policy_gate_service is None:
            try:
                from app.orchestrator.services.policy_gate_service import (
                    PolicyGateService,
                )
                from app.domains.policy.services.policy_engine_service import (
                    PolicyEngineService,
                )
                policy_gate_service = PolicyGateService(
                    policy_engine=PolicyEngineService()
                )
                logger.info(
                    "[MainOrchestrator] PolicyGateService initialized with "
                    "V2 PolicyEngineService (P3.1 canonical)"
                )
            except Exception as _e:
                logger.warning(
                    "[MainOrchestrator] Failed to initialize default "
                    "PolicyGateService V2 (%s); policy gate disabled.",
                    _e,
                )
                policy_gate_service = None
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

            # WT-2022 P0.AIC1: defense-in-depth ai_credits_balance gate.
            # Chokepoint canonical é llm_factory.generate_with_fallback, mas wire-se
            # aqui tambem pra bail-out cedo (antes de tenant context + routing).
            # fail-safe ALLOW se DB/Redis em outage.
            if ctx.company_id is not None:
                try:
                    from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted
                    await check_credit_budget(db, str(ctx.company_id), estimated_tokens=2000)
                except AICreditExhausted as _aic_exc:
                    logger.warning(
                        "[MainOrchestrator] AI credit budget exhausted: company=%s",
                        ctx.company_id,
                    )
                    return ChatResponse(
                        success=False,
                        content=(
                            "Seu pacote de creditos IA do mes esgotou. "
                            "Entre em contato com seu admin para renovar ou aumentar o plano."
                        ),
                        agent_used="ai_credit_gate",
                        confidence=1.0,
                        intent_detected="blocked_credit_exhausted",
                        conversation_id=conv_id,
                    )
                except Exception as _aic_exc:
                    logger.debug("[MainOrchestrator] ai_credit_gate skipped (fail-safe): %s", _aic_exc)

            # ── P1-W4-11: PolicyGate soft-enforcement ─────────────────────
            # Soft gate: valida intent contra policies do tenant. Log violations,
            # nunca bloqueia fluxo (hard gate em sprint futuro quando policies
            # estiverem validadas em produção). Posicionado após credit gate,
            # antes de qualquer enrichment/LLM call.
            if self._policy_gate_service and ctx.company_id:
                try:
                    _policy_result = await self._policy_gate_service.validate(
                        intent=str(ctx.extra.get("intent_hint", "general") if ctx.extra else "general"),
                        user_id=str(ctx.user_id or ""),
                        context={"company_id": str(ctx.company_id)},
                    )
                    if not _policy_result.allowed:
                        logger.warning(
                            "[PolicyGate] P1-W4-11 soft-enforcement: intent=%s blocked "
                            "by policy reason=%s company=%s user=%s — "
                            "logging violation, not blocking (hard gate em sprint futuro)",
                            _policy_result.intent, _policy_result.reason,
                            ctx.company_id, ctx.user_id,
                        )
                        # TODO P1-W4-11: converter em hard block (return ChatResponse blocked)
                        # quando policies estiverem validadas em produção.
                except Exception as _pg_err:
                    logger.debug("[PolicyGate] P1-W4-11 evaluate error (non-blocking): %s", _pg_err)

            # Enriquecer contexto com informações do tenant
            # R4 (Task T-F): idempotente + paridade com agent_chat_sse.py.
            # Se um caller upstream (SSE/WS handler) já injetou o snippet,
            # NÃO sobrescrevemos. Em caso de falha do get_context, caímos
            # no build_authenticated_snippet para manter LIA ciente de que
            # o usuário está autenticado (mesma rede de proteção do SSE
            # handler, fechando 5ª causa raiz da auditoria T-F).
            _existing_snippet = getattr(ctx, "tenant_context_snippet", "") or ""
            if not (isinstance(_existing_snippet, str) and _existing_snippet.strip()):
                _company_id_str = str(ctx.company_id) if ctx.company_id else ""
                try:
                    _job_id = (
                        ctx.entity_id
                        if getattr(ctx, "entity_type", None) == "job"
                        else None
                    )
                    _tenant_ctx = await self._tenant_context_service.get_context(
                        company_id=_company_id_str, db=db, job_id=_job_id,
                    )
                    _snippet = _tenant_ctx.to_prompt_snippet()
                    if _company_id_str:
                        _snippet += "\n" + TenantContextService.build_authenticated_snippet(
                            _company_id_str
                        )
                    ctx.tenant_context_snippet = _snippet
                except Exception as _tc_exc:
                    logger.debug(
                        "[MainOrchestrator] TenantContext skipped: %s", _tc_exc,
                    )
                    if _company_id_str:
                        ctx.tenant_context_snippet = (
                            TenantContextService.build_authenticated_snippet(
                                _company_id_str
                            )
                        )

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
                from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability
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

            # ── Phase 0.6: Policy Gate (Sprint 12.5-B4) ─────────────────────
            # Validate against tenant policies BEFORE action dispatch.
            # Mirror of V1 legacy policy_gate.validate call (legacy/orchestrator.py:181).
            #
            # Pre-action gate with intent="general_chat" (SAFE_INTENTS fast-path):
            # - Per-user rate limits still applied
            # - Blocked-user check still applied
            # - Tenant-level guardrails (e.g. global "agent disabled") still applied
            #
            # Intent-specific gates (e.g. delete_candidate, publish_job) would
            # chain in action_executor with the resolved intent. Deferred to
            # Sprint 12.5-B4-extra.
            #
            # Fail-open canonical: PolicyGate itself fail-safe (returns
            # PolicyResult with allowed=True+engine_unavailable=True on engine
            # error). Wrap in try/except for defense-in-depth.
            if self._policy_gate_service is not None:
                try:
                    _policy_result = await self._policy_gate_service.validate(
                        intent="general_chat",
                        user_id=ctx.user_id or "anon",
                        context={
                            "company_id": str(ctx.company_id) if ctx.company_id else None,
                            "user_id": ctx.user_id,
                            "channel": ctx.channel,
                        },
                    )
                    if not _policy_result.allowed:
                        logger.warning(
                            "[MainOrchestrator] Phase 0.6 policy gate DENIED: "
                            "user=%s company=%s reason=%s",
                            ctx.user_id, ctx.company_id, _policy_result.reason,
                        )
                        return ChatResponse(
                            success=False,
                            content=(
                                _policy_result.reason
                                or "Acesso negado por política do tenant. "
                                   "Entre em contato com seu administrador."
                            ),
                            agent_used="policy_gate",
                            confidence=1.0,
                            intent_detected="blocked_policy",
                            conversation_id=conv_id,
                            error_code="POLICY_DENIED",
                            error_category="policy_gate",
                        )
                except Exception as _policy_exc:
                    logger.debug(
                        "[MainOrchestrator] Phase 0.6 policy gate skipped (fail-open): %s",
                        _policy_exc,
                    )

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

            # ── Phase 1.4: Wizard Canonical Executor (Task #1055) ──────────
            # Canonical REST/SSE delegation to WizardSessionService — espelha
            # agent_chat_ws.py:914 (WS canonical path). Sem este intercept, o
            # turno do wizard era engolido pela Phase 1.5 Agentic Loop e o
            # ``ws_stage_payload`` (que carrega ``pipeline_template`` para o
            # ``WizardPipelineTemplateCard``) jamais era emitido em REST.
            #
            # Disparo:
            #   • turnos ≥2 — handler-level wizard pin (Task #1080)
            #     identifica sessão LangGraph aberta (#1051/#1052 contract).
            #   • turno 1 — heurística de start patterns (``criar vaga``, etc.)
            #     espelhando ``JobCreationDomain.process_intent``. Bootstrap
            #     necessário porque o pin só fira após a 1ª invocação do
            #     ``WizardSessionService.process_message`` marcar a sessão.
            #
            # Fail-open: qualquer exceção cai para Phase 1.5 (legado).
            try:
                _wiz_resp = await self._try_wizard_canonical(
                    ctx, conv_id, conv, db,
                )
                if _wiz_resp is not None:
                    if _soft_warnings and not _wiz_resp.fairness_warnings:
                        _wiz_resp.fairness_warnings = _soft_warnings
                    return _wiz_resp
            except Exception as _wiz_exc:
                logger.warning(
                    "[MainOrchestrator] Wizard canonical executor crashed; "
                    "falling through to Phase 1.5: %s", _wiz_exc, exc_info=True,
                )

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
                    from app.orchestrator.execution.agentic_loop import agentic_loop

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
                        except Exception as _llm_cfg_exc:
                            logger.warning(
                                "[main_orchestrator] tenant LLM config lookup failed company_id=%s - degraded to claude default: %s",
                                _loop_company_id, _llm_cfg_exc, exc_info=True,
                            )
                            # Fail-open: use claude default

                    # Sprint 1.4 (G) — canonical: build system_prompt via SystemPromptBuilder
                    # so Phase 1.5 reads the same persona/anti-patterns/capabilities/
                    # context_page that Phase 2 (fallback_react, legacy) reads.
                    # Without this, the most common chat path bypasses persona Rule 4 +
                    # Anti-pattern #7 + G3/G6 capabilities + G1 page_context.
                    _phase15_system_prompt = ""
                    try:
                        from app.shared.prompts.system_prompt_builder import (
                            SystemPromptBuilder,
                        )
                        from app.shared.agents.tenant_aware_agent import (
                            resolve_tenant_snippet_for_non_react,
                        )
                        _phase15_octx = ctx.to_orchestrator_context()
                        _phase15_tenant_snippet = resolve_tenant_snippet_for_non_react(
                            _phase15_octx,
                            agent_name="phase15_agentic_loop",
                            company_id_raw=_loop_company_id,
                        )
                        _phase15_system_prompt = SystemPromptBuilder.build(
                            agent_type="orchestrator",
                            tenant_context_snippet=_phase15_tenant_snippet,
                            user_name=getattr(ctx, "user_name", "") or "",
                            user_role=getattr(ctx, "user_role", "") or "",
                            conversation_summary=ctx.extra.get(
                                "conversation_summary", ""
                            ) or "",
                            conversation_history=ctx.extra.get(
                                "conversation_history"
                            ),
                            context_page=getattr(ctx, "context_page", "general")
                            or "general",
                            entity_type=getattr(ctx, "entity_type", None),
                        )
                    except Exception as _sp_exc:
                        # Fail-loud in log; agentic loop continues with empty prompt
                        # (no worse than pre-Sprint-1.4 behaviour).
                        logger.error(
                            "[Sprint 1.4 G] Failed to build Phase 1.5 system_prompt — "
                            "falling back to empty (persona will NOT be applied): %s",
                            _sp_exc,
                            exc_info=True,
                        )

                    # Bug obs #1 fix (2026-05-24): PREPEND greeting/ambiguous rule
                    # ANTES do persona+tools list. LLM perde focus em prompts
                    # 50K+ tokens longos — colocar regra no topo + bottom
                    # (defense in depth).
                    _greeting_priority = (
                        "## REGRA #1 — Saudações e queries vagas (PRIORIDADE MÁXIMA)\n\n"
                        "Quando o usuário enviar APENAS uma saudação ou query "
                        "vaga (\"oi\", \"olá\", \"bom dia\", \"tudo bem?\", "
                        "\"alguma coisa\", \"tudo\", \"sim\" sem contexto, "
                        "\"e aí\", etc.), você DEVE responder com saudação "
                        "amigável + pergunta concreta sobre o que ajudar. "
                        "**NÃO chame ferramenta nenhuma.** Não chute "
                        "`search_jobs`, `search_candidates`, "
                        "`check_company_completeness` ou qualquer tool quando "
                        "não há contexto explícito.\n\n"
                        "Exemplo correto:\n"
                        "User: \"oi\"\n"
                        "Você: \"Olá! 👋 Como posso ajudar? Posso te mostrar "
                        "vagas em aberto, status de candidatos, ou indicadores "
                        "— o que você precisa?\"\n\n"
                        "Exemplo ERRADO (não faça):\n"
                        "User: \"oi\"\n"
                        "Você: [chama search_jobs(status=\"Ativa\")]\n\n"
                        "## REGRA #2 — Navegação (PRIORIDADE MÁXIMA)\n\n"
                        "Quando o usuário pedir explicitamente pra ir a uma "
                        "página (\"me leve\", \"abra\", \"vai pra\", "
                        "\"me leva pra\", \"abre o(a)\", \"vamos pra\"), "
                        "**EMITA `[NAVIGATE:<canonical_page>]`** ao final do "
                        "texto. **NÃO chame ferramenta** como "
                        "`check_company_completeness`, `list_jobs`, "
                        "`search_candidates`, etc. — a navegação é UI-only.\n\n"
                        "Páginas canônicas: home, vagas, vaga_detalhe, "
                        "recrutar, funil_talentos, candidato_detalhe, "
                        "pipeline_kanban, dashboard, configuracoes, "
                        "agent_studio, ajuda, bancos_talentos, biblioteca, "
                        "central_comunicacao, tasks, chat, trust.\n\n"
                        "Exemplo correto:\n"
                        "User: \"me leve para vagas\"\n"
                        "Você: \"Te levando para Vagas! 🚀 [NAVIGATE:vagas]\"\n\n"
                        "User: \"abre as configurações\"\n"
                        "Você: \"Abrindo Configurações. ⚙️ [NAVIGATE:configuracoes]\"\n\n"
                        "Exemplo ERRADO (não faça):\n"
                        "User: \"me leve para vagas\"\n"
                        "Você: [chama check_company_completeness()]\n\n"
                        "## REGRA #3 — Abrir/visualizar vaga ou candidato específico (PRIORIDADE MÁXIMA)\n\n"
                        "Quando o usuário pedir pra **abrir/visualizar/ver/"
                        "mostrar** uma vaga ou candidato ESPECÍFICO (com nome "
                        "ou ID), **NÃO chame `search_jobs` nem "
                        "`search_candidates`**. Em vez disso:\n"
                        "1. Se tiver job_id/candidate_id explícito → chame "
                        "`get_job_details(job_id=...)` ou "
                        "`get_candidate_details(candidate_id=...)` diretamente.\n"
                        "2. Se tiver só nome/título → pergunte o ID/confirme: "
                        "\"Achei N vagas com esse título — qual o ID ou data?\"\n\n"
                        "Exemplo correto:\n"
                        "User: \"abra a vaga design lead pleno\"\n"
                        "Você: \"Encontrei 1 vaga com esse título. "
                        "[NAVIGATE:vaga_detalhe?id=<uuid>]\" OU\n"
                        "\"Achei 3 vagas com 'design lead' no título. "
                        "Pode passar o ID ou data de criação?\"\n\n"
                        "Exemplo ERRADO (não faça):\n"
                        "User: \"abra a vaga design lead\"\n"
                        "Você: [chama search_jobs(status=\"Pausada\")] ← "
                        "user NUNCA mencionou status\n\n"
                        "## REGRA #4 — Não inventar argumentos\n\n"
                        "**NUNCA invente argumentos de tool** (status, "
                        "location, seniority, skills, etc.) que o usuário "
                        "não tenha mencionado explicitamente. Se faltar info, "
                        "PERGUNTE em vez de chutar valor default.\n\n"
                        "Exemplo correto:\n"
                        "User: \"buscar candidatos\"\n"
                        "Você: \"Buscar candidatos com qual perfil? "
                        "Pode me dar 1-2 filtros: skill, seniority, "
                        "location, ou ID da vaga?\"\n\n"
                        "Exemplo ERRADO (não faça):\n"
                        "User: \"buscar candidatos\"\n"
                        "Você: [chama search_candidates(location=\"São Paulo\","
                        " seniority=\"Sênior\", skills=[\"Python\"])] ← "
                        "user não mencionou nenhum desses\n\n"
                        "Essas regras têm prioridade sobre QUALQUER outra "
                        "sugestão de tool no system prompt abaixo.\n\n"
                        "---\n\n"
                    )
                    _phase15_system_prompt = _greeting_priority + _phase15_system_prompt

                    # Sprint 12.5-TF (2026-05-24): clarification instruction.
                    # Encourage LIA to ASK when query is ambiguous instead of
                    # guessing tools or returning generic responses. Reduces
                    # tool failures (e.g. search_candidates without filters)
                    # and improves UX (recruiter gets actionable response).
                    _phase15_system_prompt += (
                        "\n\n### Clarificação canonical\n"
                        "Se a query do usuário for ambígua (múltiplas interpretações "
                        "válidas) ou você não souber qual ferramenta usar, **PERGUNTE "
                        "de volta** ao usuário ao invés de chutar uma ferramenta ou "
                        "tentar inferir parâmetros. A pergunta deve ser direta, curta, "
                        "com 2-3 opções concretas quando aplicável.\n\n"
                        "Exemplos:\n"
                        "- User: \"me ajuda com candidato João\" → Você: \"João Silva "
                        "(Dev) ou João Souza (UX)? Pode confirmar qual?\"\n"
                        "- User: \"como tá indo?\" → Você: \"Quer um resumo de vagas, "
                        "candidatos ou indicadores?\"\n"
                        "- User: \"fecha\" → Você: \"Fechar qual vaga? Pode me dizer "
                        "o título ou ID?\"\n"
                        "- User: \"tudo\" → Você: \"Sobre o que especificamente? "
                        "Vagas, candidatos, indicadores?\"\n\n"
                        "NÃO chute uma ferramenta quando a query for vaga. NÃO peça "
                        "ao usuário pra repetir — proponha 2-3 alternativas concretas."
                    )

                    # Sprint 12.3-C conservative (2026-05-24): STRUCTURED_INTENT_ADDENDA.
                    # Contexto-específico guidance pra Phase 1.5 resolver mais
                    # casos antes de fall-through V1. Reduz canary metric
                    # phase_2_v1_invocations_total (Sprint 12.3-A).
                    # V1 permanece como fallback secundário (kill-switch ativo).
                    _ctx_page = (getattr(ctx, "context_page", "") or "").lower()
                    _ctx_entity = (getattr(ctx, "entity_type", "") or "").lower()
                    _addenda_lines = []
                    if _ctx_entity in ("candidate", "candidato") or _ctx_page == "candidato_detalhe":
                        _addenda_lines.append(
                            "- Há um candidato em contexto. Para análise de match "
                            "com vaga, use `analyze_cv_match`. Para detalhes do "
                            "perfil, use `get_candidate_details`."
                        )
                    if _ctx_entity in ("job", "job_vacancy") or _ctx_page == "vaga_detalhe":
                        _addenda_lines.append(
                            "- Há uma vaga em contexto. Para detalhes, use "
                            "`get_job_details`. Para listar candidatos no pipeline, "
                            "use `get_pipeline_summary` ou `search_candidates` "
                            "com `in_vacancy_id`."
                        )
                    if _ctx_page == "funil_talentos":
                        _addenda_lines.append(
                            "- User está no Funil de Talentos. Para buscar "
                            "candidatos, use `search_candidates` com filtros "
                            "(skills, seniority, location). Para mover candidato "
                            "entre etapas, use `update_candidate_stage`."
                        )
                    if _ctx_page == "configuracoes":
                        _addenda_lines.append(
                            "- User está em Configurações. Para mudanças de perfil "
                            "da empresa, use tools de company_settings. Para "
                            "configurar políticas, use save_hiring_policy."
                        )
                    if _ctx_page == "vagas":
                        _addenda_lines.append(
                            "- User está em Vagas. Para listar/filtrar, use "
                            "`list_jobs`. Para criar nova, sinalize "
                            "`[NAVIGATE:recrutar]` (wizard) ou `create_job` direto."
                        )
                    if _addenda_lines:
                        _phase15_system_prompt += (
                            "\n\n### Tools sugeridas para este contexto\n"
                            + "\n".join(_addenda_lines)
                            + "\n\n"
                            "Use essas tools como **primeira opção**. Se a query "
                            "não casar com nenhuma, prossiga normalmente ou "
                            "pergunte clarificação (regra anterior)."
                        )

                    _agentic_result = await agentic_loop.run(
                        user_message=ctx.message,
                        system_prompt=_phase15_system_prompt,
                        conversation_history=ctx.extra.get("conversation_history", []),
                        company_id=_loop_company_id,
                        user_id=getattr(ctx, "user_id", None),
                        session_id=conv_id,
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
                        # Sprint 14.4: enrich suggested_prompts when empty + page known
                        _enrich_suggested_prompts(_resp, ctx)
                        return _resp
                except Exception as exc:
                    logger.debug("[LIA-A04] Agentic loop skipped: %s", exc)

            # ── Phase 2: Orchestrator completo (V1 fallback) ────────────────
            # Sprint 12.3-A (2026-05-24): kill-switch + canary observability.
            # Default behavior preserved (enabled=True when env unset).
            # See: PHASE_2_V1_ARCHITECTURE_AUDIT.md, canary_metrics.phase_2_v1_invocations_total.
            _phase2_enabled = _is_phase_2_v1_enabled()
            try:
                import hashlib as _hashlib
                from app.shared.observability.canary_metrics import phase_2_v1_invocations_total
                if phase_2_v1_invocations_total is not None:
                    _cid_hash = _hashlib.sha256(
                        (str(ctx.company_id) if ctx.company_id else "anon").encode()
                    ).hexdigest()[:12]
                    phase_2_v1_invocations_total.labels(
                        company_id_hash=_cid_hash,
                        flag_state="enabled" if _phase2_enabled else "disabled",
                    ).inc()
            except Exception as _canary_exc:
                logger.debug("[MainOrchestrator] Phase 2 V1 canary increment failed: %s", _canary_exc)

            # Sprint 15.3-B (2026-05-24): Loop A producer wire.
            # Phase 2 V1 hit = routing was suboptimal (Phase 1.5 didn't resolve).
            # Record correction signal so daily aggregator (MonitoringLoop)
            # computes per-domain adjustment factors for CascadedRouter.
            # Pragmatic proxy (Sprint 15.1 SIGNALS_INVENTORY.md Opt 1) — when
            # 12.3-C absorption removes V1, migrate to a different signal source.
            if _phase2_enabled and ctx.company_id:
                try:
                    from app.shared.services.routing_learning_service import (
                        routing_learning_service,
                    )
                    from lia_config.database import AsyncSessionLocal
                    _routed_proxy = getattr(ctx, "context_page", "general") or "general"
                    async with AsyncSessionLocal() as _signal_db:
                        await routing_learning_service.record_correction(
                            session_id=conv_id or "no-conv",
                            routed_domain=_routed_proxy,
                            actual_domain="fallback_v1",
                            company_id=str(ctx.company_id),
                            db=_signal_db,
                            message=ctx.message or "",
                        )
                except Exception as _learn_exc:
                    # Fail-open: signal capture exception não bloqueia request
                    logger.debug(
                        "[MainOrchestrator] Loop A producer skipped: %s",
                        _learn_exc,
                    )

            if not _phase2_enabled:
                # Sprint 12 cutover kill-switch active: return canonical fail-loud
                # response (Sprint 9 timeout pattern). LIA_PHASE_2_V1_ENABLED=false
                # gates the legacy Orchestrator.process_request — refactor pending.
                logger.warning(
                    "[MainOrchestrator] Phase 2 V1 fallback DISABLED via LIA_PHASE_2_V1_ENABLED — "
                    "returning canonical fail-loud (user=%s company=%s).",
                    ctx.user_id, ctx.company_id,
                )
                _phase2_response = ChatResponse(
                    success=False,
                    content=(
                        "Estou processando sua solicitação. "
                        "Pode tentar novamente em alguns segundos? "
                        "Se persistir, reformule a pergunta com mais detalhes."
                    ),
                    agent_used="phase_2_v1_disabled",
                    confidence=0.0,
                    intent_detected="fallback_disabled",
                    conversation_id=conv_id,
                    error_code="PHASE_2_V1_DISABLED",
                    error_category="kill_switch",
                )
            else:
                _phase2_response = await self._process_via_orchestrator(
                    ctx, conv_id, db, streaming_callback, conv=conv
                )
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
            # Sprint 14.4: enrich suggested_prompts when empty + page known
            _enrich_suggested_prompts(_phase2_response, ctx)
            return _phase2_response

        except Exception as exc:
            # CLAUDE.md REGRA 4 — anti-silent-fallback canonical handling:
            # the friendly content remains for UX, but error_code +
            # error_category + request_id propagate the real failure to
            # the response envelope AND the structured log.
            import uuid as _uuid
            _req_id = str(_uuid.uuid4())
            _exc_type = type(exc).__name__
            _exc_msg = str(exc)[:300]
            # Classify the error into stable buckets so observability /
            # alerts can route. Order matters — first match wins.
            _category = "unknown"
            _code = _exc_type
            if "process_request" in _exc_msg and "no attribute" in _exc_msg:
                _category = "orchestrator_interface"
                _code = "orchestrator_attribute_missing"
            elif "_enforce_credit_gate_sync" in _exc_msg:
                _category = "llm_provider"
                _code = "credit_gate_async_violation"
            elif "row-level security" in _exc_msg.lower() or "insufficientprivilege" in _exc_msg.lower():
                _category = "tenant_context"
                _code = "rls_violation"
            elif "could not refresh instance" in _exc_msg.lower():
                _category = "tenant_context"
                _code = "rls_select_blocked_post_commit"
            elif _exc_type == "RecursionError":
                _category = "orchestrator_interface"
                _code = "factory_infinite_recursion"
            elif _exc_type == "TimeoutError" or "timed out" in _exc_msg.lower():
                _category = "llm_provider"
                _code = "llm_timeout"
            elif _exc_type == "AICreditExhausted":
                _category = "credit_gate"
                _code = "credit_exhausted"

            logger.error(
                "[MainOrchestrator] Unhandled error request_id=%s "
                "user=%s company=%s channel=%s category=%s code=%s "
                "exc_type=%s exc=%s",
                _req_id, ctx.user_id, ctx.company_id, ctx.channel,
                _category, _code, _exc_type, _exc_msg,
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
                error_code=_code,
                error_category=_category,
                request_id=_req_id,
            )

    # ------------------------------------------------------------------
    # Phase 0 — PendingAction
    # ------------------------------------------------------------------

    @trace_span("orchestrator.phase_0_pending_action", attributes={"phase": "0"})
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
                        # Sprint 1.1 (B) — thread conversation history so the humanizer
                        # can interpret short replies ("sim", "ok") in context.
                        # Closes N4 root cause; persona Anti-pattern #7 is defense.
                        _phase0_ctx = {
                            "user_name": getattr(ctx, "user_name", "") or "",
                            "user_role": getattr(ctx, "user_role", "") or "",
                            "conversation_history": ctx.extra.get("conversation_history", []),
                            "conversation_summary": ctx.extra.get("conversation_summary"),
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
                                    # Sprint 1.1 (B) — same fix as Phase 0 confirmation.
                                    _phase0_ctx = {
                                        "user_name": getattr(ctx, "user_name", "") or "",
                                        "user_role": getattr(ctx, "user_role", "") or "",
                                        "conversation_history": ctx.extra.get("conversation_history", []),
                                        "conversation_summary": ctx.extra.get("conversation_summary"),
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

    @trace_span("orchestrator.phase_1_action_executor", attributes={"phase": "1"})
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
            # Sprint 1.2 (F) — canonical producer fix.
            # The executor returns needs_params/needs_confirmation but does NOT
            # persist to pending_action_store. Without this save, Phase 0 misses
            # the next user reply ("sim"/"não"/param) → duplicate confirmation
            # (N5) or "mensagem incompleta" (N4 collateral).
            try:
                from app.orchestrator.action_executor.intents_config import (
                    ACTIONABLE_INTENTS,
                )
                from app.orchestrator.execution.pending_action import (
                    PendingActionState,
                )
                _data = action_result.data or {}
                _intent = _data.get("intent") or action_result.action_type or ""
                _config = ACTIONABLE_INTENTS.get(_intent, {})
                _missing = list(getattr(action_result, "missing_params", None) or [])
                _summary = getattr(action_result, "confirmation_summary", None)
                _pending = PendingActionState(
                    pending_id=action_result.pending_action_id
                    or "pending-" + (_intent or "unknown"),
                    intent=_intent,
                    action_id=_config.get("action_id", _intent or "unknown"),
                    domain_id=_config.get("domain_id", "unknown"),
                    collected_params=dict(_data.get("collected_params") or {}),
                    missing_params=_missing,
                    conversation_id=conv_id,
                    company_id=getattr(ctx, "company_id", None),
                    awaiting_confirmation=(
                        action_result.status == "needs_confirmation"
                    ),
                    confirmation_summary=_summary,
                )
                pending_action_store.save(conv_id, _pending)
            except Exception as _persist_exc:
                # Fail-loud in logs but keep the response flowing. If we fail to
                # persist, the user will hit the dup-confirmation path on the next
                # turn — same behaviour as before this fix, never worse.
                logger.error(
                    "[F] failed to persist pending_action: %s",
                    _persist_exc,
                    exc_info=True,
                )
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
                # Sprint 1.1 (B): include conversation_history so the humanizer can
                # interpret short user replies in context — closes N4 at the producer.
                _phase1_context = {
                    "user_name": getattr(ctx, "user_name", "") or "",
                    "user_role": getattr(ctx, "user_role", "") or "",
                    "tenant_id": getattr(ctx, "company_id", "") or "",
                    "conversation_history": ctx.extra.get("conversation_history", []),
                    "conversation_summary": ctx.extra.get("conversation_summary"),
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

            # Sprint 1.1 (B) — inject conversation history + summary BEFORE the action
            # block so the LLM can disambiguate short replies ("sim", "ok", "vamos").
            # Without this, the LLM defaults to its pretrained "incomplete message"
            # shape (N4 root cause). Persona Anti-pattern #7 is the secondary defense.
            interpretation_prompt = (
                "Voce e a LIA, assistente inteligente da WeDOTalent.\n"
                f"{greeting} pediu: {ctx.message}\n\n"
            )

            _hist_summary = orchestrator_context.get("conversation_summary")
            if _hist_summary:
                interpretation_prompt += (
                    f"### Resumo da conversa anterior\n{_hist_summary}\n\n"
                )

            _hist = orchestrator_context.get("conversation_history") or []
            if _hist:
                # Last 6 turns is enough for context disambiguation; full history
                # would bloat the prompt for the lightweight Phase 0/1 humanizer.
                _recent = _hist[-6:]
                _lines = []
                for _m in _recent:
                    _role = _m.get("role", "?") if isinstance(_m, dict) else "?"
                    _content = str(_m.get("content", "")) if isinstance(_m, dict) else ""
                    _lines.append(f"- {_role}: {_content[:300]}")
                interpretation_prompt += (
                    "### Historico recente\n" + "\n".join(_lines) + "\n\n"
                )

            interpretation_prompt += (
                f"A acao '{action_result.action_type}' foi executada com sucesso.\n"
                f"Resultado: {action_result.message}\n"
            )

            if action_result.data:
                import json
                try:
                    data_str = json.dumps(action_result.data, ensure_ascii=False, default=str)[:2000]
                    interpretation_prompt += f"Dados retornados: {data_str}\n"
                except Exception:
                    # T-04 Tipo D: data serialization is decorative
                    # (enriches LLM prompt with structured context); if it
                    # fails (non-serializable type), the prompt still has
                    # the human-readable action_result.message above.
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

    # Phase 1.4 — Wizard Canonical Executor (Task #1055)
    # ------------------------------------------------------------------

    # Start patterns para bootstrap do TURNO 1 (sessão wizard ainda não
    # marcada). Espelha ``JobCreationDomain.process_intent`` (linha 253) —
    # mesma fonte de verdade canônica. Mantido como tuple module-level
    # para reutilização pela sentinela offline.
    _WIZARD_START_PATTERNS: tuple[str, ...] = (
        "criar vaga", "nova vaga", "abrir vaga", "contratar",
        "preciso de", "quero criar", "vamos criar", "criar uma vaga",
        "abrir uma vaga", "nova posição", "nova posicao",
    )

    async def _try_wizard_canonical(
        self,
        ctx: UniversalContext,
        conv_id: str,
        conv: Any,
        db: Any,
    ) -> ChatResponse | None:
        """Canonical wizard executor para REST/SSE — espelha agent_chat_ws.py:914.

        Decisão de disparo:
          1. **Continuação (turno ≥2):** consulta ``WizardSessionService.is_session_active``
             (wrapper delegante para ``app.shared.sessions.is_wizard_session_active``,
             mesmo predicado usado pelo wizard pin dos handlers WS/SSE — Task #1080).
             Se há sessão LangGraph aberta, delega.
          2. **Bootstrap (turno 1):** se a mensagem casa com ``_WIZARD_START_PATTERNS``
             (mesma fonte canônica de ``JobCreationDomain.process_intent``),
             delega — isso marca a sessão para o pin assumir nos turnos seguintes.

        Retorna ``None`` se não for wizard (caller cai para Phase 1.5).

        Empacota ``ws_stage_payload`` em ``structured_data["ws_stage_payload"]``
        — ``ChatAdapter._convert_response`` mapeia para ``workflow_data`` →
        ``chat.py`` propaga para ``message_metadata.ws_stage_payload`` → FE
        ``sendViaRest`` dispara ``lia:wizard-stage-payload`` (espelha
        ``useChatSocket.ts:272`` do caminho WS).
        """
        from app.domains.job_creation.services.wizard_session_service import (
            WizardSessionService,
        )

        message_text = (ctx.message or "").strip()
        if not message_text:
            return None

        company_id = str(ctx.company_id) if ctx.company_id else None
        session_id = conv_id or str(uuid.uuid4())

        # ── Decisão de disparo ──
        is_wizard_turn = False
        try:
            is_wizard_turn = await WizardSessionService.is_session_active(
                session_id=session_id, company_id=company_id,
            )
        except Exception as _pin_exc:
            logger.debug(
                "[MainOrchestrator] is_session_active skipped: %s", _pin_exc,
            )

        if not is_wizard_turn:
            _msg_lower = message_text.lower()
            if any(p in _msg_lower for p in self._WIZARD_START_PATTERNS):
                is_wizard_turn = True
                logger.info(
                    "[MainOrchestrator] Wizard bootstrap (turno 1): pattern match "
                    "session=%s company=%s", session_id, company_id,
                )

        if not is_wizard_turn:
            return None

        # ── Delegação canônica para WizardSessionService ──
        # Task #1080: thread_id derivado pelo helper canônico puro
        # (app.shared.sessions.derive_thread_id), única fonte de verdade
        # cross-transport (WS / SSE / REST orchestrator).
        from app.shared.sessions import derive_thread_id
        thread_id = derive_thread_id(company_id, session_id)

        # context dict espelha o que agent_chat_ws.py monta — mantém paridade
        # com o caminho WS para que ``_build_state`` funcione idêntico.
        wiz_context: dict[str, Any] = dict(ctx.extra or {})
        wiz_context.setdefault("user_id", ctx.user_id)
        wiz_context.setdefault("company_id", company_id)
        wiz_context.setdefault("session_id", session_id)
        if getattr(ctx, "tenant_context_snippet", ""):
            wiz_context.setdefault(
                "tenant_context_snippet", ctx.tenant_context_snippet
            )

        recruiter_msg, ws_stage_payload, _tokens = await WizardSessionService.process_message(
            thread_id=thread_id,
            user_message=message_text,
            user_id=ctx.user_id,
            company_id=company_id,
            session_id=session_id,
            context=wiz_context,
            on_token=None,  # REST não faz streaming token-by-token
        )

        recruiter_msg = recruiter_msg or "Vaga em criação — vamos seguir."

        # Persist response to conversation memory (espelha Phase 0/1)
        if conv and not ctx.skip_memory_persist:
            try:
                await self._persist_response(
                    ctx, conv_id, conv, {"response": recruiter_msg}, db,
                )
            except Exception as _exc:
                logger.warning(
                    "[MainOrchestrator] wizard canonical _persist_response "
                    "failed (non-blocking) conv_id=%s: %s",
                    conv_id, _exc,
                )

        _structured: dict[str, Any] = {}
        if ws_stage_payload:
            # Empacota com type=wizard_stage para o FE replicar 1:1 o evento WS
            # (useChatSocket.ts:272). thread_id é injetado para o WizardProvider
            # persistir o checkpointer LangGraph entre refreshes.
            _structured["ws_stage_payload"] = {
                "type": "wizard_stage",
                "thread_id": thread_id,
                "stage": ws_stage_payload.get("stage", "wizard"),
                **ws_stage_payload,
            }

        logger.info(
            "[MainOrchestrator] Wizard canonical executor: session=%s thread=%s "
            "stage=%s payload=%s",
            session_id, thread_id,
            (ws_stage_payload or {}).get("stage", "?"),
            "yes" if ws_stage_payload else "no",
        )

        return ChatResponse(
            success=True,
            content=recruiter_msg,
            agent_used="wizard_session_canonical",
            confidence=0.95,
            intent_detected="wizard",
            conversation_id=conv_id,
            structured_data=_structured or None,
        )

    # ------------------------------------------------------------------
    # Phase 2 — Pipeline consolidado (sem delegação intermediária)
    # ------------------------------------------------------------------

    @trace_span("orchestrator.phase_2_v1_fallback", attributes={"phase": "2", "canary": "phase_2_hit"})
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
                # G4 canonical fix (2026-05-24): same dual-population as
                # _setup_conversation_memory. ctx.extra is read by
                # Phase 1.5 agentic_loop.
                _history = llm_ctx.get("messages", [])
                _summary = llm_ctx.get("summary")
                orchestrator_context.update({
                    "conversation_history": _history,
                    "conversation_summary": _summary,
                    "context_type": ctx.context_type,
                    "context_id": ctx.entity_id,
                })
                ctx.extra["conversation_history"] = _history
                ctx.extra["conversation_summary"] = _summary
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
            from app.orchestrator.routing.fast_router import FastRouter
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
                        db=db,
                        user_id=ctx.user_id,
                        company_id=str(ctx.company_id) if ctx.company_id else "",
                        context_type=ctx.context_type,
                        context_id=ctx.entity_id,
                    )
                    conv_id = str(conv.id)
            else:
                conv = await conversation_memory.get_or_create_conversation(
                    db=db,
                    user_id=ctx.user_id,
                    company_id=str(ctx.company_id) if ctx.company_id else "",
                    context_type=ctx.context_type,
                    context_id=ctx.entity_id,
                )
                conv_id = str(conv.id)

            await conversation_memory.add_message(db=db, conversation_id=conv_id, role="user", content=ctx.message)
            llm_ctx = await conversation_memory.get_context_for_llm(db=db, conversation_id=conv_id, max_messages=20)
            # G4 canonical fix (2026-05-24): single source for history.
            # Populate BOTH orchestrator_context (legacy Phase 2 path) AND
            # ctx.extra (Phase 1.5 agentic_loop path) — same data, two
            # consumers. Without ctx.extra population, agentic_loop got an
            # empty history list and the LLM treated every turn as a fresh
            # session ("sua mensagem ficou incompleta — recebi apenas 'sim'").
            _history = llm_ctx.get("messages", [])
            _summary = llm_ctx.get("summary")
            orchestrator_context.update({
                "conversation_history": _history,
                "conversation_summary": _summary,
                "context_type": ctx.context_type,
                "context_id": ctx.entity_id,
            })
            ctx.extra["conversation_history"] = _history
            ctx.extra["conversation_summary"] = _summary
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
            from app.orchestrator.legacy.tasting_engine import tasting_engine, format_tasting_block

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
    """Singleton factory.

    Bug B canonical fix (2026-05-24): fallback path now reads the legacy
    Orchestrator instance DIRECTLY from the registry, not via the
    get_orchestrator() route helper. The route helper returns MainOrchestrator
    (already a wrapper), which would cause MainOrchestrator(MainOrchestrator(legacy))
    double-wrap and AttributeError 'process_request' under load. If legacy
    is not registered, fail loud — do not silently degrade.
    """
    global _main_orchestrator_instance
    if _main_orchestrator_instance is None:
        if orchestrator is None:
            from app.orchestrator.execution.registry import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if orchestrator is None:
                raise RuntimeError(
                    "Legacy Orchestrator not registered. Did "
                    "initialize_orchestrator() run during lifespan startup? "
                    "Check app/main.py and app/api/orchestrator_routes.py:initialize_orchestrator."
                )
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


# ---------------------------------------------------------------------------
# Sprint 14.4 (2026-05-24) — page-aware suggested_prompts enrichment
# ---------------------------------------------------------------------------

def _enrich_suggested_prompts(response: "ChatResponse", ctx: Any) -> None:
    """Populate ChatResponse.suggested_prompts based on ctx.context_page.

    Sprint 14.4 — quando o orchestrator/agentic loop não retorna prompts
    explícitos, derivamos do canonical_pages.suggested_prompts_for_page
    para que o usuário sempre veja 3 sugestões relevantes à página atual.

    Non-destructive: só popula quando `response.suggested_prompts` está
    vazio. Endpoints como orchestrated_jobs_management que setam manual
    continuam ganhando.

    Args:
        response: ChatResponse a ser enriquecida (mutação in-place).
        ctx: UniversalContext com context_page string ("vagas",
            "configuracoes", etc.) ou None.
    """
    try:
        if response.suggested_prompts:
            return  # respeita sugestões já presentes
        _page = getattr(ctx, "context_page", None)
        if not _page or _page == "general":
            return
        from app.shared.canonical_pages import suggested_prompts_for_page
        _suggestions = suggested_prompts_for_page(_page, limit=3)
        if _suggestions:
            response.suggested_prompts = _suggestions
    except Exception as _enrich_exc:
        # fail-open: enrichment é melhoria opcional, nunca quebra response
        logger.debug(
            "[MainOrchestrator] suggested_prompts enrichment skipped: %s",
            _enrich_exc,
        )


# ---------------------------------------------------------------------------
# Sprint 12.3-A — _is_phase_2_v1_enabled — kill-switch for Phase 2 V1 fallback
# ---------------------------------------------------------------------------

def _is_phase_2_v1_enabled() -> bool:
    """Sprint 12.3-A (2026-05-24): Phase 2 V1 fallback kill-switch.

    Reads ``LIA_PHASE_2_V1_ENABLED`` env var. Default-ON (backward compat):
    when env is unset, empty, or any non-falsy value, returns True so
    existing behavior is preserved until Sprint 12.6 cutover.

    Falsy values that DISABLE Phase 2 V1: ``{"0", "false", "no", "off"}``.

    When disabled, MainOrchestrator returns a canonical fail-loud response
    (REGRA 4 anti-silent-fallback) instead of invoking legacy
    Orchestrator.process_request. Canary counter
    ``phase_2_v1_invocations_total`` labels ``flag_state=disabled``
    on every gated call so we can correlate UX impact in Grafana.

    Returns:
        True (default) when env unset OR set to anything not in the falsy
        set. False ONLY when explicitly disabled via the falsy values.
    """
    import os

    val = os.getenv("LIA_PHASE_2_V1_ENABLED", "").lower().strip()
    return val not in {"0", "false", "no", "off"}
