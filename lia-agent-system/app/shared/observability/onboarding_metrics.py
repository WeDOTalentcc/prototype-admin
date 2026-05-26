"""onboarding_metrics.py — P2-2 Sprint C foundation telemetry.

Prometheus counters/histograms canonical pra medir adocao + qualidade
do onboarding LIA conversacional.

Pattern alinhado com canary_metrics.py (Sprint 2.2 observability — memory).

NUNCA usar PII (user_id, company_name) como label — apenas hashed_company_id
(quando precisar correlacionar) ou nenhum label.

Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint C
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Defensive import — Prometheus pode nao estar configurado em todos ambientes
try:
    from prometheus_client import Counter, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed — onboarding metrics inert")
    # Stubs no-op
    class Counter:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def inc(self, value: float = 1): pass
        def collect(self): return []
    class Histogram:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def observe(self, value: float): pass
        def collect(self): return []


def _safe_counter(name: str, doc: str, labelnames: list[str] | None = None):
    """Build counter, reuse if already registered (defensive against double-import)."""
    try:
        if labelnames:
            return Counter(name, doc, labelnames=labelnames)
        return Counter(name, doc)
    except ValueError:
        # Already registered — fetch from default registry
        try:
            from prometheus_client import REGISTRY
            for collector in list(REGISTRY._collector_to_names.keys()):
                if getattr(collector, "_name", None) == name:
                    return collector
        except Exception:
            pass
        # Fallback no-op
        return Counter.__new__(Counter)


def _safe_histogram(name: str, doc: str, buckets: tuple):
    try:
        return Histogram(name, doc, buckets=buckets)
    except ValueError:
        try:
            from prometheus_client import REGISTRY
            for collector in list(REGISTRY._collector_to_names.keys()):
                if getattr(collector, "_name", None) == name:
                    return collector
        except Exception:
            pass
        return Histogram.__new__(Histogram)


# Counters
onboarding_chat_started_total = _safe_counter(
    "onboarding_chat_started_total",
    "Total de sessoes de onboarding conversacional iniciadas",
)

onboarding_chat_completed_total = _safe_counter(
    "onboarding_chat_completed_total",
    "Total de sessoes que atingiram threshold (>= 80%% setup)",
)

onboarding_chat_abandoned_total = _safe_counter(
    "onboarding_chat_abandoned_total",
    "Total de sessoes onde usuario parou < threshold",
    labelnames=["progress_bucket"],
)

onboarding_field_extracted_total = _safe_counter(
    "onboarding_field_extracted_total",
    "Total de campos extraidos com sucesso por field_key",
    labelnames=["field_key"],
)

onboarding_field_skipped_total = _safe_counter(
    "onboarding_field_skipped_total",
    "Total de campos pulados (skip phrase) por field_key",
    labelnames=["field_key"],
)

onboarding_field_validation_failed_total = _safe_counter(
    "onboarding_field_validation_failed_total",
    "Total de validation failures por field_key + rule",
    labelnames=["field_key", "validation_rule"],
)

# Histograms
onboarding_extraction_confidence = _safe_histogram(
    "onboarding_extraction_confidence",
    "Distribuicao de confidence scores das extracoes LLM (0-1)",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0),
)

onboarding_extraction_duration_seconds = _safe_histogram(
    "onboarding_extraction_duration_seconds",
    "Latencia de extracao por field (LLM + validation)",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0),
)


def hash_company_id(company_id: str) -> str:
    """Hash canonical pra company_id em metrics (cardinality control + LGPD)."""
    return hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:12]


def progress_bucket(progress: int) -> str:
    """Bucketize progress para abandon counter."""
    if progress < 25:
        return "0-25"
    elif progress < 50:
        return "25-50"
    else:
        return "50-80"


# Helpers convenience
def record_chat_started() -> None:
    """Quando session inicia phase SETTINGS_EXTRACTION."""
    onboarding_chat_started_total.inc()


def record_chat_completed() -> None:
    """Quando is_complete=True (>=80% threshold)."""
    onboarding_chat_completed_total.inc()


def record_chat_abandoned(progress: int) -> None:
    """Quando usuario para sem completar (stop phrase OR session expira)."""
    onboarding_chat_abandoned_total.labels(
        progress_bucket=progress_bucket(progress)
    ).inc()


def record_field_extracted(field_key: str, confidence: float) -> None:
    """Por campo extraido com sucesso."""
    onboarding_field_extracted_total.labels(field_key=field_key).inc()
    onboarding_extraction_confidence.observe(confidence)


def record_field_skipped(field_key: str) -> None:
    """Por campo pulado (skip phrase)."""
    onboarding_field_skipped_total.labels(field_key=field_key).inc()


def record_field_validation_failed(field_key: str, validation_rule: str) -> None:
    """Quando validation falha em extracted_value."""
    onboarding_field_validation_failed_total.labels(
        field_key=field_key,
        validation_rule=validation_rule or "unknown",
    ).inc()


def record_extraction_duration(duration_seconds: float) -> None:
    """Latencia da extracao (incluir LLM call + validation)."""
    onboarding_extraction_duration_seconds.observe(duration_seconds)
