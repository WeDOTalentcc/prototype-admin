"""Goal service — chat-surface canonical for the recruiter assistant.

Provides a single entry point used by the recruiter_assistant chat tool
``assistant_track_goals``. Aggregates real recruiting goals/quotas from
the canonical ``goals`` table (see ``lia_models.goal.Goal`` and
``app.repositories.goals_repository.GoalsRepository``) and
returns a structured progress payload (totals, on-track / at-risk /
achieved counts, per-goal progress) for the chat surface to consume.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Iterable

from lia_models.goal import Goal, GoalStatus

logger = logging.getLogger(__name__)


_PERIOD_ALIASES: dict[str, str] = {
    "current_month": "monthly",
    "month": "monthly",
    "monthly": "monthly",
    "current_quarter": "quarterly",
    "quarter": "quarterly",
    "quarterly": "quarterly",
    "current_year": "yearly",
    "year": "yearly",
    "yearly": "yearly",
}

_AT_RISK_GAP_PCT = 15.0


def _normalize_period(period: str | None) -> str | None:
    if not period:
        return None
    return _PERIOD_ALIASES.get(period.strip().lower())


_MISSING = object()


def _coerce_company_id(company_id: Any) -> uuid.UUID | None | object:
    """Return a UUID, ``None`` if no value was supplied, or ``_MISSING``
    if a value was supplied but is not a valid UUID (so callers can
    distinguish ``missing`` vs ``invalid``)."""
    if company_id is None or company_id == "":
        return None
    if isinstance(company_id, uuid.UUID):
        return company_id
    try:
        return uuid.UUID(str(company_id))
    except (ValueError, AttributeError, TypeError):
        return _MISSING


def _classify(goal: Goal, *, now: datetime | None = None) -> str:
    """Bucket a goal into achieved / at_risk / on_track."""
    progress = float(goal.progress or 0.0)
    status = (goal.status or "").lower()

    if status == GoalStatus.ACHIEVED.value or progress >= 100.0:
        return "achieved"

    if status == GoalStatus.OVERDUE.value:
        return "at_risk"

    end_date = goal.end_date
    start_date = goal.start_date
    if end_date and start_date:
        ref_now = now or datetime.utcnow()
        end = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
        start = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
        total = (end - start).total_seconds()
        elapsed = (ref_now - start).total_seconds()
        if total > 0 and 0 <= elapsed <= total:
            elapsed_pct = (elapsed / total) * 100.0
            if elapsed_pct - progress > _AT_RISK_GAP_PCT:
                return "at_risk"
        elif end and ref_now > end:
            return "at_risk"

    return "on_track"


def _scope_error(
    code: str,
    detail: str,
    *,
    user_id: Any,
    company_id: Any,
    period: Any,
) -> dict[str, Any]:
    """Fail-closed payload for missing/invalid scoping inputs.

    Critical: never pass partial scope to the repository — that would
    risk returning goals across tenants. Callers receive a structured
    error instead.
    """
    logger.warning(
        "GoalService.get_user_goals rejected: %s (user=%s company=%s period=%s)",
        code, user_id, company_id, period,
    )
    return {
        "success": False,
        "error": code,
        "detail": detail,
        "user_id": user_id,
        "company_id": str(company_id) if company_id is not None else None,
        "period": period,
        "goals": [],
        "summary": {"total": 0, "on_track": 0, "at_risk": 0, "achieved": 0},
    }


def _serialize(goal: Goal, bucket: str) -> dict[str, Any]:
    return {
        "id": str(goal.id),
        "name": goal.name,
        "description": goal.description,
        "category": goal.category,
        "period": goal.period,
        "status": goal.status,
        "target": float(goal.target or 0.0),
        "current": float(goal.current or 0.0),
        "unit": goal.unit,
        "progress": float(goal.progress or 0.0),
        "start_date": goal.start_date.isoformat() if goal.start_date else None,
        "end_date": goal.end_date.isoformat() if goal.end_date else None,
        "bucket": bucket,
    }


def aggregate_goals(
    goals: Iterable[Goal], *, now: datetime | None = None
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Pure aggregation: produce per-goal payload + summary counts."""
    items: list[dict[str, Any]] = []
    summary = {"total": 0, "on_track": 0, "at_risk": 0, "achieved": 0}
    for goal in goals:
        bucket = _classify(goal, now=now)
        summary["total"] += 1
        summary[bucket] += 1
        items.append(_serialize(goal, bucket))
    return items, summary


