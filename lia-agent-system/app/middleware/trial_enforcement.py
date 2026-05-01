"""
Trial Enforcement — FastAPI dependency that blocks access after trial expiry.

Used as a dependency on protected endpoints. Returns HTTP 402 with a
structured payload when the company's trial has expired, guiding the
frontend to the upgrade flow.

Usage in an endpoint:
    @router.post("/jobs")
    async def create_job(
        ...,
        _: None = Depends(require_active_subscription),
    ):

The check is intentionally lightweight: one DB query per request on the
subscriptions table, cached in request.state to avoid duplicate queries
within the same request.
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.models.billing import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)

_TRIAL_EXPIRED_STATUSES = {
    SubscriptionStatus.CANCELLED.value,
    SubscriptionStatus.SUSPENDED.value,
}

_UPGRADE_URL = "/upgrade"


async def _get_subscription(db: AsyncSession, company_id: str) -> Subscription | None:
    """Fetch the most recent subscription for the company."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.client_id == company_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def require_active_subscription(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Dependency: raises HTTP 402 if the company's trial has expired.

    Skips check for superadmin users (platform admins).
    Caches result in request.state so multiple dependencies in the same
    request don't hit the DB twice.
    """
    # Skip for platform admins
    if getattr(current_user, "is_superadmin", False):
        return

    # Cache within the same request
    if hasattr(request.state, "subscription_checked"):
        if request.state.subscription_blocked:
            _raise_trial_expired()
        return

    company_id = get_user_company_id(current_user)

    try:
        subscription = await _get_subscription(db, company_id)
    except Exception as exc:
        logger.warning("Subscription check failed — allowing request: %s", exc)
        request.state.subscription_checked = True
        request.state.subscription_blocked = False
        return

    blocked = False

    if subscription is not None:
        # Trial expired: status TRIALING but trial_end has passed
        if (
            subscription.status == SubscriptionStatus.TRIALING.value
            and subscription.trial_end is not None
            and subscription.trial_end < datetime.utcnow()
        ):
            # Mark as expired in the DB (soft transition — no side effects)
            subscription.status = SubscriptionStatus.SUSPENDED.value
            try:
                await db.commit()
                logger.info(
                    "Trial expired — subscription suspended",
                    extra={"company_id": company_id, "trial_end": subscription.trial_end.isoformat()},
                )
            except Exception:
                await db.rollback()
            blocked = True

        elif subscription.status in _TRIAL_EXPIRED_STATUSES:
            blocked = True

    request.state.subscription_checked = True
    request.state.subscription_blocked = blocked

    if blocked:
        _raise_trial_expired()


async def require_active_subscription_or_demo(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
) -> None:
    if getattr(current_user, "is_superadmin", False):
        return

    if hasattr(request.state, "subscription_checked"):
        if request.state.subscription_blocked:
            _raise_trial_expired()
        return

    company_id = get_user_company_id(current_user)

    try:
        subscription = await _get_subscription(db, company_id)
    except Exception as exc:
        logger.warning("Subscription check failed — allowing request: %s", exc)
        request.state.subscription_checked = True
        request.state.subscription_blocked = False
        return

    blocked = False

    if subscription is not None:
        if (
            subscription.status == SubscriptionStatus.TRIALING.value
            and subscription.trial_end is not None
            and subscription.trial_end < datetime.utcnow()
        ):
            subscription.status = SubscriptionStatus.SUSPENDED.value
            try:
                await db.commit()
            except Exception:
                await db.rollback()
            blocked = True
        elif subscription.status in _TRIAL_EXPIRED_STATUSES:
            blocked = True

    request.state.subscription_checked = True
    request.state.subscription_blocked = blocked

    if blocked:
        _raise_trial_expired()


def _raise_trial_expired() -> None:
    raise HTTPException(
        status_code=402,
        detail={
            "code": "TRIAL_EXPIRED",
            "message": "Seu período de trial expirou. Faça upgrade para continuar usando a plataforma.",
            "upgrade_url": _UPGRADE_URL,
        },
    )
