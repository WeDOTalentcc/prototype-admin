"""
Hiring NPS API — post-hire satisfaction surveys for candidates and managers.

  POST   /hiring-nps              — send NPS survey (authenticated)
  GET    /hiring-nps              — list surveys for company (authenticated)
  GET    /hiring-nps/respond      — load survey context via token (public)
  PATCH  /hiring-nps/{id}/respond — submit NPS score via token (public)
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.repositories.hiring_nps_repository import HiringNpsRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hiring-nps", tags=["Hiring NPS"])


# ── Schemas ────────────────────────────────────────────────────────────────

class SendNpsRequest(BaseModel):
    job_vacancy_id: str
    respondent_type: str = Field(..., pattern="^(candidate|manager)$")
    respondent_email: EmailStr
    candidate_id: Optional[str] = None
    ttl_hours: int = Field(168, ge=1, le=720)

    model_config = {"extra": "forbid"}


class SubmitNpsRequest(BaseModel):
    token: str
    score: int = Field(..., ge=0, le=10)
    comment: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_response(nps) -> dict:
    return {
        "id": nps.id,
        "job_vacancy_id": nps.job_vacancy_id,
        "respondent_type": nps.respondent_type,
        "respondent_email": nps.respondent_email,
        "status": nps.status,
        "score": nps.score,
        "comment": nps.comment,
        "responded_at": nps.responded_at.isoformat() if nps.responded_at else None,
        "expires_at": nps.expires_at.isoformat(),
        "created_at": nps.created_at.isoformat(),
        "public_url": f"/pt/nps/{nps.token}",
    }


async def _send_nps_email(nps, db: AsyncSession) -> None:
    """Fire-and-forget NPS survey email. Never raises."""
    try:
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        from app.domains.communication.services.email_service import MailgunEmailService

        base_url = os.getenv("NEXT_PUBLIC_APP_URL", "https://ai.wedotalent.cc")
        survey_link = f"{base_url}/pt/nps/{nps.token}"

        if nps.respondent_type == "candidate":
            subject = "Como foi sua experiência no processo seletivo?"
            body_html = (
                f"<p>Olá!</p>"
                f"<p>Gostaríamos de saber como foi sua experiência durante o processo seletivo. "
                f"Sua opinião é muito importante para continuarmos melhorando.</p>"
                f"<p><a href='{survey_link}' style='background:#60BED1;color:white;padding:10px 20px;"
                f"border-radius:6px;text-decoration:none;font-weight:600;display:inline-block'>"
                f"Responder pesquisa</a></p>"
                f"<p style='color:#9CA3AF;font-size:12px'>Leva menos de 1 minuto. "
                f"Link válido até {nps.expires_at.strftime('%d/%m/%Y')}.</p>"
            )
        else:
            subject = "Avalie o processo de recrutamento"
            body_html = (
                f"<p>Olá!</p>"
                f"<p>Como gestor, gostaríamos de saber sua opinião sobre o processo de recrutamento "
                f"realizado pela WeDo Talent para sua vaga.</p>"
                f"<p><a href='{survey_link}' style='background:#60BED1;color:white;padding:10px 20px;"
                f"border-radius:6px;text-decoration:none;font-weight:600;display:inline-block'>"
                f"Responder avaliação</a></p>"
                f"<p style='color:#9CA3AF;font-size:12px'>Link válido até {nps.expires_at.strftime('%d/%m/%Y')}.</p>"
            )

        body_text = f"Acesse o link para responder: {survey_link}"
        svc = MailgunEmailService()
        await svc.send_email(
            to_email=nps.respondent_email,
            subject=subject,
            body=body_text,
            body_html=body_html,
            categories=["hiring-nps"],
        )
        logger.info("[NPS] Survey email sent to %s nps=%s", nps.respondent_email, nps.id)
    except Exception as e:
        logger.warning("[NPS] Email send failed (non-blocking): %s", e)


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("")
async def list_nps(
    job_vacancy_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"surveys": []}

    repo = HiringNpsRepository(db)
    if job_vacancy_id:
        surveys = await repo.list_for_job(company_id, job_vacancy_id, status=status, limit=limit)
    else:
        from sqlalchemy import and_, select
        from lia_models.hiring_nps import HiringNps
        filters = [HiringNps.company_id == company_id]
        if status:
            filters.append(HiringNps.status == status)
        result = await db.execute(
            select(HiringNps).where(and_(*filters)).order_by(HiringNps.created_at.desc()).limit(limit)
        )
        surveys = result.scalars().all()

    return {"surveys": [_to_response(s) for s in surveys]}


@router.post("", status_code=201)
async def send_nps(
    payload: SendNpsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create and send an NPS survey to a candidate or manager."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(403, "company_id not found in token")

    repo = HiringNpsRepository(db)
    nps = await repo.create(
        company_id=company_id,
        job_vacancy_id=payload.job_vacancy_id,
        respondent_type=payload.respondent_type,
        candidate_id=payload.candidate_id,
        respondent_email=str(payload.respondent_email),
        sent_by=str(getattr(current_user, "id", "")),
        ttl_hours=payload.ttl_hours,
    )
    await db.commit()

    logger.info("[NPS] Created nps=%s job=%s type=%s", nps.id, payload.job_vacancy_id, payload.respondent_type)
    await _send_nps_email(nps, db)

    return _to_response(nps)


@router.get("/respond")
async def get_nps_context(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Public — load survey context by token."""
    repo = HiringNpsRepository(db)
    nps = await repo.get_by_token(token)

    if not nps:
        raise HTTPException(404, "Link inválido ou expirado")

    if nps.is_expired() and nps.status == "pending":
        nps.status = "expired"
        await db.commit()

    if nps.status == "expired":
        raise HTTPException(410, "Este link de pesquisa expirou")

    if nps.status == "responded":
        return {
            "already_responded": True,
            "score": nps.score,
            "responded_at": nps.responded_at.isoformat() if nps.responded_at else None,
        }

    job_info = await _fetch_job_title(nps.job_vacancy_id, nps.company_id, db)

    return {
        "nps_id": nps.id,
        "status": nps.status,
        "respondent_type": nps.respondent_type,
        "job": job_info,
        "expires_at": nps.expires_at.isoformat(),
    }


@router.patch("/{nps_id}/respond")
async def submit_nps(
    nps_id: str,
    payload: SubmitNpsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public — submit NPS score via token."""
    repo = HiringNpsRepository(db)
    nps = await repo.get_by_token(payload.token)

    if not nps or nps.id != nps_id:
        raise HTTPException(404, "Link inválido")

    if nps.is_expired():
        raise HTTPException(410, "Este link de pesquisa expirou")

    if nps.status != "pending":
        raise HTTPException(409, f"Pesquisa já respondida")

    updated = await repo.respond(nps, score=payload.score, comment=payload.comment)
    await db.commit()

    logger.info("[NPS] Responded nps=%s score=%s", nps_id, payload.score)
    return {"id": updated.id, "status": updated.status, "score": updated.score}


# ── Internal helper ────────────────────────────────────────────────────────

async def _fetch_job_title(job_id: str, company_id: str, db: AsyncSession) -> dict:
    try:
        import uuid as _uuid
        from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository
        repo = JobVacancyCrudRepository(db)
        vacancy = await repo.get_vacancy_by_id_and_company(
            _uuid.UUID(job_id) if len(job_id) == 36 else job_id,
            company_id,
        )
        if vacancy:
            return {"id": job_id, "title": getattr(vacancy, "title", None)}
    except Exception as e:
        logger.warning("[NPS] job title fetch failed: %s", e)
    return {"id": job_id}
