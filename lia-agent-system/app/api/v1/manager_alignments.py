"""
Manager Alignments API — request + respond flows for manager sign-off on job vacancies.

Apply to: lia-agent-system/app/api/v1/manager_alignments.py
Register: app.include_router(manager_alignments_router)

Three endpoints:
  POST   /manager-alignments              — recruiter requests alignment (authenticated)
  GET    /manager-alignments/respond      — manager loads context via token (public)
  PATCH  /manager-alignments/{id}/respond — manager submits decision via token (public)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.domains.approvals.repositories.manager_alignment_repository import (
    ManagerAlignmentRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manager-alignments", tags=["Manager Alignment"])


# ── Request / Response schemas ─────────────────────────────────────────────

class CreateAlignmentRequest(BaseModel):
    job_vacancy_id: str = Field(..., description="Job vacancy requiring manager sign-off")
    manager_email: EmailStr
    manager_name: Optional[str] = None
    ttl_hours: int = Field(72, ge=1, le=336, description="Token validity in hours")

    model_config = {"extra": "forbid"}


class AlignmentResponse(BaseModel):
    id: str
    job_vacancy_id: str
    manager_email: str
    manager_name: Optional[str]
    status: str
    expires_at: str
    created_at: str


class RespondRequest(BaseModel):
    token: str
    status: str = Field(..., pattern="^(approved|rejected)$")
    response_notes: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("")
async def list_alignments(
    status: str | None = Query(None, description="Filter by status (pending, approved, rejected, expired)"),
    job_vacancy_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List manager alignments for the current company."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"alignments": []}

    from sqlalchemy import select, and_
    from lia_models.manager_alignment import ManagerAlignment as MAModel

    filters = [MAModel.company_id == company_id]
    if status:
        filters.append(MAModel.status == status)
    if job_vacancy_id:
        filters.append(MAModel.job_vacancy_id == job_vacancy_id)

    result = await db.execute(
        select(MAModel).where(and_(*filters))
        .order_by(MAModel.created_at.desc())
        .limit(limit)
    )
    alignments = result.scalars().all()
    return {"alignments": [_to_response(a) for a in alignments]}


@router.post("", status_code=201)
async def request_alignment(
    payload: CreateAlignmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Recruiter requests manager alignment for a job vacancy.
    Creates a token-signed request and returns the public link.
    """
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(403, "company_id not found in token")

    repo = ManagerAlignmentRepository(db)

    # Reuse existing pending alignment if not yet expired
    existing = await repo.get_pending_for_job(company_id, payload.job_vacancy_id)
    if existing:
        logger.info(
            "[Alignment] Reusing pending alignment=%s for job=%s",
            existing.id, payload.job_vacancy_id,
        )
        return _to_response(existing)

    alignment = await repo.create(
        company_id=company_id,
        job_vacancy_id=payload.job_vacancy_id,
        manager_email=payload.manager_email,
        manager_name=payload.manager_name,
        created_by=str(getattr(current_user, "id", "")),
        ttl_hours=payload.ttl_hours,
    )
    await db.commit()

    logger.info(
        "[Alignment] Created alignment=%s job=%s manager=%s",
        alignment.id, payload.job_vacancy_id, payload.manager_email,
    )

    # Fire-and-forget: send alignment email to manager
    await _send_alignment_email(alignment, db)

    return _to_response(alignment)


