"""
Plan Limits Service — enforces per-plan usage quotas.

Provides a FastAPI dependency `check_plan_limits` that raises HTTP 402
when a company has reached its plan's limit for active jobs or users.

Limits are defined in settings (app/core/config.py) and keyed by the
plan_code stored in the Subscription model.  Unknown plan codes fall
back to starter limits (conservative).

Usage:
    @router.post("/jobs")
    async def create_job(
        ...,
        _: None = Depends(check_active_jobs_limit),
    ):
"""

from __future__ import annotations

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "plan_limits_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)


import logging

from fastapi import Depends, HTTPException, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.config import settings
from app.core.database import get_db
from lia_models.billing import Subscription, SubscriptionStatus
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)

# Plan code prefixes that identify each tier
_STARTER_CODES = {"starter", "basic", "free"}
_PRO_CODES = {"pro", "professional", "growth"}
_ENTERPRISE_CODES = {"enterprise", "unlimited", "custom"}
_TRIAL_CODES = {"trial", "trialing"}


def _get_limits(plan_code: str, status: str) -> dict:
    """Return usage limits for a given plan code."""
    code = (plan_code or "").lower()
    is_trial = status == SubscriptionStatus.TRIALING.value

    if is_trial or any(code.startswith(t) for t in _TRIAL_CODES):
        return {
            "active_jobs": settings.PLAN_TRIAL_ACTIVE_JOBS,
            "users": settings.PLAN_TRIAL_USERS,
            "candidates_per_job": settings.PLAN_TRIAL_CANDIDATES_PER_JOB,
            "plan_label": "Trial",
        }
    if any(code.startswith(t) for t in _ENTERPRISE_CODES):
        return {
            "active_jobs": settings.PLAN_ENTERPRISE_ACTIVE_JOBS,
            "users": settings.PLAN_ENTERPRISE_USERS,
            "candidates_per_job": settings.PLAN_ENTERPRISE_CANDIDATES_PER_JOB,
            "plan_label": "Enterprise",
        }
    if any(code.startswith(t) for t in _PRO_CODES):
        return {
            "active_jobs": settings.PLAN_PRO_ACTIVE_JOBS,
            "users": settings.PLAN_PRO_USERS,
            "candidates_per_job": settings.PLAN_PRO_CANDIDATES_PER_JOB,
            "plan_label": "Pro",
        }
    # Default: Starter
    return {
        "active_jobs": settings.PLAN_STARTER_ACTIVE_JOBS,
        "users": settings.PLAN_STARTER_USERS,
        "candidates_per_job": settings.PLAN_STARTER_CANDIDATES_PER_JOB,
        "plan_label": "Starter",
    }


async def _get_subscription(db: AsyncSession, company_id: str) -> Subscription | None:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.client_id == company_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _count_active_jobs(db: AsyncSession, company_id: str) -> int:
    result = await db.execute(
        select(func.count(JobVacancy.id)).where(
            and_(
                JobVacancy.company_id == company_id,
                JobVacancy.status == "Ativa",
            )
        )
    )
    return result.scalar_one() or 0


def _limit_exceeded_error(resource: str, current: int, limit: int, plan_label: str) -> HTTPException:
    return HTTPException(
        status_code=402,
        detail={
            "code": "PLAN_LIMIT_REACHED",
            "resource": resource,
            "current": current,
            "limit": limit,
            "plan": plan_label,
            "message": (
                f"Você atingiu o limite de {limit} {resource} no plano {plan_label}. "
                "Faça upgrade para continuar."
            ),
            "upgrade_url": "/upgrade",
        },
    )


async def check_active_jobs_limit(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Dependency: raises HTTP 402 if the company has reached its active jobs limit.
    Add to POST /jobs endpoints.
    """
    if not settings.PLAN_LIMITS_ENFORCE:
        return

    if getattr(current_user, "is_superadmin", False):
        return

    company_id = get_user_company_id(current_user)

    try:
        subscription = await _get_subscription(db, company_id)
        plan_code = subscription.plan_code if subscription else "starter"
        status = subscription.status if subscription else "active"
        limits = _get_limits(plan_code, status)

        current = await _count_active_jobs(db, company_id)
        if current >= limits["active_jobs"]:
            logger.warning(
                "Plan limit reached: active_jobs company=%s current=%d limit=%d",
                company_id, current, limits["active_jobs"],
            )
            raise _limit_exceeded_error(
                "vagas ativas", current, limits["active_jobs"], limits["plan_label"]
            )

    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Plan limit check failed — allowing request: %s", exc)


async def check_active_jobs_limit_or_demo(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not settings.PLAN_LIMITS_ENFORCE:
        return

    if getattr(current_user, "is_superadmin", False):
        return

    company_id = get_user_company_id(current_user)

    try:
        subscription = await _get_subscription(db, company_id)
        plan_code = subscription.plan_code if subscription else "starter"
        status = subscription.status if subscription else "active"
        limits = _get_limits(plan_code, status)

        current = await _count_active_jobs(db, company_id)
        if current >= limits["active_jobs"]:
            logger.warning(
                "Plan limit reached: active_jobs company=%s current=%d limit=%d",
                company_id, current, limits["active_jobs"],
            )
            raise _limit_exceeded_error(
                "vagas ativas", current, limits["active_jobs"], limits["plan_label"]
            )

    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Plan limit check failed — allowing request: %s", exc)
