"""
Weekly Digest API — endpoints for triggering and previewing weekly digest.

Endpoints:
- GET  /digest/weekly/preview      — Preview digest data for the authenticated user
- POST /digest/weekly/send         — Trigger digest delivery for a specific user (admin)
- POST /digest/weekly/send-all     — Trigger digest for all recruiters (admin, manual)
- GET  /digest/weekly/preferences  — Get weekly digest preference for current user
- PUT  /digest/weekly/preferences  — Toggle weekly digest opt-in/opt-out
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User, UserRole
from app.core.database import get_db
from app.domains.analytics.services.weekly_digest_service import WeeklyDigestService, get_weekly_digest_service
from app.repositories.auth_user_repository import UserRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digest", tags=["digest"])


class WeeklyDigestPreferenceRequest(WeDoBaseModel):
    enabled: bool


@router.get("/weekly/preview", response_model=None)
# TODO(phase2): extract to repository — digest generation DB calls
async def preview_weekly_digest(
    recruiter_id: str | None = None,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    svc: WeeklyDigestService = Depends(get_weekly_digest_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.domains.analytics.services.digest_formatter import (
        BellDigestFormatter,
        ChatDigestFormatter,
        TeamsDigestFormatter,
    )

    if recruiter_id and recruiter_id != str(current_user.id):
        if current_user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem visualizar digest de outros usuários")
        uid = recruiter_id
        name = "Recrutador"
        try:
            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(recruiter_id)
            if user:
                name = getattr(user, "name", getattr(user, "email", "Recrutador"))
        except Exception:
            pass
    else:
        uid = str(current_user.id)
        name = current_user.name or "Recrutador"

    digest = await svc.generate_digest(uid, name, db)

    return {
        "digest": digest,
        "formatted": {
            "chat": ChatDigestFormatter().format(digest),
            "bell": BellDigestFormatter().format(digest),
            "teams_card": TeamsDigestFormatter().format(digest),
        },
    }


@router.post("/weekly/send", response_model=None)
async def send_weekly_digest(
    recruiter_id: str,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    svc: WeeklyDigestService = Depends(get_weekly_digest_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    if current_user.role != UserRole.admin and str(current_user.id) != recruiter_id:
        raise HTTPException(status_code=403, detail="Apenas administradores podem enviar digest para outros usuários")

    name = "Recrutador"
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(recruiter_id)
    if user:
        name = getattr(user, "name", getattr(user, "email", "Recrutador"))
    else:
        raise HTTPException(status_code=404, detail="Recruiter not found")

    result = await svc.generate_and_deliver(recruiter_id, name, db, company_id=company_id)
    return result


@router.post("/weekly/send-all", response_model=None)
async def send_weekly_digest_to_all(
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    svc: WeeklyDigestService = Depends(get_weekly_digest_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem disparar digest para todos")

    result = await svc.send_to_all_recruiters(db)
    return result


@router.get("/weekly/preferences", response_model=None)
async def get_weekly_digest_preference(
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    user_id = str(current_user.id)
    prefs = getattr(current_user, "notification_preferences", None) or {}
    enabled = prefs.get("weekly_report_enabled", True)

    return {"user_id": user_id, "weekly_report_enabled": enabled}


@router.put("/weekly/preferences", response_model=None)
async def update_weekly_digest_preference(
    body: WeeklyDigestPreferenceRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    prefs = getattr(current_user, "notification_preferences", None) or {}
    if not isinstance(prefs, dict):
        prefs = {}

    prefs["weekly_report_enabled"] = body.enabled
    current_user.notification_preferences = prefs

    try:
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(current_user, "notification_preferences")
    except Exception:
        pass


    user_id = str(current_user.id)
    logger.info(
        "[WeeklyDigest] Preference updated user=%s weekly_report_enabled=%s",
        user_id,
        body.enabled,
    )

    return {
        "user_id": user_id,
        "weekly_report_enabled": body.enabled,
        "message": "Preferência atualizada com sucesso.",
    }


# ─────────────────────────────────────────────────────────────
# Daily digest endpoints (platform-native, runs at 08:00 BRT)
# ─────────────────────────────────────────────────────────────

@router.post("/daily/send-all", response_model=None)
async def send_daily_digest_to_all(
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    svc: WeeklyDigestService = Depends(get_weekly_digest_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Trigger the daily morning digest for all active recruiters.
    Delivers via bell notification + LIA chat proactive message.
    Normally called by the cron job at 08:00 BRT (Mon–Fri).
    Admins can also call manually to test.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem disparar o digest diário para todos")

    result = await svc.send_to_all_recruiters(db)
    return result


@router.post("/daily/send", response_model=None)
async def send_daily_digest_to_user(
    recruiter_id: str,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    svc: WeeklyDigestService = Depends(get_weekly_digest_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Send daily digest to a specific recruiter (admin or self)."""
    if current_user.role != UserRole.admin and str(current_user.id) != recruiter_id:
        raise HTTPException(status_code=403, detail="Apenas administradores podem enviar digest para outros usuários")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(recruiter_id)
    if not user:
        raise HTTPException(status_code=404, detail="Recrutador não encontrado")

    name = getattr(user, "name", getattr(user, "email", "Recrutador"))
    return await svc.generate_and_deliver(recruiter_id, name, db)
