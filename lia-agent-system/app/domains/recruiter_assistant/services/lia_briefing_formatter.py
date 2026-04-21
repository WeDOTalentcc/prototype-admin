"""Onda 2.3 Init IV (2026-04-21) — LIA Briefing Formatter.

Consumes briefing_service.generate_daily_briefing output and formats a
compact greeting-friendly summary. Cached with TTL to avoid DB thrash.

Integration path: SystemPromptBuilder or orchestrator greeting hook calls
`get_cached_briefing(user_id, company_id)` on greeting intents; if non-empty,
renders into the `## Saudação Inicial` section context.

Canonical-fix: briefing_service is the single producer for briefing data.
This module only formats + caches — no independent DB access.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# Feature flag — default ON
_PROACTIVE_AGENDA_ENABLED = os.environ.get(
    "LIA_PROACTIVE_AGENDA_ENABLED", "true"
).lower() == "true"

# In-memory TTL cache: {(user_id, company_id): (briefing_dict, expires_at)}
_CACHE: dict[tuple[str, str], tuple[dict, float]] = {}
_DEFAULT_TTL_S = 300  # 5 minutes


def format_briefing_for_greeting(briefing: dict[str, Any] | None) -> str:
    """Format a briefing dict as a compact 1-3 sentence greeting summary.

    Args:
        briefing: Output of briefing_service.generate_daily_briefing()
            (may be None if disabled/empty tenant).

    Returns:
        Formatted string like:
        "Temos 3 ofertas pendentes, 5 candidatos parados há >7 dias e 2
        entrevistas sem feedback."
        Empty string if briefing is None/empty/disabled.

    Policy:
        - Mentions counts only (never raw candidate names — LGPD G5 defense
          in depth; the ChatAdapter G5 redactor would also catch)
        - Top 3 signals max to keep greeting concise
        - Ordered by urgency (urgent_actions first)
    """
    if not _PROACTIVE_AGENDA_ENABLED or not briefing:
        return ""

    parts: list[str] = []

    # 1. Urgent actions (most important)
    urgent = briefing.get("urgent_actions") or []
    n_urgent = len(urgent) if isinstance(urgent, list) else 0
    if n_urgent > 0:
        label = "ações urgentes" if n_urgent != 1 else "ação urgente"
        parts.append(f"{n_urgent} {label}")

    # 2. Pipeline signals (candidates stale, missing feedback)
    pipeline = briefing.get("pipeline_summary") or {}
    stale_candidates = pipeline.get("stale_candidates_count", 0) if isinstance(pipeline, dict) else 0
    missing_feedback = pipeline.get("missing_feedback_count", 0) if isinstance(pipeline, dict) else 0

    if stale_candidates and stale_candidates > 0:
        parts.append(f"{stale_candidates} candidato{'s' if stale_candidates != 1 else ''} parado{'s' if stale_candidates != 1 else ''} há >7 dias")

    if missing_feedback and missing_feedback > 0:
        parts.append(f"{missing_feedback} entrevista{'s' if missing_feedback != 1 else ''} sem feedback")

    # 3. Pending offers (from pending_tasks or alerts)
    alerts = briefing.get("active_alerts") or []
    n_alerts = len(alerts) if isinstance(alerts, list) else 0
    if n_alerts > 0 and len(parts) < 3:
        parts.append(f"{n_alerts} alerta{'s' if n_alerts != 1 else ''}")

    if not parts:
        return ""

    # Compose: "Temos X, Y e Z."
    if len(parts) == 1:
        return f"Temos {parts[0]}."
    elif len(parts) == 2:
        return f"Temos {parts[0]} e {parts[1]}."
    else:
        return f"Temos {parts[0]}, {parts[1]} e {parts[2]}."


async def get_cached_briefing(
    user_id: str,
    company_id: str,
    *,
    ttl_s: int = _DEFAULT_TTL_S,
    db: Any = None,
) -> dict[str, Any] | None:
    """Get briefing from cache or generate fresh.

    TTL cache prevents DB thrash on every greeting (user opens chat → 1 call per
    5min window, not per turn).

    Returns None if disabled or generation fails (fail-safe for greeting path).
    """
    if not _PROACTIVE_AGENDA_ENABLED:
        return None

    key = (str(user_id), str(company_id))
    now = time.time()

    cached = _CACHE.get(key)
    if cached and cached[1] > now:
        return cached[0]

    # Miss or expired — regenerate
    try:
        from app.shared.services.briefing_service import briefing_service
        briefing = await briefing_service.generate_daily_briefing(
            user_id=user_id, db=db,
        )
        _CACHE[key] = (briefing, now + ttl_s)
        return briefing
    except Exception as exc:
        logger.debug("[Init IV] briefing generation failed (non-fatal): %s", exc)
        return None


def invalidate_cache(user_id: str | None = None, company_id: str | None = None) -> None:
    """Invalidate briefing cache for specific user or all."""
    global _CACHE
    if user_id is None and company_id is None:
        _CACHE = {}
        return
    if user_id is not None and company_id is not None:
        _CACHE.pop((str(user_id), str(company_id)), None)
