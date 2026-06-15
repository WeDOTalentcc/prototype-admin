"""
Briefing API endpoints.

Provides endpoints for:
- Getting daily briefing
- Refreshing briefing
"""
import asyncio
import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from app.shared.observability.canary_metrics import (
    inc_briefing_generated,
    obs_briefing_duration,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.services.briefing_service import briefing_service
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/briefing", tags=["briefing"])

# Task 3.G (2026-05-25): timeout + stale-cache fallback
# If generate_daily_briefing() takes longer than this, we return stale cache.
BRIEFING_TIMEOUT_SECONDS = 15.0
# Stale briefing is acceptable for up to 1 hour (briefing refreshes hourly).
_BRIEFING_STALE_TTL_SECONDS = 3600

# In-memory stale cache — keyed by "{company_id}:{user_id}".
# Not Redis: briefing is per-request, single-process cache is sufficient.
# LGPD: key includes company_id so cross-tenant lookup is structurally impossible.
_briefing_cache: dict[str, dict] = {}

_EMPTY_BRIEFING = {
    "urgent_actions": [],
    "pipeline_summary": {},
    "today_schedule": [],
    "pending_tasks": [],
    "active_alerts": [],
    "insights": [],
}


def _get_stale(cache_key: str) -> dict | None:
    """Return cached briefing if still within TTL, else None."""
    entry = _briefing_cache.get(cache_key)
    if entry is None:
        return None
    age = time.monotonic() - entry["_cached_at_mono"]
    if age > _BRIEFING_STALE_TTL_SECONDS:
        _briefing_cache.pop(cache_key, None)
        return None
    return entry


def _set_stale(cache_key: str, briefing: dict) -> None:
    briefing["_cached_at_mono"] = time.monotonic()
    briefing["_cached_at"] = datetime.utcnow().isoformat()
    _briefing_cache[cache_key] = briefing


@router.get("", response_model=None)
async def get_daily_briefing(
    request: Request,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get daily briefing for a user.

    Returns comprehensive briefing including:
    - Urgent actions
    - Pipeline summary
    - Today's schedule
    - Pending tasks
    - Active alerts
    - AI-powered insights

    Safety: para "default_user" (pre-auth / anonymous), retorna briefing vazio
    em vez de 500 — evita o card quebrar enquanto o auth context hidrata no FE.

    Resilience (Task 3.G): timeout 15s + stale cache fallback (1h TTL).
    """
    request_id = getattr(request.state, "request_id", "unknown")
    if not user_id or user_id == "default_user":
        logger.info(
            "briefing.anonymous_or_default_user",
            extra={"request_id": request_id, "user_id": user_id},
        )
        inc_briefing_generated(company_id or "", "empty_user")
        return {"success": True, "data": _EMPTY_BRIEFING}

    cache_key = f"{company_id or 'unknown'}:{user_id}"
    _t0 = time.perf_counter()

    try:
        briefing = await asyncio.wait_for(
            briefing_service.generate_daily_briefing(
                user_id, db, company_id=company_id  # WT-2022 P0.TASK
            ),
            timeout=BRIEFING_TIMEOUT_SECONDS,
        )
        _elapsed = time.perf_counter() - _t0
        logger.info(
            "briefing.generated",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
                "urgent_count": briefing.get("summary", {}).get("urgent_count", 0),
                "alerts_active": briefing.get("summary", {}).get("alerts_active", 0),
            },
        )
        inc_briefing_generated(company_id or "", "success")
        obs_briefing_duration(company_id or "", _elapsed)
        _set_stale(cache_key, briefing)
        return {"success": True, "data": briefing}

    except asyncio.TimeoutError:
        _elapsed = time.perf_counter() - _t0
        stale = _get_stale(cache_key)
        logger.warning(
            "briefing.timeout — returning %s",
            "stale" if stale else "empty_degraded",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
                "timeout_seconds": BRIEFING_TIMEOUT_SECONDS,
                "stale_available": stale is not None,
            },
        )
        inc_briefing_generated(company_id or "", "timeout")
        obs_briefing_duration(company_id or "", _elapsed)
        if stale:
            return {
                "success": True,
                "data": stale,
                "degraded": True,
                "degraded_reason": "timeout",
                "stale": True,
                "stale_generated_at": stale.get("_cached_at"),
            }
        return {
            "success": True,
            "data": _EMPTY_BRIEFING,
            "degraded": True,
            "degraded_reason": "timeout_no_cache",
        }

    except HTTPException:
        raise
    except Exception as e:
        _elapsed = time.perf_counter() - _t0
        logger.error(
            "briefing.generate_failed",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
                "error": e.__class__.__name__,
            },
            exc_info=True,
        )
        inc_briefing_generated(company_id or "", "error")
        obs_briefing_duration(company_id or "", _elapsed)
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao gerar briefing: {e.__class__.__name__}",
        )


@router.post("/refresh", response_model=None)
async def refresh_briefing(
    request: Request,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Force refresh the daily briefing. Bypasses stale cache on success."""
    request_id = getattr(request.state, "request_id", "unknown")
    cache_key = f"{company_id or 'unknown'}:{user_id}"
    _t0 = time.perf_counter()

    try:
        briefing = await asyncio.wait_for(
            briefing_service.generate_daily_briefing(
                user_id, db, company_id=company_id  # WT-2022 P0.TASK
            ),
            timeout=BRIEFING_TIMEOUT_SECONDS,
        )
        _elapsed = time.perf_counter() - _t0
        logger.info(
            "briefing.refreshed",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
            },
        )
        inc_briefing_generated(company_id or "", "success")
        obs_briefing_duration(company_id or "", _elapsed)
        _set_stale(cache_key, briefing)
        return {"success": True, "data": briefing, "message": "Briefing atualizado com sucesso"}

    except asyncio.TimeoutError:
        _elapsed = time.perf_counter() - _t0
        logger.warning(
            "briefing.refresh_timeout",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
            },
        )
        inc_briefing_generated(company_id or "", "timeout")
        obs_briefing_duration(company_id or "", _elapsed)
        raise HTTPException(
            status_code=503,
            detail="Briefing demorou mais de 15s para atualizar. Tente novamente em instantes.",
        )

    except HTTPException:
        raise
    except Exception as e:
        _elapsed = time.perf_counter() - _t0
        logger.error(
            "briefing.refresh_failed",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": round(_elapsed * 1000, 1),
                "error": e.__class__.__name__,
            },
            exc_info=True,
        )
        inc_briefing_generated(company_id or "", "error")
        obs_briefing_duration(company_id or "", _elapsed)
        raise HTTPException(status_code=500, detail="Internal server error")
