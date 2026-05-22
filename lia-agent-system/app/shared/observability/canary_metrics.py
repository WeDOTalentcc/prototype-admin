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
except Exception:  # pragma: no cover -- prometheus opcional em dev
    _PROM_REGISTRY = None  # type: ignore[assignment]
    _PromCounter = None  # type: ignore[assignment]


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


__all__ = (
    "ai_credit_exhausted_total",
    "fairness_guard_skip_total",
    "dsr_overdue_created_total",
    "tasks_cross_tenant_blocked_total",
    "policy_engine_runtime_invocations_total",
    "granular_consent_revoke_per_purpose_total",
    "inc_policy_engine_invocation",
    "inc_granular_consent_revoke",
)
