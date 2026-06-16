"""
Span attribute validation helper — N-08 follow-up.

Provides:
  * `validate_span_attributes(span, required, *, forbidden)` — pure function
    used by CI gates and unit tests to confirm every wizard/orchestrator span
    carries the mandatory tenant/user/conversation tags AND is free of any
    LGPD-protected attribute name.
  * `wizard_traced_node(span_name)` — decorator applied to sync LangGraph
    nodes inside `JobCreationGraph`. It opens a span, copies the canonical
    tenant context out of the wizard state, and finishes the span with the
    correct status — without changing the node's return value.

Both helpers reuse the canonical constants from
`app.orchestrator._observability` so we have a single source of truth for
which span attributes are required (and which are forbidden under LGPD).

Reference: ADR-019 §Promotion Gate #8, task #861 (closes N-07 + N-08).
"""

from __future__ import annotations

import functools
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from app.shared.observability.tracing import finish_span, get_tracer

# ─────────────────────────────────────────────────────────────────────────────
# N-14 (Audit Rev 4) — `wizard_node_latency_seconds` OTLP histogram
# Lazy-singleton to keep the import boundary cheap (matches the rationale in
# the module-header NOTE). On first call, attempt to create a real OTLP
# histogram; if the OTel SDK is missing or no provider is configured we
# fall back to a no-op stub so the decorator stays side-effect-free in
# unit tests that do not boot the metrics pipeline.
# ─────────────────────────────────────────────────────────────────────────────
_WIZARD_NODE_LATENCY_HIST: Any = None
# Histogram-bucket boundaries chosen to match Production Readiness Gate #14
# (P95 < 5s) — finer resolution below 1s, coarser above 5s.
_WIZARD_LATENCY_BUCKETS_MS: tuple[float, ...] = (
    25, 50, 100, 250, 500, 1000, 2500, 5000, 10_000, 30_000,
)


class _NoopHistogram:
    """Fallback histogram used when OpenTelemetry metrics is not wired."""

    def record(self, value: float, attributes: Mapping[str, Any] | None = None) -> None:  # noqa: D401
        return None


def _get_wizard_node_latency_histogram() -> Any:
    """Return the wizard node latency histogram (singleton)."""
    global _WIZARD_NODE_LATENCY_HIST
    if _WIZARD_NODE_LATENCY_HIST is not None:
        return _WIZARD_NODE_LATENCY_HIST
    try:
        from opentelemetry import metrics as _otel_metrics

        meter = _otel_metrics.get_meter("lia.wizard")
        _WIZARD_NODE_LATENCY_HIST = meter.create_histogram(
            name="wizard_node_latency_seconds",
            unit="s",
            description=(
                "Latency of each JobCreationGraph node "
                "(Rev 4 N-14, Production Readiness Gate #14)"
            ),
        )
    except Exception:  # pragma: no cover — defensive: OTel optional in tests
        _WIZARD_NODE_LATENCY_HIST = _NoopHistogram()
    return _WIZARD_NODE_LATENCY_HIST


def _reset_wizard_node_latency_histogram_for_tests() -> None:
    """Test-only helper: reset the lazy singleton so a test can inject a fake."""
    global _WIZARD_NODE_LATENCY_HIST
    _WIZARD_NODE_LATENCY_HIST = None

# NOTE on import boundary: we deliberately DO NOT import the constants from
# `app.orchestrator._observability` because that triggers the orchestrator
# package `__init__` (40+s cascade including JobCreationDomain). Instead we
# inline the canonical lists here — the orchestrator module re-exports our
# values to keep a single source of truth at the call sites.
REQUIRED_SPAN_ATTRS: tuple[str, ...] = (
    "tenant.company_id",
    "user.id",
    "conversation.id",
    "orchestrator.version",
)

FORBIDDEN_SPAN_ATTR_PATTERNS: tuple[str, ...] = (
    "race", "raca",
    "religion", "religiao",
    "gender", "genero",
    "ethnicity", "etnia",
    "marital_status", "estado_civil",
    "health", "saude",
    "sexual_orientation", "orientacao_sexual",
    "raw_message",  # full message body must NOT go to spans (use audit_service)
    "prompt_content",
)

logger = logging.getLogger(__name__)

