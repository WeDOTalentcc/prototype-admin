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
- caller_module -- str do __name__ do modulo que emitiu (helps debug
  qual callsite esta em fail-soft).
- method -- str do metodo de repository que levantou (granularidade
  pra alarme).
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
    ("company_id_hash",),
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


__all__ = (
    "ai_credit_exhausted_total",
    "fairness_guard_skip_total",
    "dsr_overdue_created_total",
    "tasks_cross_tenant_blocked_total",
)
