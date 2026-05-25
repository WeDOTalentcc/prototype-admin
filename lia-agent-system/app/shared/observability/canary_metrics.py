"""WT-2022 Canary metrics canonical (harness-engineering, registrado 2026-05-21).

Counters Prometheus para deteccao de regressoes silenciosas em paths
criticos de seguranca / multi-tenancy / LGPD. Pattern canonical alinhado
com app/jobs/tenant_aware_task.py: import seguro, reuso de collector
existente quando ja registrado, fail-open (None) quando prometheus_client
indisponivel.

Counters expostos:

- ai_credit_exhausted_total -- ai_credit_gate.check_credit_budget
  bloqueou execucao (sucesso do gate; spike = budget mal dimensionado
  ou ataque de exaustao).
- fairness_guard_skip_total -- FairnessGuard caiu em fail-soft path
  (REGRA 4 violation indicator -- toda silent fallback eh bug em paths
  de IA criticos).
- dsr_overdue_created_total -- alerts criados pelo cron
  dsr.check_overdue_daily. Sinal de saude do SLA worker LGPD
  (zero = worker possivelmente travado).
- tasks_cross_tenant_blocked_total -- tasks_repository raise
  ValueError por company_id ausente. Sinal de saude do gate fail-closed
  (qualquer incremento = bug em caller que esqueceu de propagar
  RuntimeContext, NAO violation real).
- policy_engine_runtime_invocations_total -- contador de invocacoes dos
  metodos publicos do PolicyEngineService (evaluate / check_rate_limit /
  trigger_escalation). Sinal de saude do gate Sprint Governance:
  ausencia de invocacoes por 24h+ = ghost reincidente (V2 sem caller).
  Hardening C.2.
- granular_consent_revoke_per_purpose_total -- contador de revoke de
  consentimento granular LGPD por finalidade. Sinal de UX/LGPD:
  spike sugere falha de UX ou perda de confianca; spike em uma unica
  finalidade sugere bug naquele consumer. Hardening C.3.

Uso (call site):

    from app.shared.observability.canary_metrics import (
        ai_credit_exhausted_total,
        fairness_guard_skip_total,
    )
    if ai_credit_exhausted_total is not None:
        ai_credit_exhausted_total.labels(
            company_id_hash=hashlib.sha256(company_id.encode()).hexdigest()[:12]
        ).inc()

Labels:

- company_id_hash -- SHA-256[:12] do company_id, evita cardinality
  explosion (Prometheus best practice: < 10k unique label values por
  metric). Hash deterministico permite cross-reference com logs.
  NUNCA usar company_id RAW como label (alta cardinalidade + LGPD).
- caller_module -- str do __name__ do modulo que emitiu (helps debug
  qual callsite esta em fail-soft).
- method -- str do metodo de repository que levantou (granularidade
  pra alarme).
- purpose -- finalidade canonical de consent granular (ai_screening,
  ai_scoring, ai_video_analysis, ai_comparison, data_retention,
  marketing, analytics, training_data, ats_sharing). Whitelist
  enforced em inc_granular_consent_revoke pra prevenir cardinality
  explosion via typos.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Safe Prometheus import (fail-open quando lib indisponivel).
# Reuso de collector ja registrado evita "Duplicated timeseries"
# em hot-reload (uvicorn --reload, pytest re-import).
# ----------------------------------------------------------------------
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter
    from prometheus_client import Gauge as _PromGauge
    from prometheus_client import Histogram as _PromHistogram
except Exception:  # pragma: no cover -- prometheus opcional em dev
    _PROM_REGISTRY = None  # type: ignore[assignment]
    _PromCounter = None  # type: ignore[assignment]
    _PromGauge = None  # type: ignore[assignment]
    _PromHistogram = None  # type: ignore[assignment]


def _make_counter(name: str, doc: str, labels: tuple[str, ...] | tuple = ()):
    """Cria Counter Prometheus ou reusa existente. None se lib indisponivel."""
    if _PromCounter is None or _PROM_REGISTRY is None:
        return None
    try:
        existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(name)
        if existing is not None:
            return existing
        if labels:
            return _PromCounter(name, doc, labelnames=labels)
        return _PromCounter(name, doc)
    except Exception:  # pragma: no cover -- fail-open
        logger.debug("canary_metrics: failed to register %s", name, exc_info=True)
        return None




def _make_gauge(name: str, doc: str, labels=()):
    """Cria Gauge Prometheus ou reusa existente. None se lib indisponivel."""
    if _PromGauge is None or _PROM_REGISTRY is None:
        return None
    try:
        existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(name)
        if existing is not None:
            return existing
        if labels:
            return _PromGauge(name, doc, labelnames=labels)
        return _PromGauge(name, doc)
    except Exception:
        logger.debug("canary_metrics: failed to register gauge %s", name, exc_info=True)
        return None


def _make_histogram(name: str, doc: str, labels=(), buckets=None):
    """Cria Histogram Prometheus ou reusa existente. None se lib indisponivel."""
    if _PromHistogram is None or _PROM_REGISTRY is None:
        return None
    try:
        existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(name)
        if existing is not None:
            return existing
        kwargs = {}
        if labels:
            kwargs["labelnames"] = labels
        if buckets is not None:
            kwargs["buckets"] = buckets
        return _PromHistogram(name, doc, **kwargs)
    except Exception:
        logger.debug("canary_metrics: failed to register histogram %s", name, exc_info=True)
        return None


ai_credit_exhausted_total = _make_counter(
    "ai_credit_exhausted_total",
    "Count of ai_credit_gate.check_credit_budget rejections (gate success).",
    ("company_id_hash", "service"),
)

# Wave 3 fix (2026-05-22): universal SDK monkey-patch in llm_bootstrap.
# Increments on EVERY gated LLM call (allowed or denied) to give visibility into
# coverage gap closure. Compared against ai_credit_exhausted_total it answers
# 'what fraction of LLM calls hit the gate vs exhausted?'.
ai_credit_gate_calls_total = _make_counter(
    "ai_credit_gate_calls_total",
    "Count of LLM calls intercepted by ai_credit_gate (Wave 3 universal coverage).",
    ("provider", "service", "outcome"),
)

# Wave 4 follow-up (2026-05-22) - LLM guards installation sanity.
# Gauge set to 1 by install_llm_guards() once per process (FastAPI startup,
# Celery worker_process_init, etc). Grafana alarm: any entry point where
# gauge=0 indicates SDK bypass risk (Gap 1: Celery workers/voice bypass).
llm_guards_installed = _make_gauge(
    "llm_guards_installed",
    "1 = install_llm_guards() ran for this provider in this process. 0 = NEVER ran (alarm).",
    ("provider", "entrypoint"),
)

# Wave 4 follow-up (2026-05-22) - streaming/tool-use reconciliation delta.
# Counts |actual - estimated| token-eq deltas after each LLM call where
# response.usage was observed. sign=positive when actual > estimated
# (we under-charged, reconciliation tops up); sign=negative when actual <
# estimated (we over-charged, reconciliation refunds). Persistent skew
# in one direction flags estimator drift in _estimate_tokens_*.
llm_gate_reconciliation_delta_total = _make_counter(
    "llm_gate_reconciliation_delta_total",
    "Sum of |actual - estimated| token-eqs from llm gate reconciliation (per provider).",
    ("provider", "sign"),
)

# ----------------------------------------------------------------------
# ADR-WT-2027 BYOK Strategy (Opcao C, 2026-05-22).
# Counter pair tracks BYOK tenant gate behavior:
# - byok_track_only_total: incremented on EVERY gate call where BYOK is
#   active (track-only mode). Compared against ai_credit_gate_calls_total
#   gives the BYOK fraction of overall LLM traffic.
# - byok_soft_cap_breached_total: incremented when BYOK tenant exceeds
#   their self-managed soft cap. ALARM signal (track-only, never blocks).
#   Spike per tenant = tenant should review their cap or LLM call pattern.
# ----------------------------------------------------------------------
byok_track_only_total = _make_counter(
    "byok_track_only_total",
    "Gate calls where BYOK active so enforcement is track-only (no block). "
    "ADR-WT-2027 Opcao C, 2026-05-22.",
    ("service", "provider"),
)

byok_soft_cap_breached_total = _make_counter(
    "byok_soft_cap_breached_total",
    "BYOK tenant breached self-managed soft cap (track-only, NOT blocking). "
    "Alarm signal; alarm rule should fire on rate > baseline. "
    "ADR-WT-2027 Opcao C, 2026-05-22.",
    ("company_id_hash", "service", "provider"),
)

fairness_guard_skip_total = _make_counter(
    "fairness_guard_skip_total",
    "Count of FairnessGuard fail-soft fallbacks (REGRA 4 violation indicator).",
    ("caller_module",),
)

dsr_overdue_created_total = _make_counter(
    "dsr_overdue_created_total",
    "Count of DSR overdue alerts created by dsr.check_overdue_daily cron.",
)

tasks_cross_tenant_blocked_total = _make_counter(
    "tasks_cross_tenant_blocked_total",
    "Count of tasks_repository ValueError (company_id required) -- bug indicator.",
    ("method",),
)

# ----------------------------------------------------------------------
# Hardening C.2 -- PolicyEngineService runtime invocations.
# Alarm: absent(rate(policy_engine_runtime_invocations_total[24h])) > 0
#        => V2 nao esta sendo chamado por 24h (ghost reincidente).
# ----------------------------------------------------------------------
policy_engine_runtime_invocations_total = _make_counter(
    "policy_engine_runtime_invocations_total",
    "Count of PolicyEngineService public method invocations (evaluate / "
    "check_rate_limit / trigger_escalation). Hardening C.2 -- silence "
    "for 24h+ flags ghost reincidente.",
    ("method",),
)

# ----------------------------------------------------------------------
# Hardening C.3 -- LGPD granular consent revoke per purpose.
# Alarm: rate(granular_consent_revoke_per_purpose_total{purpose="X"}[1h])
#        > baseline + 3*stddev => UX issue ou bug em consumer X.
# ----------------------------------------------------------------------
granular_consent_revoke_per_purpose_total = _make_counter(
    "granular_consent_revoke_per_purpose_total",
    "Count of LGPD granular consent revocations per purpose. Hardening C.3 -- "
    "spike sinaliza UX issue ou perda de confianca; spike numa unica "
    "finalidade sinaliza bug em consumer especifico.",
    ("purpose",),
)


# ----------------------------------------------------------------------
# Whitelists para prevenir cardinality explosion via typos.
# Update only when adding a new canonical method/purpose.
# ----------------------------------------------------------------------
_POLICY_ENGINE_METHODS = frozenset({
    "evaluate",
    "check_rate_limit",
    "trigger_escalation",
})

# Espelha GRANULAR_PURPOSE_MAP em app/domains/lgpd/services/granular_consent_service.py.
# Manter sincronizado: adicionar purpose novo aqui ao adicionar la.
_GRANULAR_CONSENT_PURPOSES = frozenset({
    "ai_screening",
    "ai_scoring",
    "ai_video_analysis",
    "ai_comparison",
    "data_retention",
    "marketing",
    "analytics",
    "training_data",
    "ats_sharing",
})


def inc_policy_engine_invocation(method: str) -> None:
    """Incrementa contador de invocacao do PolicyEngineService (fail-open).

    Args:
        method: evaluate | check_rate_limit | trigger_escalation.
                Outros valores sao logged e skipped (cardinality guard).
    """
    if policy_engine_runtime_invocations_total is None:
        return
    if method not in _POLICY_ENGINE_METHODS:
        logger.warning(
            "[canary_metrics] unknown PolicyEngine method=%r (allowed=%s) -- "
            "metric skipped",
            method, sorted(_POLICY_ENGINE_METHODS),
        )
        return
    try:
        policy_engine_runtime_invocations_total.labels(method=method).inc()
    except Exception as exc:  # pragma: no cover -- fail-open
        logger.debug(
            "[canary_metrics] policy_engine inc failed (fail-open): %s", exc
        )


def inc_granular_consent_revoke(purpose: str) -> None:
    """Incrementa contador de revoke LGPD granular (fail-open).

    Args:
        purpose: finalidade canonical (ver _GRANULAR_CONSENT_PURPOSES).
                 Outros valores sao logged e skipped (cardinality guard
                 + LGPD: alta cardinalidade pode vazar PII via labels).
    """
    if granular_consent_revoke_per_purpose_total is None:
        return
    if purpose not in _GRANULAR_CONSENT_PURPOSES:
        logger.warning(
            "[canary_metrics] unknown granular consent purpose=%r "
            "(allowed=%s) -- metric skipped",
            purpose, sorted(_GRANULAR_CONSENT_PURPOSES),
        )
        return
    try:
        granular_consent_revoke_per_purpose_total.labels(purpose=purpose).inc()
    except Exception as exc:  # pragma: no cover -- fail-open
        logger.debug(
            "[canary_metrics] granular_consent_revoke inc failed (fail-open): %s",
            exc,
        )



# Realtime WS voice gate canonical (PLAN_WEBSOCKET_VOICE_GATE 2026-05-22)
# Pair counters track session lifecycle outcomes (started vs terminated reasons)
# + per-direction token consumption.
# Used by app/domains/voice/services/realtime_credit_session.py.
realtime_session_started_total = _make_counter(
    "realtime_session_started_total",
    "Realtime WS sessions started (pre-check passed)",
    ("company_id_hash",),
)

realtime_session_terminated_total = _make_counter(
    "realtime_session_terminated_total",
    "Realtime WS sessions terminated, by reason",
    ("reason",),  # normal|credit_exhausted_pre|credit_exhausted_mid|error|timeout
)

realtime_tokens_consumed_total = _make_counter(
    "realtime_tokens_consumed_total",
    "Realtime tokens consumed, by direction",
    ("direction",),  # input|output
)


# ----------------------------------------------------------------------
# ADR-WT-2025 Sprint D+1 partial -- legacy /alerts/config endpoint
# telemetry (sunset 2026-08-22). Counter increments on every call to
# deprecated GET/PUT /alerts/config. Spike = clients still on legacy
# API; zero before sunset = safe to remove endpoint early.
# ----------------------------------------------------------------------
legacy_alerts_config_endpoint_calls_total = _make_counter(
    "legacy_alerts_config_endpoint_calls_total",
    "Calls to deprecated /alerts/config endpoint (sunset 2026-08-22, "
    "ADR-WT-2025 Sprint D+1). Spike near sunset = clients still on "
    "legacy; zero pre-sunset = safe to remove endpoint early.",
    ("method", "company_id_hash"),
)

# ----------------------------------------------------------------------
# ADR-WT-2025 Sprint D+1 partial -- briefing dispatch legacy AlertConfig
# read counter (fallback path). Counter increments whenever briefing
# dispatch falls back to AlertConfig.briefing_frequency because
# HiringPolicy.communication_rules.briefing_frequency is missing for
# the tenant. Spike = tenants not backfilled by migration 174 OR
# new tenants without briefing config. Drives Sprint D+1 final timing
# (when this counter hits 0 sustained pre-sunset, safe to remove the
# fallback path early).
# ----------------------------------------------------------------------
briefing_dispatch_legacy_alertconfig_read_total = _make_counter(
    "briefing_dispatch_legacy_alertconfig_read_total",
    "briefing_dispatch falls back to legacy alert_configs.briefing_frequency "
    "because HiringPolicy.communication_rules.briefing_frequency missing. "
    "ADR-WT-2025 Sprint D+1 partial -- spike = un-backfilled tenants.",
    ("company_id_hash",),
)



# ----------------------------------------------------------------------
# Task 3.A (2026-05-25) -- Briefing generation observability.
# Counter tracks outcomes (success/error); histogram tracks latency.
# Labels use company_id_hash (SHA-256[:12]) per cardinality convention.
# Used by app/api/v1/briefing.py.
# Alarm rules:
#   - rate(briefing_generated_total{outcome="error"}[5m]) / rate(briefing_generated_total[5m]) > 0.1
#     => briefing error rate > 10% (oncall)
#   - histogram_quantile(0.95, rate(briefing_generation_duration_seconds_bucket[5m])) > 10
#     => P95 > 10s (SLO breach)
# ----------------------------------------------------------------------
briefing_generated_total = _make_counter(
    "briefing_generated_total",
    "Count of daily briefing generation attempts, by outcome. "
    "Task 3.A observability sensor (2026-05-25).",
    ("company_id_hash", "outcome"),   # outcome: success | error | empty_user
)

# Buckets in seconds: sub-second to 60s (briefing is DB-heavy + optional LLM).
_BRIEFING_LATENCY_BUCKETS = (0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0)

briefing_generation_duration_seconds = _make_histogram(
    "briefing_generation_duration_seconds",
    "Latency of generate_daily_briefing() in seconds. "
    "Task 3.A observability sensor (2026-05-25). "
    "SLO: P95 < 10s.",
    ("company_id_hash",),
    buckets=_BRIEFING_LATENCY_BUCKETS,
)


def inc_briefing_generated(company_id: str, outcome: str) -> None:
    """Incrementa briefing_generated_total (fail-open).

    Args:
        company_id: tenant ID para hash (nunca raw como label).
        outcome: success | error | empty_user
    """
    if briefing_generated_total is None:
        return
    try:
        h = hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:12] if company_id else "unknown"
        briefing_generated_total.labels(company_id_hash=h, outcome=outcome).inc()
    except Exception:  # pragma: no cover -- fail-open
        pass


def obs_briefing_duration(company_id: str, duration_seconds: float) -> None:
    """Observa latencia de geracao de briefing (fail-open).

    Args:
        company_id: tenant ID para hash.
        duration_seconds: tempo total em segundos.
    """
    if briefing_generation_duration_seconds is None:
        return
    try:
        h = hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:12] if company_id else "unknown"
        briefing_generation_duration_seconds.labels(company_id_hash=h).observe(duration_seconds)
    except Exception:  # pragma: no cover -- fail-open
        pass

__all__ = (
    "ai_credit_exhausted_total",
    "ai_credit_gate_calls_total",
    "llm_guards_installed",
    "llm_gate_reconciliation_delta_total",
    "byok_track_only_total",
    "byok_soft_cap_breached_total",
    "fairness_guard_skip_total",
    "dsr_overdue_created_total",
    "tasks_cross_tenant_blocked_total",
    "policy_engine_runtime_invocations_total",
    "granular_consent_revoke_per_purpose_total",
    "inc_policy_engine_invocation",
    "inc_granular_consent_revoke",
    "realtime_session_started_total",
    "realtime_session_terminated_total",
    "realtime_tokens_consumed_total",
    "legacy_alerts_config_endpoint_calls_total",
    "briefing_dispatch_legacy_alertconfig_read_total",
    "briefing_generated_total",
    "briefing_generation_duration_seconds",
    "inc_briefing_generated",
    "obs_briefing_duration",
)


# W4-041 (2026-05-23): Tier 6 canary gate observability.
# Spike em invocations + flag_state=off = users sendo gated out (canary working).
# Spike em flag_state=on com baixa hit rate downstream = Tier 6 underperforming.
tier6_invocations_total = _make_counter(
    "tier6_invocations_total",
    "Count of Tier 6 (AutonomousReActAgent) gate evaluations in CascadedRouter.",
    ("company_id_hash", "flag_state"),
)


# Sprint 12.3-A (2026-05-24): Phase 2 V1 fallback canary observability.
# Tracks invocations of legacy Orchestrator.process_request (Phase 2 V1 fallback).
# Goal: drive count to near-zero post Sprint 12 refactor (Phase 1.5 absorption).
# Flag state semantics:
#   - "enabled" = LIA_PHASE_2_V1_ENABLED=true (or unset = default-on backward compat)
#   - "disabled" = LIA_PHASE_2_V1_ENABLED=false (kill-switch, returns canonical fail-loud)
# Spike em flag_state=disabled = users hitting kill-switch (Sprint 12 cutover signal).
# Spike em flag_state=enabled with high latency = V1 still hot path (refactor pending).
phase_2_v1_invocations_total = _make_counter(
    "phase_2_v1_invocations_total",
    "Count of Phase 2 V1 fallback (legacy Orchestrator.process_request) invocations.",
    ("company_id_hash", "flag_state"),
)
