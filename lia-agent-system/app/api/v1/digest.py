"""
Weekly Digest API — endpoints for triggering and previewing weekly digest.

Endpoints:
- GET  /digest/weekly/preview      — Preview digest data for the authenticated user
- POST /digest/weekly/send         — Trigger digest delivery for a specific user (admin)
- POST /digest/weekly/send-all     — Trigger digest for all recruiters (admin, manual)
- GET  /digest/weekly/preferences  — Get weekly digest preference for a user
- PUT  /digest/weekly/preferences  — Toggle weekly digest opt-in/opt-out
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digest", tags=["digest"])


class WeeklyDigestPreferenceRequest(BaseModel):
    user_id: str
    enabled: bool


@router.get("/weekly/preview")
async def preview_weekly_digest(
    recruiter_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    from app.domains.analytics.services.weekly_digest_service import WeeklyDigestService

    svc = WeeklyDigestService()
    uid = recruiter_id or "preview-user"
    name = "Recrutador"

    if recruiter_id:
        try:
            from app.auth.models import User
            from sqlalchemy import select

            result = await db.execute(select(User).where(User.id == recruiter_id))
            user = result.scalar_one_or_none()
            if user:
                name = getattr(user, "name", getattr(user, "email", "Recrutador"))
        except Exception:
            pass

    digest = await svc.generate_digest(uid, name, db)

    from app.domains.analytics.services.digest_formatter import (
        TeamsDigestFormatter,
        ChatDigestFormatter,
        BellDigestFormatter,
    )

    return {
        "digest": digest,
        "formatted": {
            "chat": ChatDigestFormatter().format(digest),
            "bell": BellDigestFormatter().format(digest),
            "teams_card": TeamsDigestFormatter().format(digest),
        },
    }


@router.post("/weekly/send")
async def send_weekly_digest(
    recruiter_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.domains.analytics.services.weekly_digest_service import WeeklyDigestService

    svc = WeeklyDigestService()

    name = "Recrutador"
    try:
        from app.auth.models import User
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.id == recruiter_id))
        user = result.scalar_one_or_none()
        if user:
            name = getattr(user, "name", getattr(user, "email", "Recrutador"))
        else:
            raise HTTPException(status_code=404, detail="Recruiter not found")
    except HTTPException:
        raise
    except Exception:
        pass

    result = await svc.generate_and_deliver(recruiter_id, name, db)
    return result


@router.post("/weekly/send-all")
async def send_weekly_digest_to_all(
    db: AsyncSession = Depends(get_db),
):
    from app.domains.analytics.services.weekly_digest_service import WeeklyDigestService

    svc = WeeklyDigestService()
    result = await svc.send_to_all_recruiters(db)
    return result


@router.get("/weekly/preferences")
async def get_weekly_digest_preference(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    try:
        _uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return {"user_id": user_id, "weekly_report_enabled": True}

    from app.auth.models import User
    from sqlalchemy import select

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except Exception:
        return {"user_id": user_id, "weekly_report_enabled": True}

    if not user:
        return {"user_id": user_id, "weekly_report_enabled": True}

    prefs = getattr(user, "notification_preferences", None) or {}
    enabled = prefs.get("weekly_report_enabled", True)

    return {"user_id": user_id, "weekly_report_enabled": enabled}


@router.put("/weekly/preferences")
async def update_weekly_digest_preference(
    body: WeeklyDigestPreferenceRequest,
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    try:
        _uuid.UUID(body.user_id)
    except (ValueError, AttributeError):
        return {
            "user_id": body.user_id,
            "weekly_report_enabled": body.enabled,
            "message": "Preferência registrada (usuário temporário).",
        }

    from app.auth.models import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = getattr(user, "notification_preferences", None) or {}
    if not isinstance(prefs, dict):
        prefs = {}

    prefs["weekly_report_enabled"] = body.enabled
    user.notification_preferences = prefs

    try:
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "notification_preferences")
    except Exception:
        pass

    await db.commit()

    logger.info(
        "[WeeklyDigest] Preference updated user=%s weekly_report_enabled=%s",
        body.user_id,
        body.enabled,
    )

    return {
        "user_id": body.user_id,
        "weekly_report_enabled": body.enabled,
        "message": "Preferência atualizada com sucesso.",
    }