__all__ = [
    "SpanValidationResult",
    "validate_span_attributes",
    "wizard_traced_node",
    "WIZARD_REQUIRED_SPAN_ATTRS",
]

# Required attributes for every wizard span. We extend the canonical
# orchestrator list with `wizard.stage` so dashboards can break-down by stage.
WIZARD_REQUIRED_SPAN_ATTRS: tuple[str, ...] = REQUIRED_SPAN_ATTRS + ("wizard.stage",)

_TOKEN_SPLIT_RE = re.compile(r"[._\-/\s]+")
_FORBIDDEN_LOWER = {p.lower() for p in FORBIDDEN_SPAN_ATTR_PATTERNS}

# Sentinel values that count as "missing" even when the attribute key exists.
# A span carrying `tenant.company_id="0"` is just as broken as one missing the
# key — the attribute is supposed to identify a real tenant.
_EMPTY_VALUES: frozenset = frozenset(["", "0", "None", "none", "null", "0.0"])


@dataclass
class SpanValidationResult:
    """Outcome of validating a span's attributes."""

    span_name: str
    is_valid: bool
    missing: list[str] = field(default_factory=list)
    empty: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)

    def reason(self) -> str:
        """Human-readable reason — used by CI assertions."""
        parts: list[str] = []
        if self.missing:
            parts.append(f"missing={self.missing}")
        if self.empty:
            parts.append(f"empty={self.empty}")
        if self.forbidden:
            parts.append(f"forbidden={self.forbidden}")
        return f"span={self.span_name!r} " + (" ".join(parts) or "ok")


def _coerce_attributes(span: Any) -> tuple[str, Mapping[str, Any]]:
    """Extract `(name, attributes)` from a Span / dict / mapping.

    Accepts:
      * `LightweightTracer.Span` (has `.name` + `.attributes`)
      * Any object with `.name` + `.attributes`
      * A plain mapping where `name` lives under `"name"` key
      * A bare attribute mapping (name defaults to `"<unknown>"`)
    """
    if hasattr(span, "attributes") and hasattr(span, "name"):
        return str(span.name), dict(span.attributes or {})
    if isinstance(span, Mapping):
        attrs = span.get("attributes") if "attributes" in span else span
        name = span.get("name", "<unknown>") if "name" in span else "<unknown>"
        return str(name), dict(attrs or {})
    raise TypeError(
        f"validate_span_attributes: unsupported span type {type(span).__name__}; "
        "expected Span, mapping, or object with .attributes"
    )


def _value_is_empty(value: Any) -> bool:
    """Return True if `value` should count as missing for tenant/user attrs."""
    if value is None:
        return True
    if isinstance(value, (int, float)):
        return value == 0
    text = str(value).strip()
    return text == "" or text in _EMPTY_VALUES


def _attr_key_is_forbidden(key: str) -> str | None:
    """If `key` matches a LGPD-forbidden pattern, return the matched token."""
    tokens = {t for t in _TOKEN_SPLIT_RE.split(key.lower()) if t}
    for forbidden in _FORBIDDEN_LOWER:
        if forbidden in tokens:
            return forbidden
    return None


def validate_span_attributes(
    span: Any,
    required: Sequence[str] = WIZARD_REQUIRED_SPAN_ATTRS,
    *,
    forbidden: Sequence[str] = FORBIDDEN_SPAN_ATTR_PATTERNS,
    raise_on_missing: bool = False,
) -> SpanValidationResult:
    """Validate a single span's attributes.

    Args:
        span: A `Span`, mapping, or attributes dict to inspect.
        required: Attribute names that MUST be present and non-empty.
        forbidden: Attribute name tokens that MUST NEVER appear (LGPD).
        raise_on_missing: If True, raise `ValueError` instead of returning
            an invalid result. Useful for CI gates that want immediate failure.

    Returns:
        `SpanValidationResult` with `is_valid=True` only when no required
        attribute is missing/empty AND no forbidden attribute is present.
    """
    name, attributes = _coerce_attributes(span)

    # Bind the local forbidden set so callers can override it for tests
    # without affecting the module-level cache used by the wizard decorator.
    forbidden_lower = {p.lower() for p in forbidden}

    missing: list[str] = []
    empty: list[str] = []
    for key in required:
        if key not in attributes:
            missing.append(key)
            continue
        if _value_is_empty(attributes[key]):
            empty.append(key)

    forbidden_hits: list[str] = []
    if forbidden_lower:
        for key in attributes.keys():
            tokens = {t for t in _TOKEN_SPLIT_RE.split(str(key).lower()) if t}
            if tokens & forbidden_lower:
                forbidden_hits.append(key)

    is_valid = not missing and not empty and not forbidden_hits
    result = SpanValidationResult(
        span_name=name,
        is_valid=is_valid,
        missing=missing,
        empty=empty,
        forbidden=forbidden_hits,
    )

    if not is_valid and raise_on_missing:
        raise ValueError(
            f"Span attribute validation failed: {result.reason()}"
        )
    return result