class GoalService:
    """Aggregates user/team recruiting goals for the chat assistant."""

    async def get_user_goals(
        self,
        user_id: str = "",
        company_id: str | uuid.UUID | None = None,
        period: str = "current_month",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return the user's recruiting goals and current progress.

        Reads from the canonical ``goals`` table scoped by ``company_id``
        and the requested ``period``. Returns aggregated counts plus the
        per-goal items used by the chat surface.

        Fails closed: rejects requests with a missing/invalid
        ``company_id``, missing ``user_id``, or an unknown ``period``
        instead of falling back to an unscoped query (which would risk
        leaking goals across tenants).
        """
        normalized_period = _normalize_period(period)
        coerced_company_id = _coerce_company_id(company_id)

        logger.info(
            "GoalService.get_user_goals user=%s company=%s period=%s -> %s",
            user_id, company_id, period, normalized_period,
        )

        if coerced_company_id is None:
            return _scope_error(
                "missing_company_id",
                "company_id is required",
                user_id=user_id, company_id=company_id, period=period,
            )
        if coerced_company_id is _MISSING:
            return _scope_error(
                "invalid_company_id",
                "company_id must be a valid UUID",
                user_id=user_id, company_id=company_id, period=period,
            )
        if not user_id or not str(user_id).strip():
            return _scope_error(
                "missing_user_id",
                "user_id is required",
                user_id=user_id, company_id=company_id, period=period,
            )
        if normalized_period is None:
            return _scope_error(
                "invalid_period",
                f"period {period!r} is not recognized; expected one of "
                f"{sorted(set(_PERIOD_ALIASES))}",
                user_id=user_id, company_id=company_id, period=period,
            )

        try:
            goals = await self._fetch_goals(
                user_id=str(user_id).strip(),
                company_id=coerced_company_id,
                period=normalized_period,
            )
        except Exception as exc:
            # Log the full exception for operators; surface only a
            # generic message so backend internals (SQL, paths, etc.)
            # don't leak into chat responses.
            logger.exception("GoalService.get_user_goals fetch failed: %s", exc)
            return {
                "success": False,
                "error": "goal_fetch_failed",
                "detail": "Unable to load goals at this time.",
                "user_id": user_id,
                "company_id": str(coerced_company_id),
                "period": period,
                "goals": [],
                "summary": {"total": 0, "on_track": 0, "at_risk": 0, "achieved": 0},
            }

        items, summary = aggregate_goals(goals)

        return {
            "success": True,
            "user_id": user_id,
            "company_id": str(coerced_company_id) if coerced_company_id else (
                str(company_id) if company_id else None
            ),
            "period": period,
            "normalized_period": normalized_period,
            "goals": items,
            "summary": summary,
        }

    async def _fetch_goals(
        self,
        *,
        user_id: str | None,
        company_id: uuid.UUID | None,
        period: str | None,
    ) -> list[Goal]:
        """Open a session and read goals from the canonical repository.

        Isolated for ease of testing — unit tests patch this method to
        avoid needing a live database connection.
        """
        # Imported lazily so the module remains importable in environments
        # (e.g. unit tests) where the database stack is not configured.
        from app.core.database import AsyncSessionLocal
        from app.repositories.goals_repository import (
            GoalsRepository,
        )

        async with AsyncSessionLocal() as session:
            repo = GoalsRepository(session)
            return await repo.list_goals(
                user_id=user_id,
                company_id=company_id,
                period=period,
            )


goal_service = GoalService()


def get_goal_service() -> GoalService:
    return goal_service
