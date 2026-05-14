"""
Task #1070 — agrega ``*_fallback_reason`` por sessão de wizard e por tenant
para detectar quando o provedor de LLM está degradado, e não apenas ruído
pontual em uma única chamada.

Fonte dos eventos: ``app.domains.job_creation.graph`` chama
:func:`get_wizard_fallback_tracker().record_fallback` toda vez que um nó cai
no fallback determinístico (timeout / provider_error / exception). O tracker
mantém duas janelas deslizantes em memória do processo:

- por ``session_id`` do wizard (default: 30 min, threshold 3 fallbacks)
- por ``company_id`` (default: 60 min, threshold 5 fallbacks)

Quando algum threshold é cruzado, ``record_fallback`` devolve um snapshot
``ai_degraded_mode`` que ``ws_stage_payload`` propaga ao frontend, e emite
um aviso warning no log estruturado + ``sentry_sdk.capture_message`` para o
time de plataforma. Há cooldown de 5 min entre alertas para o mesmo escopo
para evitar storm.

Limitação conhecida: o tracker é per-process. Em deployments multi-worker,
o threshold por tenant pode disparar tarde (cada worker precisa observar
≥N fallbacks individualmente). A migração para Redis sliding window pode
ser feita depois sem mudar a interface pública (``record_fallback`` /
``get_state`` / ``reset``).
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


SESSION_WINDOW_S = _env_int("LIA_WIZARD_FALLBACK_SESSION_WINDOW_S", 1800)
SESSION_THRESHOLD = _env_int("LIA_WIZARD_FALLBACK_SESSION_THRESHOLD", 3)
TENANT_WINDOW_S = _env_int("LIA_WIZARD_FALLBACK_TENANT_WINDOW_S", 3600)
TENANT_THRESHOLD = _env_int("LIA_WIZARD_FALLBACK_TENANT_THRESHOLD", 5)
ALERT_COOLDOWN_S = _env_int("LIA_WIZARD_FALLBACK_ALERT_COOLDOWN_S", 300)


@dataclass
class _Event:
    ts: float
    stage: str
    reason: str


@dataclass
class _Window:
    events: Deque[_Event] = field(default_factory=deque)
    last_alert_ts: float = 0.0


class WizardFallbackTracker:
    """In-memory aggregator of wizard fallback events per session and tenant."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: Dict[str, _Window] = {}
        self._tenants: Dict[str, _Window] = {}

    @staticmethod
    def _prune(window: _Window, max_age_s: int, now: float) -> None:
        cutoff = now - max_age_s
        while window.events and window.events[0].ts < cutoff:
            window.events.popleft()

    @staticmethod
    def _snapshot(window: _Window, scope: str, threshold: int, window_s: int) -> Dict[str, Any]:
        breakdown: Dict[str, int] = {}
        for ev in window.events:
            breakdown[ev.reason] = breakdown.get(ev.reason, 0) + 1
        since_ts = window.events[0].ts
        return {
            "active": True,
            "scope": scope,
            "count": sum(breakdown.values()),
            "threshold": threshold,
            "window_seconds": window_s,
            "since": datetime.fromtimestamp(since_ts, tz=timezone.utc).isoformat(),
            "reason_breakdown": breakdown,
        }

    def record_fallback(
        self,
        *,
        session_id: Optional[str],
        company_id: Optional[str],
        stage: str,
        reason: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Record a fallback event; return ai_degraded_mode snapshot if active."""
        if not reason:
            return None
        now = time.time()
        ev = _Event(ts=now, stage=stage, reason=reason)

        with self._lock:
            session_active = False
            tenant_active = False

            if session_id:
                w = self._sessions.setdefault(session_id, _Window())
                self._prune(w, SESSION_WINDOW_S, now)
                w.events.append(ev)
                session_active = len(w.events) >= SESSION_THRESHOLD

            if company_id:
                tw = self._tenants.setdefault(company_id, _Window())
                self._prune(tw, TENANT_WINDOW_S, now)
                tw.events.append(ev)
                tenant_active = len(tw.events) >= TENANT_THRESHOLD

            scope: Optional[str] = None
            chosen_window: Optional[_Window] = None
            chosen_threshold = 0
            chosen_window_s = 0
            if session_active and session_id:
                scope = "session"
                chosen_window = self._sessions[session_id]
                chosen_threshold = SESSION_THRESHOLD
                chosen_window_s = SESSION_WINDOW_S
            elif tenant_active and company_id:
                scope = "tenant"
                chosen_window = self._tenants[company_id]
                chosen_threshold = TENANT_THRESHOLD
                chosen_window_s = TENANT_WINDOW_S

            if scope is None or chosen_window is None:
                return None

            should_alert = (now - chosen_window.last_alert_ts) > ALERT_COOLDOWN_S
            if should_alert:
                chosen_window.last_alert_ts = now
            snapshot = self._snapshot(chosen_window, scope, chosen_threshold, chosen_window_s)

        if should_alert:
            self._emit_alert(
                scope=scope,
                session_id=session_id,
                company_id=company_id,
                snapshot=snapshot,
            )
        return snapshot

    def get_state(
        self,
        *,
        session_id: Optional[str],
        company_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Return the current degraded-mode snapshot (session takes priority)."""
        now = time.time()
        with self._lock:
            for scope, key, store, window_s, threshold in (
                ("session", session_id, self._sessions, SESSION_WINDOW_S, SESSION_THRESHOLD),
                ("tenant", company_id, self._tenants, TENANT_WINDOW_S, TENANT_THRESHOLD),
            ):
                if not key:
                    continue
                w = store.get(key)
                if not w:
                    continue
                self._prune(w, window_s, now)
                if len(w.events) >= threshold:
                    return self._snapshot(w, scope, threshold, window_s)
        return None

    def reset(self) -> None:
        """Test helper — clears all state."""
        with self._lock:
            self._sessions.clear()
            self._tenants.clear()

    def _emit_alert(
        self,
        *,
        scope: str,
        session_id: Optional[str],
        company_id: Optional[str],
        snapshot: Dict[str, Any],
    ) -> None:
        log_extra = {
            "scope": scope,
            "session_id": session_id,
            "company_id": company_id,
            "count": snapshot["count"],
            "threshold": snapshot["threshold"],
            "window_seconds": snapshot["window_seconds"],
            "reason_breakdown": snapshot["reason_breakdown"],
        }
        logger.warning(
            "[WizardFallbackTracker] AI degraded mode triggered scope=%s "
            "count=%s threshold=%s reasons=%s session=%s company=%s",
            scope,
            snapshot["count"],
            snapshot["threshold"],
            snapshot["reason_breakdown"],
            session_id,
            company_id,
        )
        try:  # pragma: no cover — Sentry is optional in test env
            import sentry_sdk

            sentry_sdk.capture_message(
                f"Wizard AI degraded mode ({scope})",
                level="warning",
                extras=log_extra,
            )
        except Exception:
            pass


_tracker_singleton: Optional[WizardFallbackTracker] = None
_singleton_lock = threading.Lock()


def get_wizard_fallback_tracker() -> WizardFallbackTracker:
    """Return the process-wide WizardFallbackTracker singleton."""
    global _tracker_singleton
    if _tracker_singleton is None:
        with _singleton_lock:
            if _tracker_singleton is None:
                _tracker_singleton = WizardFallbackTracker()
    return _tracker_singleton