# ---------------------------------------------------------------------------
# Wizard graph node decorator
# ---------------------------------------------------------------------------

def _stage_from_span_name(span_name: str) -> str:
    """`wizard.job_creation.intake` -> `intake`."""
    return span_name.rsplit(".", 1)[-1] if "." in span_name else span_name


def _attrs_from_state(state: Mapping[str, Any], stage: str) -> dict[str, Any]:
    """Extract canonical span attributes from a wizard state dict.

    Wizard state stores `workspace_id` for the tenant (Rails calls it
    "workspace", Postgres calls it "company") — both names map to the same
    isolation boundary. We coerce to `str` because OTel attributes are
    represented as strings by the lightweight tracer + the OTLP exporter.
    """
    return {
        "service.name": "wizard",
        "wizard.graph": "job_creation",
        "wizard.stage": str(state.get("current_stage") or stage or ""),
        "tenant.company_id": str(
            state.get("workspace_id")
            or state.get("company_id")
            or ""
        ),
        "user.id": str(
            state.get("user_id")
            or state.get("recruiter_id")
            or ""
        ),
        "conversation.id": str(state.get("session_id") or ""),
        "orchestrator.version": "wizard",
    }


def wizard_traced_node(span_name: str) -> Callable:
    """Decorator that emits an OTLP span around a sync wizard graph node.

    The decorated function MUST take `state: dict` as its first positional
    argument (LangGraph contract). The decorator:

      1. Opens a span named `span_name` BEFORE calling the node so even a
         crash in the node is captured.
      2. Pulls `tenant.company_id`, `user.id`, `conversation.id`, etc. from
         the state and attaches them as span attributes.
      3. Marks the span as `error` if the node raises, `ok` otherwise.
      4. Returns the node's return value unchanged — pure [sensor] wrapper.
    """
    if not span_name:
        raise ValueError("wizard_traced_node requires a non-empty span_name")
    stage = _stage_from_span_name(span_name)

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(state: Mapping[str, Any], *args, **kwargs):
            tracer = get_tracer()
            attrs = _attrs_from_state(state or {}, stage)
            span = tracer.create_span(span_name, attributes=attrs, _start_otel=True)
            # N-14 (Rev 4): also record per-node latency in a histogram so
            # dashboards can break-down P50/P95/P99 by node without parsing
            # spans. Histogram emits even on error so a regressing node
            # shows up in alerts.
            histogram = _get_wizard_node_latency_histogram()
            t0 = time.perf_counter()
            metric_attrs: dict[str, Any] = {
                "node": stage,
                "wizard.stage": stage,
                "tenant.company_id": str(attrs.get("tenant.company_id", "")),
            }
            try:
                result = fn(state, *args, **kwargs)
            except Exception as exc:
                elapsed = time.perf_counter() - t0
                try:
                    histogram.record(elapsed, attributes={**metric_attrs, "status": "error"})
                except Exception:  # pragma: no cover — never break the node on telemetry
                    pass
                finish_span(span, status="error", error=exc)
                raise
            elapsed = time.perf_counter() - t0
            # Refresh attrs from the result state so spans reflect the value
            # the node actually wrote (e.g. `current_stage` may change).
            try:
                if isinstance(result, Mapping):
                    refreshed = _attrs_from_state(result, stage)
                    for key, value in refreshed.items():
                        span.set_attribute(key, value)
            except Exception:  # pragma: no cover — defensive
                pass
            try:
                histogram.record(elapsed, attributes={**metric_attrs, "status": "ok"})
            except Exception:  # pragma: no cover
                pass
            finish_span(span, status="ok")
            return result

        return wrapper

    return decorator
