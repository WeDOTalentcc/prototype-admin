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

from pydantic import BaseModel, Field, field_validator

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

    @field_validator("intent_detected", mode="before")
    @classmethod
    def _coerce_intent_detected(cls, v: object) -> str:
        # OrchestratorIntentResult é str-like (__str__ -> intent_id) mas a
        # validação string_type do Pydantic rejeita o objeto. Coage pra string.
        # Fix canonical 2026-06-03: single point, protege todos os call sites
        # (ex.: from_action_result com intent=pending.intent objeto).
        return str(v) if v is not None else "general"
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
    response_blocks: list[dict[str, Any]] | None = None
    # HITL bird (AUD-4 §4.2): hitl_pending do sub-agente ReAct do supervisor
    # (via rrp/hitl sink -> dr.metadata). O drain SSE minta + emite approval_required.
    hitl_pending: dict[str, Any] | None = None
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
            response_blocks=(result.get("response_blocks") or _structured.get("response_blocks")),
            hitl_pending=result.get("hitl_pending"),
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
            response_blocks=((action_result.data or {}).get("response_blocks")),
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

# -- Phase 1 -> Agentic fall-through (2026-06-04, harness GUIDE computacional) --
# Acoes onde, se o Phase 1 ActionExecutor nao tem o param obrigatorio, e melhor
# DEFERIR ao agentic loop (Phase 1.5) -- o LLM extrai o criterio do NL e chama a
# tool -- em vez de devolver needs_params e PERGUNTAR. Restrito a allowlist para
# nao afetar acoes que legitimamente exigem param (ex: agendar entrevista).
PREFER_AGENTIC_ON_MISSING_PARAMS: frozenset = frozenset({"search_candidates"})


# Fase 2 (2026-06-09): ui_actions emitidas por tool que o FE consome direto
# (useUIAction). Constante nomeada = sensor testavel. apply_table_state = ponte
# in-page (filtra/ordena a tabela aberta). open_modal/navigate_to = open_ui.
# P-SSOT: import from single canonical source -- do not redefine here.
# ALL_ACTIONABLE_UI_ACTION_TYPES includes the 3 page-specific strings
# (suggest_pipeline_template, move_candidate, switch_search_mode) that previously
# passed gate1 but were silently dropped here. They reach FE via ChatResponse.ui_action
# and are dispatched via lia:unhandled_ui_action to page-specific handlers.
from app.shared.ui_action_canonical import ALL_ACTIONABLE_UI_ACTION_TYPES as _FE_TOOL_UI_ACTIONS  # noqa: E501


def _defer_needs_params_to_agentic(action_response) -> bool:
    """True quando o Phase 1 retornou needs_params para uma acao 'prefer-agentic'
    -> deve cair pro agentic loop em vez de perguntar o param. Canonical-fix:
    ponto unico de decisao, puro e testavel."""
    return bool(getattr(action_response, "needs_params", False)) and (
        getattr(action_response, "action_type", None)
        in PREFER_AGENTIC_ON_MISSING_PARAMS
    )



# Frases que indicam criar vaga A PARTIR DE uma fonte (template/vaga existente).
# Conservador de proposito: so DEFERE o bootstrap do wizard vazio quando ha
# sinal CLARO de "a partir de fonte" — caso contrario, "criar vaga"/"nova vaga"
# segue bootstrapando exatamente como hoje (sem regressao). GUIDE feedforward
# computacional (CLAUDE.md harness): impede o wizard vazio de engolir o turno
# em que o recruiter_copilot deveria identificar a fonte (Phase 1.5).
_CREATE_FROM_SOURCE_PATTERNS: tuple[str, ...] = (
    "a partir de",
    "a partir da",
    "usar modelo",
    "usar um modelo",
    "usar template",
    "usar um template",
    "usando modelo",
    "usando um modelo",
    "usando template",
    "usando um template",
    "usar arquetipo",
    "usar um arquetipo",
    "usando arquetipo",
    "usando um arquetipo",
    "usar arquétipo",
    "usar um arquétipo",
    "usando arquétipo",
    "usando um arquétipo",
    "arquetipo",
    "arquétipo",
    "vaga existente",
    "vaga ja existente",
    "vaga já existente",
    "baseada na vaga",
    "baseada no modelo",
    "baseada no template",
    "baseado na vaga",
    "baseado no modelo",
    "igual a vaga",
    "igual à vaga",
    "como a vaga",
    "clonar vaga",
    "clonar a vaga",
    "duplicar vaga",
    "duplicar a vaga",
)