@router.get("/respond")
async def get_alignment_context(
    token: str = Query(..., description="Alignment token from email link"),
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — no auth required.
    Returns job + alignment context so the manager can review and decide.
    """
    repo = ManagerAlignmentRepository(db)
    alignment = await repo.get_by_token(token)

    if not alignment:
        raise HTTPException(404, "Link inválido ou expirado")

    if alignment.is_expired() and alignment.status == "pending":
        alignment.status = "expired"
        await db.commit()

    if alignment.status == "expired":
        raise HTTPException(410, "Este link de alinhamento expirou")

    if alignment.status in ("approved", "rejected"):
        return {
            "already_responded": True,
            "status": alignment.status,
            "responded_at": alignment.responded_at.isoformat() if alignment.responded_at else None,
        }

    # Fetch basic job info (best-effort — no auth so limited fields)
    job_info = await _fetch_job_summary(alignment.job_vacancy_id, alignment.company_id, db)

    return {
        "alignment_id": alignment.id,
        "status": alignment.status,
        "job": job_info,
        "manager_name": alignment.manager_name,
        "expires_at": alignment.expires_at.isoformat(),
    }


@router.patch("/{alignment_id}/respond")
async def respond_to_alignment(
    alignment_id: str,
    payload: RespondRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — manager submits decision using the token from their email.
    Token is the auth proof; no session cookie needed.
    """
    repo = ManagerAlignmentRepository(db)
    alignment = await repo.get_by_token(payload.token)

    if not alignment or alignment.id != alignment_id:
        raise HTTPException(404, "Link inválido")

    if alignment.is_expired():
        raise HTTPException(410, "Este link de alinhamento expirou")

    if alignment.status != "pending":
        raise HTTPException(409, f"Alinhamento já respondido: {alignment.status}")

    updated = await repo.respond(
        alignment=alignment,
        status=payload.status,
        response_notes=payload.response_notes,
    )
    await db.commit()

    logger.info(
        "[Alignment] Responded alignment=%s status=%s",
        alignment_id, payload.status,
    )

    # Notify the recruiter who created the request
    await _notify_recruiter_response(updated, db)

    return {"id": updated.id, "status": updated.status, "responded_at": updated.responded_at.isoformat()}


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_response(alignment) -> dict:
    return {
        "id": alignment.id,
        "job_vacancy_id": alignment.job_vacancy_id,
        "manager_email": alignment.manager_email,
        "manager_name": alignment.manager_name,
        "status": alignment.status,
        "token": alignment.token,
        "expires_at": alignment.expires_at.isoformat(),
        "created_at": alignment.created_at.isoformat(),
        "public_url": f"/pt/align/{alignment.token}",
    }


async def _fetch_job_summary(job_id: str, company_id: str, db: AsyncSession) -> dict:
    try:
        import uuid as _uuid
        from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository
        repo = JobVacancyCrudRepository(db)
        vacancy = await repo.get_vacancy_by_id_and_company(
            _uuid.UUID(job_id) if len(job_id) == 36 else job_id,
            company_id,
        )
        if vacancy:
            return {
                "id": job_id,
                "title": getattr(vacancy, "title", None),
                "department": getattr(vacancy, "department", None),
                "seniority": getattr(vacancy, "seniority_level", None),
            }
    except Exception as e:
        logger.warning("[Alignment] job summary fetch failed: %s", e)
    return {"id": job_id}


async def _send_alignment_email(alignment, db: AsyncSession) -> None:
    """Send alignment request email to manager. Fire-and-forget — never raises."""
    try:
        from app.domains.communication.services.email_service import MailgunEmailService

        job = await _fetch_job_summary(alignment.job_vacancy_id, alignment.company_id, db)
        job_title = job.get("title", "Vaga")
        manager_greeting = alignment.manager_name or "Gestor(a)"
        # Build absolute URL from env or default
        import os
        base_url = os.getenv("NEXT_PUBLIC_APP_URL", "https://ai.wedotalent.cc")
        public_link = f"{base_url}/pt/align/{alignment.token}"

        subject = f"Alinhamento necessário: {job_title}"
        body_html = (
            f"<p>Olá, {manager_greeting}!</p>"
            f"<p>A equipe de recrutamento da WeDo Talent precisa da sua aprovação para "
            f"iniciar a prospecção de candidatos para a vaga <strong>{job_title}</strong>.</p>"
            f"<p><a href='{public_link}' style='background:#60BED1;color:white;padding:10px 20px;"
            f"border-radius:6px;text-decoration:none;font-weight:600;display:inline-block'>"
            f"Revisar e responder</a></p>"
            f"<p style='color:#9CA3AF;font-size:12px'>Este link expira em "
            f"{alignment.expires_at.strftime('%d/%m/%Y às %H:%M')} (UTC).</p>"
        )
        body_text = (
            f"Olá, {manager_greeting}!\n\n"
            f"Acesse o link para revisar e aprovar a vaga {job_title}:\n{public_link}\n\n"
            f"Expira em {alignment.expires_at.strftime('%d/%m/%Y às %H:%M')} (UTC)."
        )

        svc = MailgunEmailService()
        await svc.send_email(
            to_email=alignment.manager_email,
            to_name=alignment.manager_name,
            subject=subject,
            body=body_text,
            body_html=body_html,
            categories=["alignment-request"],
        )
        logger.info("[Alignment] Email sent to %s for alignment=%s", alignment.manager_email, alignment.id)
    except Exception as e:
        logger.warning("[Alignment] Email send failed (non-blocking): %s", e)


async def _notify_recruiter_response(alignment, db: AsyncSession) -> None:
    """Notify recruiter when manager responds. Fire-and-forget — never raises."""
    try:
        from sqlalchemy import text
        from app.domains.communication.services.email_service import MailgunEmailService

        if not alignment.created_by:
            return

        result = await db.execute(
            text("SELECT email, name FROM users WHERE id = :uid LIMIT 1"),
            {"uid": alignment.created_by},
        )
        row = result.fetchone()
        if not row or not row.email:
            return

        job = await _fetch_job_summary(alignment.job_vacancy_id, alignment.company_id, db)
        job_title = job.get("title", "Vaga")
        status_pt = "aprovada" if alignment.status == "approved" else "não aprovada"
        status_emoji = "✅" if alignment.status == "approved" else "❌"

        subject = f"Alinhamento {status_pt} {status_emoji}: {job_title}"
        body_html = (
            f"<p>Olá, {row.name or 'Recrutador(a)'}!</p>"
            f"<p>O gestor <strong>{alignment.manager_email}</strong> respondeu ao pedido de "
            f"alinhamento para a vaga <strong>{job_title}</strong>.</p>"
            f"<p>Status: <strong>{status_pt} {status_emoji}</strong></p>"
        )
        if alignment.response_notes:
            body_html += f"<p>Observações: <em>{alignment.response_notes}</em></p>"

        svc = MailgunEmailService()
        await svc.send_email(
            to_email=row.email,
            to_name=row.name,
            subject=subject,
            body=f"Alinhamento {status_pt} para vaga {job_title}. Gestor: {alignment.manager_email}",
            body_html=body_html,
            categories=["alignment-response"],
        )
        logger.info("[Alignment] Recruiter notified at %s for alignment=%s", row.email, alignment.id)
    except Exception as e:
        logger.warning("[Alignment] Recruiter notification failed (non-blocking): %s", e)
