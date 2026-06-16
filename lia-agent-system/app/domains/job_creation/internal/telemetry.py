"""telemetry canonical — PR-17 step 5 extract (2026-05-26 ONDA 3 follow-up).

Wizard observability helpers movidos de graph.py:
- _emit_fallback_telemetry (Task #1070 — fallback tracker get/record)
- _emit_wizard_fallback_metric (Task #1068 — structured log + Sentry + Prometheus)

Ambos fail-open: telemetria nunca quebra o wizard.
"""

import logging
from typing import Any, Dict, Optional

from app.domains.job_creation.internal.constants import _WIZARD_FALLBACK_NODES

logger = logging.getLogger(__name__)


def _emit_fallback_telemetry(
    state: dict, stage: str, reason):
    """Task #1070 — registra um evento de fallback no tracker e devolve o
    snapshot ai_degraded_mode (sessão ou tenant) para ser propagado pelo
    ws_stage_payload. Quando o threshold é cruzado, o tracker emite log
    estruturado + sentry_sdk.capture_message para o time de plataforma.

    Sempre invoca get_state para que stages que não caíram em fallback
    no turno atual ainda surfacem o aviso enquanto a janela está ativa.
    """
    try:
        from app.shared.observability.wizard_fallback_tracker import (
            get_wizard_fallback_tracker,
        )

        sid = (
            str(state.get("session_id") or state.get("thread_id") or "")
            or None
        )
        cid = (
            str(state.get("workspace_id") or state.get("company_id") or "")
            or None
        )
        tracker = get_wizard_fallback_tracker()
        if reason:
            tracker.record_fallback(
                session_id=sid, company_id=cid, stage=stage, reason=reason,
            )
        return tracker.get_state(session_id=sid, company_id=cid)
    except Exception as exc:  # noqa: BLE001 — telemetria nunca quebra o wizard
        logger.warning(
            "[JobCreation:%s] wizard fallback tracker failed: %s", stage, exc,
        )
        return None


def _emit_wizard_fallback_metric(
    *,
    node: str,
    state: dict,
    reason: str,
    timeout_s: Optional[float] = None,
    elapsed_ms: Optional[float] = None,
) -> None:
    """Emit observability signal when a wizard node falls back.

    Args:
        node: One of `_WIZARD_FALLBACK_NODES`.
        state: LangGraph state — used to extract tenant id (workspace_id /
            company_id) and session id without leaking PII.
        reason: Short machine token, e.g. `"llm_timeout"`, `"llm_exception"`,
            `"benchmark_timeout"`. Becomes a Sentry tag — keep it low-cardinality.
        timeout_s: Configured timeout (when applicable) so dashboards can
            justify raising it.
        elapsed_ms: Wall-clock spent before the fallback fired (when known).
    """
    try:
        if node not in _WIZARD_FALLBACK_NODES:
            # Prevent silent taxonomy drift — a typo here would split the
            # dashboard into two buckets and hide the regression.
            logger.warning(
                "[JobCreation] _emit_wizard_fallback_metric got unknown node=%r "
                "(allowed=%s) — telemetry skipped",
                node, _WIZARD_FALLBACK_NODES,
            )
            return
        tenant_id = str(
            state.get("workspace_id") or state.get("company_id") or ""
        ) or "unknown"
        session_id = str(state.get("session_id") or "") or None
        job_id = state.get("job_id")

        # ── 1. Structured log (picked up by JSONFormatter) ──
        extra: Dict[str, Any] = {
            "extra_data": {
                "metric": "wizard_fallback",
                "node": node,
                "tenant_id": tenant_id,
                "reason": reason,
                "timeout_s": timeout_s,
                "elapsed_ms": elapsed_ms,
                "session_id": session_id,
                "job_id": str(job_id) if job_id else None,
            },
            "tenant_id": tenant_id,
        }
        logger.warning(
            "[JobCreation:%s] wizard fallback fired (reason=%s)",
            node, reason, extra=extra,
        )

        # REGRA 4 sensor — Prometheus counter for Grafana alarm.
        # inc_wizard_fallback is fail-open + cardinality-bounded.
        try:
            from app.shared.observability.fallback_metrics import (
                inc_wizard_fallback,
            )
            inc_wizard_fallback(node, reason)
        except Exception as _counter_exc:  # noqa: BLE001 — fail-open
            logger.debug(
                "[JobCreation:%s] wizard fallback counter inc failed: %s",
                node, _counter_exc,
            )

        # ── 2. Sentry breadcrumb + capture_message ──
        try:
            import sentry_sdk as _sentry  # noqa: WPS433 — lazy import
        except Exception:  # noqa: BLE001 — sentry optional
            return
        try:
            _sentry.add_breadcrumb(
                category="wizard.fallback",
                level="warning",
                message=f"wizard:{node} fallback ({reason})",
                data={
                    "node": node,
                    "reason": reason,
                    "tenant_id": tenant_id,
                    "timeout_s": timeout_s,
                    "elapsed_ms": elapsed_ms,
                },
            )
            with _sentry.push_scope() as _scope:
                _scope.set_tag("wizard.node", node)
                _scope.set_tag("wizard.fallback_reason", reason)
                _scope.set_tag("tenant_id", tenant_id)
                _scope.set_extra("timeout_s", timeout_s)
                _scope.set_extra("elapsed_ms", elapsed_ms)
                _scope.set_extra("session_id", session_id)
                _sentry.capture_message(
                    f"wizard fallback: {node} ({reason})",
                    level="warning",
                )
        except Exception as _sentry_exc:  # noqa: BLE001 — fail-open
            logger.debug(
                "[JobCreation:%s] sentry capture failed (fail-open): %s",
                node, _sentry_exc,
            )
    except Exception as _metric_exc:  # noqa: BLE001 — fail-open
        logger.debug(
            "[JobCreation:%s] wizard fallback metric emit failed (fail-open): %s",
            node, _metric_exc,
        )