def _is_create_from_source(message: str) -> bool:
    """True quando a mensagem pede criar vaga A PARTIR DE uma fonte existente.

    GUIDE (feedforward, computacional). Quando True, ``_try_wizard_canonical``
    NAO bootstrapa o wizard vazio no turno 1 — deixa cair para a Phase 1.5
    (agentic loop), onde o ``recruiter_copilot`` chama ``list_job_creation_sources``
    + ``start_creation_from_source`` para identificar a fonte. Quando False,
    "criar vaga"/"nova vaga" seguem bootstrapando como hoje (sem regressao).

    Conservador: exige um padrao CLARO de "a partir de fonte"; nao basta a
    intencao de criar.
    """
    if not message:
        return False
    _m = message.lower()
    return any(p in _m for p in _CREATE_FROM_SOURCE_PATTERNS)


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
                # CR-5 Sprint 2.2 observability
                try:
                    from app.shared.observability.canary_metrics import main_orchestrator_guard_fires_total
                    if main_orchestrator_guard_fires_total is not None:
                        main_orchestrator_guard_fires_total.labels(
                            guard="security_patterns_input", outcome="block",
                        ).inc()
                except Exception:
                    pass
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
                # CR-5 Sprint 2.2 observability
                try:
                    from app.shared.observability.canary_metrics import main_orchestrator_guard_fires_total
                    if main_orchestrator_guard_fires_total is not None:
                        main_orchestrator_guard_fires_total.labels(
                            guard="fairness_input", outcome="block",
                        ).inc()
                except Exception:
                    pass
                # GAP-00-001: log_check() para audit trail do bloqueio
                try:
                    import asyncio as _fg_asyncio_orch
                    _fg_asyncio_orch.get_event_loop().create_task(
                        self._fairness_guard.log_check(
                            result=_fairness_result,
                            context="main_orchestrator",
                            company_id=str(ctx.company_id) if ctx.company_id else None,
                            recruiter_id=str(ctx.user_id) if ctx.user_id else None,
                        )
                    )
                except Exception:
                    pass
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
                    # CR-5 Sprint 2.2 observability
                    try:
                        from app.shared.observability.canary_metrics import main_orchestrator_guard_fires_total
                        if main_orchestrator_guard_fires_total is not None:
                            main_orchestrator_guard_fires_total.labels(
                                guard="fairness_implicit", outcome="soft_warn",
                            ).inc()
                    except Exception:
                        pass
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
                    # CR-5 Sprint 2.2 observability (complementa ai_credit_exhausted_total
                    # com label unificado de guard origin).
                    try:
                        from app.shared.observability.canary_metrics import main_orchestrator_guard_fires_total
                        if main_orchestrator_guard_fires_total is not None:
                            main_orchestrator_guard_fires_total.labels(
                                guard="ai_credit_gate", outcome="block",
                            ).inc()
                    except Exception:
                        pass
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

            # GAP-00-001: daily token budget check (defense-in-depth) ─────
            # agent_chat_sse.py checks before calling orchestrator;
            # this catches any other caller that skips the entry-point check.
            try:
                from app.domains.credits.services.token_budget_service import (
                    check_budget as _chk_bgt_orch,
                    get_plan_for_company as _get_plan_orch,
                )
                _bgt_plan_orch = await _get_plan_orch(str(ctx.company_id))
                _bgt_ok_orch, _bgt_used_orch, _bgt_lim_orch = await _chk_bgt_orch(
                    str(ctx.company_id), _bgt_plan_orch
                )
                if not _bgt_ok_orch:
                    logger.warning(
                        "[MainOrchestrator] Daily token budget exhausted: company=%s used=%d limit=%d",
                        ctx.company_id, _bgt_used_orch, _bgt_lim_orch,
                    )
                    return ChatResponse(
                        success=False,
                        content=(
                            f"Limite diario de uso de IA atingido "
                            f"({_bgt_used_orch:,}/{_bgt_lim_orch:,} tokens). "
                            "O budget sera renovado a meia-noite UTC."
                        ),
                        agent_used="token_budget_gate",
                        confidence=1.0,
                        intent_detected="blocked_budget_exhausted",
                        conversation_id=conv_id,
                    )
            except Exception as _bgt_orch_exc:
                logger.debug("[MainOrchestrator] token_budget_gate skipped (fail-safe): %s", _bgt_orch_exc)

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
                        # CR-5 Sprint 2.2 observability
                        try:
                            from app.shared.observability.canary_metrics import main_orchestrator_guard_fires_total
                            if main_orchestrator_guard_fires_total is not None:
                                main_orchestrator_guard_fires_total.labels(
                                    guard="policy_gate", outcome="soft_warn",
                                ).inc()
                        except Exception:
                            pass
                        # TODO P1-W4-11: converter em hard block (return ChatResponse blocked)
                        # quando policies estiverem validadas em produção.
                except Exception as _pg_err:
                    logger.debug("[PolicyGate] P1-W4-11 evaluate error (non-blocking): %s", _pg_err)

            # GAP-00-001: LGPD consent gate (defense-in-depth) ────────────
            # get_active_candidate() reads a ContextVar set by the calling
            # layer (agent_chat_sse entity resolver). For calls from chat.py
            # without entity resolution, this is a no-op (None candidate).
            try:
                from app.shared.entity_resolver import get_active_candidate as _get_cand_orch
                _orch_cand_id = _get_cand_orch()
                if _orch_cand_id and ctx.company_id:
                    from app.core.database import AsyncSessionLocal as _ConsentASL_orch
                    from app.domains.lgpd.services.consent_checker_service import ConsentCheckerService as _CSvc_orch
                    async with _ConsentASL_orch() as _cons_db_orch:
                        _cons_result_orch = await _CSvc_orch(_cons_db_orch).check_candidate_consent(
                            candidate_id=_orch_cand_id,
                            company_id=str(ctx.company_id),
                            purpose="ai_screening",
                        )
                    if not _cons_result_orch.allowed and not _cons_result_orch.soft_warning:
                        logger.warning(
                            "[MainOrchestrator] LGPD consent revogado: company=%s candidate=%s",
                            ctx.company_id, _orch_cand_id,
                        )
                        return ChatResponse(
                            success=False,
                            content=(
                                "Nao posso processar informacoes deste candidato por IA porque o "
                                "consentimento LGPD foi revogado. Solicite novo consentimento via "
                                "Gestao de Consentimentos."
                            ),
                            agent_used="lgpd_consent_gate",
                            confidence=1.0,
                            intent_detected="blocked_consent_revoked",
                            conversation_id=conv_id,
                        )
            except Exception as _cons_orch_exc:
                logger.debug("[MainOrchestrator] consent gate (fail-safe): %s", _cons_orch_exc)

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

            # ── Phase 0-pre: Post-wizard continuity (Task #1211) ────────────
            # Runs BEFORE Phase 0 so a recruiter's natural-language reply to the
            # continuity OFFER ("sim, pode publicar" / "agora não") is handled by
            # the dedicated continuation handler — never swallowed by Phase 0 or
            # re-routed into the wizard.
            try:
                _cont_response = await self._handle_post_wizard_continuation(
                    ctx, conv_id, db, conv
                )
                if _cont_response is not None:
                    if _soft_warnings and not _cont_response.fairness_warnings:
                        _cont_response.fairness_warnings = _soft_warnings
                    return _cont_response
            except Exception as _cont_exc:
                logger.warning(
                    "[LIA-Continuity] post-wizard continuation skipped: %s",
                    _cont_exc,
                )

            # ── Phase 0-pre: P&E add-to-vacancy continuity (Task #1227) ──────
            # Mirrors post-wizard continuity: the recruiter's natural PT-BR reply
            # to the "quer que eu adicione os aprovados?" OFFER is handled here,
            # BEFORE Phase 0, so it is never swallowed as a generic param flow.
            try:
                _add_cont_response = await self._handle_pe_add_to_vacancy_continuation(
                    ctx, conv_id, db, conv
                )
                if _add_cont_response is not None:
                    if _soft_warnings and not _add_cont_response.fairness_warnings:
                        _add_cont_response.fairness_warnings = _soft_warnings
                    return _add_cont_response
            except Exception as _add_cont_exc:
                logger.warning(
                    "[LIA-P&E] add-to-vacancy continuation skipped: %s",
                    _add_cont_exc,
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
                if _defer_needs_params_to_agentic(action_response):
                    # #3 (2026-06-04): em vez de PERGUNTAR o criterio, deixa o
                    # agentic loop (Phase 1.5) extrair do NL e chamar a tool.
                    logger.info(
                        "[Phase1->Agentic] needs_params para '%s' -- deferindo ao "
                        "agentic loop (extrai do NL) em vez de pedir param. user=%s",
                        action_response.action_type, getattr(ctx, "user_id", None),
                    )
                else:
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

                    # -- /planejar Slash Command ----------------------------------------
                    import re as _re_plan
                    _msg = (ctx.message or "").strip()
                    _PLANEJAR_RE = _re_plan.compile(
                        r"^/planejar\b\s*(.*)",
                        _re_plan.IGNORECASE,
                    )
                    _planejar_match = _PLANEJAR_RE.match(_msg)
                    if _planejar_match:
                        _task_desc = _planejar_match.group(1).strip()
                        if not _task_desc:
                            _no_desc = ChatResponse(
                                success=True,
                                content=(
                                    "Use `/planejar` seguido da tarefa. Exemplo:\n\n"
                                    "- `/planejar contratar 5 devs backend ate julho`\n"
                                    "- `/planejar agendar entrevistas com os 3 melhores e enviar feedback pros reprovados`\n"
                                    "- `/planejar expandir sourcing da vaga de PM e mover aprovados`\n\n"
                                    "Ou diga **que planos tem?** para ver os templates prontos."
                                ),
                                intent_detected="planejar_usage",
                                conversation_id=conv_id,
                                action_executed=False,
                            )
                            if _soft_warnings:
                                _no_desc.fairness_warnings = _soft_warnings
                            return _no_desc

                        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
                        _auto_agent = AutomationReActAgent()
                        _decomp = await _auto_agent.decompose_task(
                            task_description=_task_desc,
                            company_id=str(getattr(ctx, "company_id", None) or ""),
                            user_id=str(getattr(ctx, "user_id", "system") or "system"),
                            persist=True,
                        )
                        _subtasks = _decomp.get("subtasks", [])
                        _plan_id = _decomp.get("plan_id", "")

                        _lines_out = ["**Plano criado** — " + str(len(_subtasks)) + " subtarefa(s):\n"]
                        for _si, _st in enumerate(_subtasks, 1):
                            _dep_str = ""
                            if _st.get("depends_on"):
                                _dep_str = " (depende de: " + ", ".join(_st["depends_on"]) + ")"
                            _lines_out.append(
                                str(_si) + ". **" + _st.get("title", _st.get("task_id", "Tarefa " + str(_si))) + "**"
                                " — " + _st.get("description", "") + _dep_str
                            )
                        if _plan_id:
                            _lines_out.append("\nPlan ID: `" + _plan_id + "`")
                        _lines_out.append("\nDiga **executar plano** para iniciar ou **ajustar plano** para refinar.")

                        _planejar_resp = ChatResponse(
                            success=True,
                            content="\n".join(_lines_out),
                            intent_detected="planejar_decompose",
                            conversation_id=conv_id,
                            action_executed=True,
                            structured_data=_decomp,
                        )
                        if _soft_warnings:
                            _planejar_resp.fairness_warnings = _soft_warnings
                        return _planejar_resp

                    # -- Auto-detect: 3+ action verbs => route to PlanDetector ---
                    _VERB_RE = _re_plan.compile(
                        r"\b(?:buscar|encontrar|pesquisar|agendar|enviar|mover|avancar"
                        r"|rejeitar|publicar|fechar|aprovar|gerar|analisar|comparar"
                        r"|importar|notificar|expandir|contratar)\b",
                        _re_plan.IGNORECASE,
                    )
                    _verb_matches = _VERB_RE.findall(_msg)
                    if len(_verb_matches) >= 3:
                        logger.info(
                            "[LIA-P&E] Auto-detect: %d action verbs in message -> PlanDetector",
                            len(_verb_matches),
                        )

                    # -- /planejar Slash Command ----------------------------------------
                    _msg = (ctx.message or "").strip()
                    _PLANEJAR_RE = _re_plan.compile(
                        r"^/planejar\b\s*(.*)",
                        _re_plan.IGNORECASE,
                    )
                    _planejar_match = _PLANEJAR_RE.match(_msg)
                    if _planejar_match:
                        _task_desc = _planejar_match.group(1).strip()
                        if not _task_desc:
                            _no_desc = ChatResponse(
                                success=True,
                                content=(
                                    "Use `/planejar` seguido da tarefa. Exemplo:\n\n"
                                    "- `/planejar contratar 5 devs backend ate julho`\n"
                                    "- `/planejar agendar entrevistas com os 3 melhores e enviar feedback pros reprovados`\n"
                                    "- `/planejar expandir sourcing da vaga de PM e mover aprovados`\n\n"
                                    "Ou diga **que planos tem?** para ver os templates prontos."
                                ),
                                intent_detected="planejar_usage",
                                conversation_id=conv_id,
                                action_executed=False,
                            )
                            if _soft_warnings:
                                _no_desc.fairness_warnings = _soft_warnings
                            return _no_desc

                        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
                        _auto_agent = AutomationReActAgent()
                        _decomp = await _auto_agent.decompose_task(
                            task_description=_task_desc,
                            company_id=str(getattr(ctx, "company_id", None) or ""),
                            user_id=str(getattr(ctx, "user_id", "system") or "system"),
                            persist=True,
                        )
                        _subtasks = _decomp.get("subtasks", [])
                        _plan_id = _decomp.get("plan_id", "")

                        _lines_out = ["**Plano criado** — " + str(len(_subtasks)) + " subtarefa(s):\n"]
                        for _si, _st in enumerate(_subtasks, 1):
                            _dep_str = ""
                            if _st.get("depends_on"):
                                _dep_str = " (depende de: " + ", ".join(_st["depends_on"]) + ")"
                            _lines_out.append(
                                str(_si) + ". **" + _st.get("title", _st.get("task_id", "Tarefa " + str(_si))) + "**"
                                " — " + _st.get("description", "") + _dep_str
                            )
                        if _plan_id:
                            _lines_out.append("\nPlan ID: `" + _plan_id + "`")
                        _lines_out.append("\nDiga **executar plano** para iniciar ou **ajustar plano** para refinar.")

                        _planejar_resp = ChatResponse(
                            success=True,
                            content="\n".join(_lines_out),
                            intent_detected="planejar_decompose",
                            conversation_id=conv_id,
                            action_executed=True,
                            structured_data=_decomp,
                        )
                        if _soft_warnings:
                            _planejar_resp.fairness_warnings = _soft_warnings
                        return _planejar_resp

                    # -- Auto-detect: 3+ action verbs => route to PlanDetector ---
                    _VERB_RE = _re_plan.compile(
                        r"\b(?:buscar|encontrar|pesquisar|agendar|enviar|mover|avancar"
                        r"|rejeitar|publicar|fechar|aprovar|gerar|analisar|comparar"
                        r"|importar|notificar|expandir|contratar)\b",
                        _re_plan.IGNORECASE,
                    )
                    _verb_matches = _VERB_RE.findall(_msg)
                    if len(_verb_matches) >= 3:
                        logger.info(
                            "[LIA-P&E] Auto-detect: %d action verbs in message -> PlanDetector",
                            len(_verb_matches),
                        )

                    # -- /planejar Slash Command ----------------------------------------
                    _msg = (ctx.message or "").strip()
                    _PLANEJAR_RE = _re_plan.compile(
                        r"^/planejar\b\s*(.*)",
                        _re_plan.IGNORECASE,
                    )
                    _planejar_match = _PLANEJAR_RE.match(_msg)
                    if _planejar_match:
                        _task_desc = _planejar_match.group(1).strip()
                        if not _task_desc:
                            _no_desc = ChatResponse(
                                success=True,
                                content=(
                                    "Use `/planejar` seguido da tarefa. Exemplo:\n\n"
                                    "- `/planejar contratar 5 devs backend ate julho`\n"
                                    "- `/planejar agendar entrevistas com os 3 melhores e enviar feedback pros reprovados`\n"
                                    "- `/planejar expandir sourcing da vaga de PM e mover aprovados`\n\n"
                                    "Ou diga **que planos tem?** para ver os templates prontos."
                                ),
                                intent_detected="planejar_usage",
                                conversation_id=conv_id,
                                action_executed=False,
                            )
                            if _soft_warnings:
                                _no_desc.fairness_warnings = _soft_warnings
                            return _no_desc

                        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
                        _auto_agent = AutomationReActAgent()
                        _decomp = await _auto_agent.decompose_task(
                            task_description=_task_desc,
                            company_id=str(getattr(ctx, "company_id", None) or ""),
                            user_id=str(getattr(ctx, "user_id", "system") or "system"),
                            persist=True,
                        )
                        _subtasks = _decomp.get("subtasks", [])
                        _plan_id = _decomp.get("plan_id", "")

                        _lines_out = ["**Plano criado** — " + str(len(_subtasks)) + " subtarefa(s):\n"]
                        for _si, _st in enumerate(_subtasks, 1):
                            _dep_str = ""
                            if _st.get("depends_on"):
                                _dep_str = " (depende de: " + ", ".join(_st["depends_on"]) + ")"
                            _lines_out.append(
                                str(_si) + ". **" + _st.get("title", _st.get("task_id", "Tarefa " + str(_si))) + "**"
                                " — " + _st.get("description", "") + _dep_str
                            )
                        if _plan_id:
                            _lines_out.append("\nPlan ID: `" + _plan_id + "`")
                        _lines_out.append("\nDiga **executar plano** para iniciar ou **ajustar plano** para refinar.")

                        _planejar_resp = ChatResponse(
                            success=True,
                            content="\n".join(_lines_out),
                            intent_detected="planejar_decompose",
                            conversation_id=conv_id,
                            action_executed=True,
                            structured_data=_decomp,
                        )
                        if _soft_warnings:
                            _planejar_resp.fairness_warnings = _soft_warnings
                        return _planejar_resp

                    # -- Auto-detect: 3+ action verbs => route to PlanDetector ---
                    _VERB_RE = _re_plan.compile(
                        r"\b(?:buscar|encontrar|pesquisar|agendar|enviar|mover|avancar"
                        r"|rejeitar|publicar|fechar|aprovar|gerar|analisar|comparar"
                        r"|importar|notificar|expandir|contratar)\b",
                        _re_plan.IGNORECASE,
                    )
                    _verb_matches = _VERB_RE.findall(_msg)
                    if len(_verb_matches) >= 3:
                        logger.info(
                            "[LIA-P&E] Auto-detect: %d action verbs in message -> PlanDetector",
                            len(_verb_matches),
                        )

                    # ── Template Discovery ────────────────────────────────
                    # Respond to "que planos tem?" / "listar templates" / etc.
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
                        # Task #1211: wire the REAL domain registry + workflow so
                        # tasks dispatch to live domains. Without these,
                        # PlanExecutor._execute_task falls into the no-registry
                        # branch and returns synthetic success for every task
                        # ("...executed (no domain registry)") — a silent fake
                        # success. Mirrors agent_chat_ws.py and legacy/orchestrator.
                        from app.domains.registry import DomainRegistry
                        from app.domains.workflow import DomainWorkflow

                        _plan_executor = PlanExecutor(
                            domain_registry=DomainRegistry(),
                            domain_workflow=DomainWorkflow(),
                        )
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

                        # Task #1227: after "buscar_pontuar_e_adicionar" (search +
                        # score), adding the approved candidates to the vacancy is a
                        # state-changing step gated behind a natural PT-BR
                        # confirmation (chat-first). Park the offer keyed by
                        # conversation and OFFER it in the same LIA message. Only
                        # fires when there ARE approved candidates AND a vacancy —
                        # otherwise no offer (honest, never a fake pending).
                        if _completed_plan.detected_pattern == "buscar_pontuar_e_adicionar":
                            try:
                                from app.orchestrator.routing.pe_add_to_vacancy_continuation import (
                                    build_add_offer_message,
                                    store_add_offer,
                                )

                                _approved_ids = (
                                    _completed_plan.get_context("task_1.approved_candidate_ids")
                                    or []
                                )
                                _add_job_id = _completed_plan.get_context("task_1.job_id")
                                _offer = store_add_offer(
                                    conv_id,
                                    str(_pe_company_id) if _pe_company_id else None,
                                    _add_job_id,
                                    _approved_ids,
                                )
                                if _offer is not None:
                                    _plan_text = _plan_text + build_add_offer_message(
                                        len(_offer.collected_params["approved_candidate_ids"])
                                    )
                            except Exception as _offer_exc:
                                logger.warning(
                                    "[LIA-P&E] add-to-vacancy offer skipped: %s",
                                    _offer_exc,
                                )

                        if conv and not ctx.skip_memory_persist:
                            try:
                                await self._persist_response(
                                    ctx, conv_id, conv, {"response": _plan_text}, db
                                )
                            except Exception as _pe_exc:
                                logger.warning("[LIA-P&E] memory persist failed: %s", _pe_exc)

                        # Task #1222: derive success/action_executed from the REAL
                        # plan result — never hardcode True. When a step handed off
                        # to a continuous agent (honest handoff), the consolidated
                        # response is success=False, so the envelope must NOT claim
                        # the action was executed.
                        _plan_handoffs = (_plan_domain_resp.metadata or {}).get("agent_handoffs", [])
                        _plan_resp = ChatResponse(
                            success=_plan_domain_resp.success,
                            content=_plan_text,
                            intent_detected="plan_execute",
                            conversation_id=conv_id,
                            action_executed=_plan_domain_resp.success,
                            structured_data={
                                "plan_id": _completed_plan.plan_id,
                                "pattern": _completed_plan.detected_pattern,
                                "tasks": len(_completed_plan.tasks),
                                "status": _completed_plan.status.value,
                                "agent_handoffs": _plan_handoffs,
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
                        _persona_cid = _loop_company_id
                        if _persona_cid:
                            from app.shared.prompts.persona_aware_prompt import (
                                build_system_prompt_with_persona,
                            )
                            from lia_config.database import AsyncSessionLocal
                            async with AsyncSessionLocal() as _persona_db:
                                _phase15_system_prompt = (
                                    await build_system_prompt_with_persona(
                                        company_id=str(_persona_cid),
                                        db=_persona_db,
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
                                        context_page=getattr(
                                            ctx, "context_page", "general"
                                        )
                                        or "general",
                                        entity_type=getattr(ctx, "entity_type", None),
                                    )
                                )
                        else:
                            _phase15_system_prompt = SystemPromptBuilder.build(
                                ai_persona=None,
                                agent_type="orchestrator",
                                company_id=(
                                    str(_loop_company_id)
                                    if _loop_company_id
                                    else None
                                ),
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

                    # Fase B P0.1 (2026-06-04): injeta o contexto da tela
                    # (view_context) no system prompt -> supervisor abre ciente
                    # do que o recrutador ve agora (page_type + counts + filtros).
                    try:
                        from app.orchestrator.context.view_context import format_view_context
                        _vc_snip = format_view_context(getattr(ctx, "view_context", None))
                        if _vc_snip:
                            _phase15_system_prompt = (_phase15_system_prompt or "") + "\n\n" + _vc_snip
                    except Exception:
                        pass

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
                        "amigável + pergunta aberta natural. "
                        "**NÃO chame ferramenta nenhuma.** Não chute "
                        "`search_jobs`, `search_candidates`, "
                        "`check_company_completeness` ou qualquer tool quando "
                        "não há contexto explícito.\n\n"
                        "Sub-regra anti-spam de capabilities (CR-4 Sprint 2.3 2026-05-26):\n"
                        "**NUNCA enumere features, capabilities ou áreas como "
                        "lista bullet em saudações OU em qualquer turn "
                        "subsequente**. Se você acabou de listar capabilities "
                        "uma vez, NÃO repita na próxima resposta. Conflita "
                        "com lia_persona.yaml Anti-pattern #1 e gera ruído "
                        "(transcript Paulo 2026-05-26 mostrou LIA repetindo "
                        "mesma lista 3x na mesma conversa).\n\n"
                        "Exemplo correto (CONTEXTUAL, sem enumerar features):\n"
                        "User: \"oi\"\n"
                        "Você (sem contexto): \"Olá! 👋 Como posso ajudar você hoje?\"\n"
                        "Você (com 3 vagas abertas no contexto): \"Olá! Vi "
                        "que você tem 3 vagas abertas. Quer revisar o pipeline "
                        "de alguma delas?\"\n\n"
                        "Exemplo ERRADO ❌ (NÃO faça — gera capability spam):\n"
                        "User: \"oi\"\n"
                        "Você: \"Olá! Posso te mostrar vagas em aberto, "
                        "status de candidatos, ou indicadores...\" "
                        "← isso é uma mini-lista de features, ANTI-PATTERN.\n\n"
                        "Exemplo ERRADO ❌ (não chame tool em saudação):\n"
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

                    # Sprint 3.4 G9 wire (2026-05-26) — inject proactive
                    # context notes from Settings hub. Frontend
                    # settings-notify.ts (debounced 1500ms) POSTou notes
                    # para Redis via ProactiveContextStore (Sprint 3.2/3.3).
                    # Aqui, ao construir o system_prompt do agentic loop,
                    # buscamos notes recentes do user+company e incluímos
                    # em context_block. LLM próximo turn vê e reage
                    # proativamente respeitando lia_persona.yaml
                    # Anti-pattern #1 (NÃO bullet-list capabilities; sim,
                    # contextual sugestões baseadas no que mudou).
                    # Fail-open: Redis down -> empty list -> sem injeção.
                    try:
                        from app.shared.services.proactive_context_store import (
                            ProactiveContextStore,
                            PROACTIVE_CTX_MAX_NOTES,  # PR-12/F-4.15 env-tunable
                            proactive_context_inject_counter,  # PR-12/F-4.14
                        )
                        _pc_notes = await ProactiveContextStore.list_recent(
                            company_id=str(_loop_company_id or ""),
                            user_id=str(getattr(ctx, "user_id", None) or ""),
                            limit=PROACTIVE_CTX_MAX_NOTES,
                        )
                        if _pc_notes:
                            _pc_lines = [
                                "\n\n### Contexto recente das configurações (últimos 30min)\n",
                                "O recrutador acabou de editar configurações via UI. "
                                "Considere reagir proativamente (sugerir complementos, "
                                "validar consistência, ou continuar silencioso se não "
                                "houver follow-up útil). NUNCA enumere features (Anti-"
                                "pattern #1) — comente APENAS o que mudou se relevante.",
                                "",
                            ]
                            for _n in _pc_notes[:PROACTIVE_CTX_MAX_NOTES]:
                                _act = str(_n.get("action_id") or "")
                                _sec = str(_n.get("section") or "")
                                _fld = _n.get("field")
                                _val = _n.get("value")
                                _fld_part = f' · campo "{_fld}"' if _fld else ""
                                _val_part = ""
                                if _val is not None:
                                    _val_str = str(_val)
                                    if len(_val_str) > 200:
                                        _val_str = _val_str[:200] + "…"
                                    _val_part = f" = {_val_str}"
                                _pc_lines.append(
                                    f"- {_sec}{_fld_part}{_val_part}  (ação: {_act})"
                                )
                            _phase15_system_prompt += "\n".join(_pc_lines)
                            logger.info(
                                "[MainOrchestrator] Sprint 3.4 G9: injected %d proactive "
                                "context notes (company=%s user=%s)",
                                len(_pc_notes), _loop_company_id,
                                getattr(ctx, "user_id", None),
                            )
                            # PR-12 / F-4.14 — telemetry: count successful injections
                            if proactive_context_inject_counter is not None:
                                try:
                                    proactive_context_inject_counter.labels(
                                        path="orchestrator", status="hit"
                                    ).inc()
                                except Exception:
                                    pass
                            # Clear notes consumed para evitar re-injeção
                            # no próximo turn (LIA já viu). Fail-open.
                            try:
                                await ProactiveContextStore.clear_consumed(
                                    company_id=str(_loop_company_id or ""),
                                    user_id=str(getattr(ctx, "user_id", None) or ""),
                                )
                            except Exception:
                                pass
                    except Exception as _pc_exc:
                        logger.debug(
                            "[MainOrchestrator] proactive context inject failed (fail-open): %s",
                            _pc_exc,
                        )
                        # PR-12 / F-4.14 — telemetry: count fail-open occurrences
                        try:
                            from app.shared.services.proactive_context_store import (
                                proactive_context_inject_counter as _ctr,
                            )
                            if _ctr is not None:
                                _ctr.labels(path="orchestrator", status="fail_open").inc()
                        except Exception:
                            pass

                    # Supervisor tool scoping (paridade com agente federado):
                    # deriva scope via page_type do view_context que o SSE ja popula.
                    # Fail-open: scope indefinido ou GLOBAL -> tools_override=None
                    # -> agentic_loop usa todos os tools (comportamento anterior).
                    _tools_override: list[str] | None = None
                    try:
                        from app.tools.scope_config import (
                            scope_for_context,
                            get_tools_for_scope,
                            PromptScope,
                        )
                        _vc = getattr(ctx, "view_context", None) or {}
                        _pt = _vc.get("page_type") if isinstance(_vc, dict) else None
                        _scope = scope_for_context(_pt, None)
                        if _scope != PromptScope.GLOBAL:
                            _scoped = get_tools_for_scope(_scope)
                            if _scoped:
                                _tools_override = list(_scoped)
                    except Exception as _scope_exc:
                        logger.debug(
                            "[MainOrchestrator] tool scope (fail-open): %s", _scope_exc
                        )

                    _agentic_result = await agentic_loop.run(
                        user_message=ctx.message,
                        system_prompt=_phase15_system_prompt,
                        conversation_history=ctx.extra.get("conversation_history", []),
                        company_id=_loop_company_id,
                        user_id=getattr(ctx, "user_id", None),
                        session_id=conv_id,
                        provider=_agentic_provider,
                        tools_override=_tools_override,
                    )

                    # Step C (2026-06-04): consome a diretiva surfaçada por um
                    # tool result. ADITIVO — só dispara quando um tool retornou
                    # ``ui_action == "start_wizard_seeded"`` (ex.:
                    # start_creation_from_source). Em turno de chat NORMAL o
                    # campo é None e nada muda. O recrutador entra direto no
                    # wizard semeado a partir do template, em vez do texto cru.
                    _directive = (_agentic_result or {}).get("tool_directive")
                    if (
                        _directive
                        and _directive.get("ui_action") == "start_wizard_seeded"
                        and _directive.get("seed_source")
                    ):
                        logger.info(
                            "[MainOrchestrator] tool directive start_wizard_seeded "
                            "consumida (session=%s seed=%s) — desviando para o "
                            "wizard semeado.",
                            conv_id, _directive.get("seed_source"),
                        )
                        _seeded_resp = await self._start_seeded_wizard(
                            ctx, conv_id, conv, db,
                            seed_source=_directive["seed_source"],
                        )
                        if _soft_warnings and not _seeded_resp.fairness_warnings:
                            _seeded_resp.fairness_warnings = _soft_warnings
                        _enrich_suggested_prompts(_seeded_resp, ctx)
                        return _seeded_resp

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

                        # Fase B (2026-06-06): propaga a diretiva open_modal
                        # surfaçada por open_ui → ui_action/ui_action_params
                        # na resposta (FE LIAGlobalModals escuta lia:open_modal).
                        # Aditivo: None em turno normal.
                        _modal_ui_action = None
                        _modal_ui_params = None
                        if _directive and _directive.get("ui_action") in _FE_TOOL_UI_ACTIONS:
                            _modal_ui_action = _directive.get("ui_action")
                            _modal_ui_params = _directive.get("ui_action_params")
                        elif _directive and _directive.get("ui_action"):
                            # P-FAILLOUD: a non-None directive arrived at gate 2 with an unknown ui_action.
                            # This should be impossible after gate 1 is wired to the same canonical source.
                            # If this fires, it means a code path bypassed gate 1 or the canonical is out of sync.
                            logger.warning(
                                "gate2: ui_action %r passed gate1 but is not in _FE_TOOL_UI_ACTIONS -- "
                                "invariant violation, check app/shared/ui_action_canonical.py",
                                _directive.get("ui_action"),
                            )
                        _resp = ChatResponse(
                            success=True,
                            content=_agentic_result["response"],
                            intent_detected="agentic_tool_call",
                            conversation_id=conv_id,
                            action_executed=bool(_agentic_result.get("tool_calls_made")),
                            ui_action=_modal_ui_action,
                            ui_action_params=_modal_ui_params,
                            structured_data={
                                "tool_calls": _agentic_result.get("tool_calls_made", []),
                                "iterations": _agentic_result.get("iterations", 0),
                            },
                            response_blocks=_agentic_result.get("response_blocks"),
                            hitl_pending=_agentic_result.get("hitl_pending"),  # F5 supervisor HITL drain (2026-06-09)
                        )
                        if _soft_warnings:
                            _resp.fairness_warnings = _soft_warnings
                        # Sprint 14.4: enrich suggested_prompts when empty + page known
                        _enrich_suggested_prompts(_resp, ctx)
                        return _resp

                    # Canonical (2026-06-04): transient provider overload
                    # (HTTP 529). Don't blame the user's phrasing for a
                    # provider outage — return an honest, overload-specific
                    # message instead of the generic V1 fallback. (REGRA-4.)
                    if (
                        _agentic_result
                        and _agentic_result.get("failure_reason")
                        == "provider_overloaded"
                    ):
                        logger.warning(
                            "[MainOrchestrator] Agentic loop provider-overloaded "
                            "after retries — honest fail (user=%s company=%s).",
                            getattr(ctx, "user_id", None), ctx.company_id,
                        )
                        return ChatResponse(
                            success=False,
                            content=(
                                "Os servidores de IA estão sobrecarregados neste "
                                "instante. Pode tentar de novo em alguns segundos? "
                                "Sua pergunta está ok — é só uma instabilidade "
                                "temporária do provedor."
                            ),
                            agent_used="agentic_loop",
                            confidence=0.0,
                            intent_detected="provider_overloaded",
                            conversation_id=conv_id,
                            error_code="PROVIDER_OVERLOADED",
                            error_category="transient",
                        )
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
    # Phase 0-pre — Post-wizard continuity (Task #1211)
    # ------------------------------------------------------------------

    async def _handle_post_wizard_continuation(
        self, ctx: UniversalContext, conv_id: str, db: Any, conv: Any = None
    ) -> ChatResponse | None:
        """Handle the recruiter's reply to a post-wizard continuity OFFER.

        Only fires when a continuation is parked AND already offered
        (``awaiting_confirmation``). Classifies the free-text PT-BR reply:
          • ``no``  → acknowledge, drop the continuation;
          • ``ambiguous`` → re-ask, keep it pending;
          • ``yes`` + connected → execute via the canonical Plan & Execute path
            (real domain registry) bound to the created ``job_id``;
          • ``yes`` + not-connected → explicit "ainda não conectado" (NEVER a
            fake success).

        INVIOLABLE: this NEVER creates a job — it only runs already-connected
        follow-ups (ATS publish/sync) on the job the wizard already created.
        """
        from app.orchestrator.routing.confirmation_classifier import (
            classify_confirmation,
        )
        from app.orchestrator.routing.post_wizard_continuation import (
            clear_continuation,
            dispatch_for,
            get_continuation,
        )

        state = get_continuation(conv_id)
        if state is None or not state.awaiting_confirmation:
            return None

        decision = classify_confirmation(ctx.message)
        logger.info(
            "[LIA-Continuity] offer reply classified=%s conv=%s kind=%s",
            decision, conv_id, (state.collected_params or {}).get("continuation_kind"),
        )

        def _finish(content: str, *, intent: str, executed: bool,
                    structured: dict[str, Any] | None = None) -> ChatResponse:
            if conv and not ctx.skip_memory_persist:
                try:
                    import asyncio as _aio
                    _aio.ensure_future(
                        self._persist_response(
                            ctx, conv_id, conv, {"response": content}, db
                        )
                    )
                except Exception as _pexc:
                    logger.debug("[LIA-Continuity] persist skipped: %s", _pexc)
            return ChatResponse(
                success=True,
                content=content,
                agent_used="post_wizard_continuation",
                confidence=0.95,
                intent_detected=intent,
                conversation_id=conv_id,
                action_executed=executed,
                structured_data=structured,
            )

        if decision == "ambiguous":
            # Keep the offer pending; ask one clear yes/no question.
            return _finish(
                "Só pra confirmar: quer que eu siga com essa etapa agora? "
                "Responda *sim* ou *agora não*.",
                intent="continuation_clarify",
                executed=False,
            )

        if decision == "no":
            clear_continuation(conv_id)
            return _finish(
                "Combinado — a vaga fica como está por enquanto. "
                "Quando quiser seguir, é só me avisar.",
                intent="continuation_declined",
                executed=False,
            )

        # decision == "yes" — consume the continuation regardless of outcome.
        params = dict(state.collected_params or {})
        connected = bool(params.get("continuation_connected"))
        dispatch = dispatch_for(params.get("continuation_kind"))
        job_id = params.get("job_id")
        clear_continuation(conv_id)

        if not connected or not dispatch:
            # Explicit signal — never pretend an unconnected step ran.
            return _finish(
                "Essa etapa ainda não está conectada para execução automática, "
                "então não vou marcá-la como concluída — por enquanto você "
                "precisa fazê-la manualmente. Posso ajudar em mais alguma coisa?",
                intent="continuation_not_connected",
                executed=False,
            )

        domain_id, action_id, label = dispatch

        # Execute through the canonical Plan & Execute path with the REAL domain
        # registry (no fake success) — single follow-up task on the created job.
        from app.domains.registry import DomainRegistry
        from app.domains.workflow import DomainWorkflow
        from app.shared.execution.execution_plan import AgentTask, ExecutionPlan
        from app.shared.execution.plan_executor import PlanExecutor

        _plan = ExecutionPlan(plan_id=f"continuation_{conv_id}")
        _plan.detected_pattern = f"post_wizard_{params.get('continuation_kind')}"
        _plan.add_task(
            AgentTask(
                task_id="task_0",
                domain_id=domain_id,
                action_id=action_id,
                params={"job_id": job_id} if job_id else {},
            )
        )
        _company_id = getattr(ctx, "company_id", None)
        _executor = PlanExecutor(
            domain_registry=DomainRegistry(),
            domain_workflow=DomainWorkflow(),
        )
        _completed = await _executor.execute(
            _plan,
            user_id=str(getattr(ctx, "user_id", "system") or "system"),
            session_id=conv_id or "",
            tenant_id=str(_company_id) if _company_id else None,
            base_context={"job_id": job_id} if job_id else None,
        )
        _domain_resp = _executor.build_consolidated_response(_completed)
        logger.info(
            "[LIA-Continuity] continuation executed kind=%s job_id=%s status=%s",
            params.get("continuation_kind"), job_id, _completed.status.value,
        )
        return _finish(
            _domain_resp.message,
            intent="continuation_executed",
            executed=True,
            structured={
                "plan_id": _completed.plan_id,
                "pattern": _completed.detected_pattern,
                "status": _completed.status.value,
                "continuation_kind": params.get("continuation_kind"),
                "job_id": job_id,
            },
        )

    # ------------------------------------------------------------------
    # Phase 0-pre — P&E add-to-vacancy continuity (Task #1227)
    # ------------------------------------------------------------------

    async def _handle_pe_add_to_vacancy_continuation(
        self, ctx: UniversalContext, conv_id: str, db: Any, conv: Any = None
    ) -> ChatResponse | None:
        """Handle the recruiter's reply to the "add approved to vacancy" OFFER.

        Only fires when a ``pe_add_to_vacancy`` continuation is parked AND
        awaiting confirmation (set by Phase 1.3 after scoring). Classifies the
        free-text PT-BR reply:
          • ``no``  → acknowledge, drop the offer;
          • ``ambiguous`` → re-ask, keep it pending;
          • ``yes`` → execute ``cv_screening.add_approved_to_vacancy`` via the
            canonical Plan & Execute path (real domain registry — no fake
            success), scoped to the parked ``job_id`` + approved ids.

        INVIOLABLE (#1211): never creates a job — only adds existing candidates
        to the existing vacancy.
        """
        from app.orchestrator.routing.confirmation_classifier import (
            classify_confirmation,
        )
        from app.orchestrator.routing.pe_add_to_vacancy_continuation import (
            clear_add_continuation,
            get_add_continuation,
        )

        state = get_add_continuation(conv_id)
        if state is None or not state.awaiting_confirmation:
            return None

        decision = classify_confirmation(ctx.message)
        logger.info(
            "[LIA-P&E] add-to-vacancy offer reply classified=%s conv=%s",
            decision, conv_id,
        )

        def _finish(content: str, *, intent: str, executed: bool,
                    structured: dict[str, Any] | None = None) -> ChatResponse:
            if conv and not ctx.skip_memory_persist:
                try:
                    import asyncio as _aio
                    _aio.ensure_future(
                        self._persist_response(
                            ctx, conv_id, conv, {"response": content}, db
                        )
                    )
                except Exception as _pexc:
                    logger.debug("[LIA-P&E] add continuation persist skipped: %s", _pexc)
            return ChatResponse(
                success=True,
                content=content,
                agent_used="pe_add_to_vacancy_continuation",
                confidence=0.95,
                intent_detected=intent,
                conversation_id=conv_id,
                action_executed=executed,
                structured_data=structured,
            )

        if decision == "ambiguous":
            return _finish(
                "Só pra confirmar: quer que eu adicione os aprovados à vaga agora? "
                "Responda *sim* ou *agora não*.",
                intent="add_to_vacancy_clarify",
                executed=False,
            )

        if decision == "no":
            clear_add_continuation(conv_id)
            return _finish(
                "Combinado — não vou adicionar ninguém por enquanto. "
                "Quando quiser, é só me avisar.",
                intent="add_to_vacancy_declined",
                executed=False,
            )

        # decision == "yes" — consume the offer and execute the real add.
        params = dict(state.collected_params or {})
        job_id = params.get("job_id")
        approved_ids = list(params.get("approved_candidate_ids") or [])
        clear_add_continuation(conv_id)

        from app.domains.registry import DomainRegistry
        from app.domains.workflow import DomainWorkflow
        from app.shared.execution.execution_plan import AgentTask, ExecutionPlan
        from app.shared.execution.plan_executor import PlanExecutor

        _plan = ExecutionPlan(plan_id=f"add_to_vacancy_{conv_id}")
        _plan.detected_pattern = "pe_add_to_vacancy"
        _plan.add_task(
            AgentTask(
                task_id="task_0",
                domain_id="cv_screening",
                action_id="add_approved_to_vacancy",
                params={"job_id": job_id, "approved_candidate_ids": approved_ids},
            )
        )
        _company_id = getattr(ctx, "company_id", None)
        _executor = PlanExecutor(
            domain_registry=DomainRegistry(),
            domain_workflow=DomainWorkflow(),
        )
        _completed = await _executor.execute(
            _plan,
            user_id=str(getattr(ctx, "user_id", "system") or "system"),
            session_id=conv_id or "",
            tenant_id=str(_company_id) if _company_id else None,
            base_context={"job_id": job_id, "approved_candidate_ids": approved_ids},
        )
        _domain_resp = _executor.build_consolidated_response(_completed)
        logger.info(
            "[LIA-P&E] add-to-vacancy executed job_id=%s count=%d status=%s",
            job_id, len(approved_ids), _completed.status.value,
        )
        return _finish(
            _domain_resp.message,
            intent="add_to_vacancy_executed",
            executed=_domain_resp.success,
            structured={
                "plan_id": _completed.plan_id,
                "pattern": _completed.detected_pattern,
                "status": _completed.status.value,
                "job_id": job_id,
            },
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
        # Task #1211: post-wizard continuation pendings are owned exclusively by
        # _handle_post_wizard_continuation (runs BEFORE this phase). Skip them
        # here so Phase 0 never mistakes a parked continuation for a
        # param-collection / confirmation flow and hijacks the wizard turns.
        # Task #1227: same for the P&E add-to-vacancy continuation, owned by
        # _handle_pe_add_to_vacancy_continuation (also runs BEFORE this phase).
        from app.orchestrator.routing.post_wizard_continuation import (
            CONTINUATION_INTENT,
        )
        from app.orchestrator.routing.pe_add_to_vacancy_continuation import (
            ADD_CONTINUATION_INTENT,
        )
        if pending.intent in (CONTINUATION_INTENT, ADD_CONTINUATION_INTENT):
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
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        from app.orchestrator.routing.post_wizard_continuation import (
            build_offer_message,
            mark_offered,
            store_continuation,
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

        # Bootstrap (turno 1): se a mensagem casa com _WIZARD_START_PATTERNS
        # (mesma fonte canônica de JobCreationDomain.process_intent), delega —
        # isso marca a sessão para o pin assumir nos turnos seguintes.
        if not is_wizard_turn:
            _msg_lower = message_text.lower()
            # Task #1211: detect_job_creation ALSO catches composite phrasings the
            # substring patterns miss — e.g. "criar a vaga e publicar" (has
            # "criar a vaga", not "criar vaga") which would otherwise leak into
            # Phase 1.3 Plan & Execute. Job creation must ALWAYS land in the wizard.
            _creation = detect_job_creation(message_text)
            # GUIDE (2026-06-04): se a intencao e criar A PARTIR DE uma fonte
            # (template/vaga existente), NAO bootstrapa o wizard vazio — deixa
            # cair pra Phase 1.5 (recruiter_copilot identifica a fonte via
            # list_job_creation_sources + start_creation_from_source). "criar
            # vaga"/"nova vaga" simples seguem bootstrapando como hoje.
            if _is_create_from_source(message_text):
                logger.info(
                    "[MainOrchestrator] create-from-source detectado — defere "
                    "bootstrap do wizard vazio para Phase 1.5 (session=%s).",
                    session_id,
                )
            elif any(p in _msg_lower for p in self._WIZARD_START_PATTERNS) or (
                _creation is not None and _creation.is_creation
            ):
                is_wizard_turn = True
                logger.info(
                    "[MainOrchestrator] Wizard bootstrap (turno 1): match "
                    "session=%s company=%s composite=%s",
                    session_id, company_id,
                    bool(_creation and _creation.continuation_text),
                )
                # Park the optional composite continuation (e.g. "...e publicar")
                # so LIA can OFFER it once the wizard finishes. The wizard still
                # creates the job ALONE — nothing is executed now.
                if _creation is not None and _creation.continuation_text:
                    try:
                        store_continuation(
                            conv_id or session_id,
                            company_id,
                            _creation,
                            message_text,
                        )
                    except Exception as _store_exc:
                        logger.debug(
                            "[LIA-Continuity] store_continuation skipped: %s",
                            _store_exc,
                        )

        if not is_wizard_turn:
            return None

        # ── Delegação canônica para WizardSessionService ──
        # Delegação canônica ÚNICA via _start_seeded_wizard — reusa o mesmo
        # helper que a diretiva ``start_wizard_seeded`` consome (Step B dedup,
        # 2026-06-04). Sem seed_source para o caminho bootstrap/continuação.
        return await self._start_seeded_wizard(ctx, conv_id, conv, db, seed_source=None)

    async def _start_seeded_wizard(
        self,
        ctx: UniversalContext,
        conv_id: str,
        conv: Any,
        db: Any,
        seed_source: "dict | None" = None,
    ) -> ChatResponse:
        """Canonical: delega ao ``WizardSessionService`` e empacota a resposta.

        ÚNICA implementação da delegação wizard + construção de resposta usada
        por DOIS caminhos (single source of truth — CLAUDE.md canonical-fix):

          1. ``_try_wizard_canonical`` (bootstrap turno-1 / continuação pin) —
             chama com ``seed_source=None``.
          2. Diretiva ``start_wizard_seeded`` surfaçada por um tool result no
             agentic loop (``start_creation_from_source``) — chama com
             ``seed_source={"type":"template","id":...}`` para SEMEAR uma
             sessão FRESH a partir do arquétipo. ``process_message`` lê
             ``context["seed_source"]`` no bootstrap da sessão.

        Multi-tenancy: ``company_id`` do ``ctx`` (JWT), NUNCA do payload.
        """
        from app.domains.job_creation.services.wizard_session_service import (
            WizardSessionService,
        )
        from app.orchestrator.routing.post_wizard_continuation import (
            build_offer_message,
            mark_offered,
        )
        from app.shared.sessions import derive_thread_id

        message_text = (ctx.message or "").strip()
        company_id = str(ctx.company_id) if ctx.company_id else None
        session_id = conv_id or str(uuid.uuid4())

        # Task #1080: thread_id derivado pelo helper canônico puro
        # (app.shared.sessions.derive_thread_id), única fonte de verdade
        # cross-transport (WS / SSE / REST orchestrator).
        thread_id = derive_thread_id(company_id, session_id)

        # context dict espelha o que agent_chat_ws.py monta — mantém paridade
        # com o caminho WS para que ``_build_state`` funcione idêntico.
        wiz_context: dict[str, Any] = dict(ctx.extra or {})
        wiz_context.setdefault("user_id", ctx.user_id)
        wiz_context.setdefault("user_name", ctx.user_name or None)
        wiz_context.setdefault("user_email", ctx.user_email or None)
        wiz_context.setdefault("company_id", company_id)
        wiz_context.setdefault("session_id", session_id)
        if getattr(ctx, "tenant_context_snippet", ""):
            wiz_context.setdefault(
                "tenant_context_snippet", ctx.tenant_context_snippet
            )
        # Diretiva create-from-source (2026-06-04): injeta seed_source para o
        # produtor canônico (WizardSessionService.seed_initial_state) semear o
        # state FRESH a partir do template. Sobrescreve sempre — é a intenção
        # explícita do recrutador para este turno.
        if seed_source:
            wiz_context["seed_source"] = seed_source
            logger.info(
                "[MainOrchestrator] seeded-wizard start: session=%s seed=%s",
                session_id, seed_source,
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

        # ── Post-wizard continuity OFFER (Task #1211) ──────────────────────
        # When the wizard reaches a terminal stage and a composite continuation
        # was parked at bootstrap, LIA proactively OFFERS the remaining task in
        # the chat (conversational, no buttons). Execution happens only on the
        # recruiter's natural-language confirmation, on the NEXT turn, via
        # _handle_post_wizard_continuation. The wizard already created the job.
        try:
            _stage = (ws_stage_payload or {}).get("stage", "")
            _DONE_STAGES = {"done", "completed", "finished", "handoff"}
            if _stage in _DONE_STAGES:
                _job_id = None
                if ws_stage_payload:
                    _job_id = ws_stage_payload.get("job_vacancy_id") or (
                        ws_stage_payload.get("data") or {}
                    ).get("job_id")
                _offered = mark_offered(conv_id, _job_id)
                if _offered is not None:
                    recruiter_msg = recruiter_msg + build_offer_message(_offered)
                    logger.info(
                        "[LIA-Continuity] offer surfaced conv=%s stage=%s job_id=%s",
                        conv_id, _stage, _job_id,
                    )
        except Exception as _offer_exc:
            logger.debug(
                "[LIA-Continuity] post-wizard offer skipped: %s", _offer_exc
            )

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
            "stage=%s payload=%s seeded=%s",
            session_id, thread_id,
            (ws_stage_payload or {}).get("stage", "?"),
            "yes" if ws_stage_payload else "no",
            "yes" if seed_source else "no",
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
