"""
Job Offers API — draft/send/respond lifecycle for candidate offers.

Three endpoints:
  GET    /job-offers              — list offers for company (authenticated)
  POST   /job-offers              — create a draft offer (authenticated)
  PATCH  /job-offers/{id}/send    — send offer to candidate (authenticated)
  PATCH  /job-offers/{id}/respond — record candidate response (authenticated)
  PATCH  /job-offers/{id}/withdraw — withdraw offer (authenticated)
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.repositories.job_offer_repository import JobOfferRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-offers", tags=["Job Offers"])


# ── Schemas ────────────────────────────────────────────────────────────────

class CreateOfferRequest(BaseModel):
    job_vacancy_id: str
    candidate_id: str
    salary: Optional[float] = None
    currency: str = Field("BRL", max_length=10)
    start_date: Optional[date] = None
    notes: Optional[str] = None

    model_config = {"extra": "forbid"}


class RespondOfferRequest(BaseModel):
    response: str = Field(..., pattern="^(accepted|rejected)$")
    response_notes: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_response(offer) -> dict:
    return {
        "id": offer.id,
        "job_vacancy_id": offer.job_vacancy_id,
        "candidate_id": offer.candidate_id,
        "salary": float(offer.salary) if offer.salary is not None else None,
        "currency": offer.currency,
        "start_date": offer.start_date.isoformat() if offer.start_date else None,
        "notes": offer.notes,
        "status": offer.status,
        "sent_at": offer.sent_at.isoformat() if offer.sent_at else None,
        "responded_at": offer.responded_at.isoformat() if offer.responded_at else None,
        "candidate_response": offer.candidate_response,
        "response_notes": offer.response_notes,
        "requires_manager_approval": offer.requires_manager_approval,
        "manager_approved_at": offer.manager_approved_at.isoformat() if offer.manager_approved_at else None,
        "created_at": offer.created_at.isoformat(),
    }


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("")
async def list_offers(
    job_vacancy_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List offers for the current company, optionally filtered by job or status."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"offers": []}

    repo = JobOfferRepository(db)
    if job_vacancy_id:
        offers = await repo.list_for_job(company_id, job_vacancy_id, status=status, limit=limit)
    else:
        offers = await repo.list_for_company(company_id, status=status, limit=limit)

    return {"offers": [_to_response(o) for o in offers]}


@router.post("", status_code=201)
async def create_offer(
    payload: CreateOfferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft offer for a candidate."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(403, "company_id not found in token")

    repo = JobOfferRepository(db)
    offer = await repo.create(
        company_id=company_id,
        job_vacancy_id=payload.job_vacancy_id,
        candidate_id=payload.candidate_id,
        created_by=str(getattr(current_user, "id", "")),
        salary=payload.salary,
        currency=payload.currency,
        start_date=payload.start_date,
        notes=payload.notes,
    )
    await db.commit()

    logger.info("[Offer] Created offer=%s job=%s candidate=%s", offer.id, payload.job_vacancy_id, payload.candidate_id)
    return _to_response(offer)


@router.patch("/{offer_id}/send")
async def send_offer(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Advance offer from draft → sent."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(403, "company_id not found in token")

    repo = JobOfferRepository(db)
    offer = await repo.get_by_id(company_id, offer_id)
    if not offer:
        raise HTTPException(404, "Oferta não encontrada")
    if offer.status != "draft":
        raise HTTPException(409, f"Oferta já está com status: {offer.status}")

    updated = await repo.send(offer)
    await db.commit()

    logger.info("[Offer] Sent offer=%s", offer_id)
    return _to_response(updated)


@router.patch("/{offer_id}/respond")
async def respond_to_offer(
    offer_id: str,
    payload: RespondOfferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record candidate response: accepted or rejected."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(403, "company_id not found in token")

    repo = JobOfferRepository(db)
    offer = await repo.get_by_id(company_id, offer_id)
    if not offer:
        raise HTTPException(404, "Oferta não encontrada")
    if offer.status != "sent":
        raise HTTPException(409, f"Oferta não está no estado 'sent' (atual: {offer.status})")

    updated = await repo.record_response(offer, payload.response, payload.response_notes)
    await db.commit()

    logger.info("[Offer] Response recorded offer=%s response=%s", offer_id, payload.response)
    return _to_response(updated)


@router.patch("/{offer_id}/withdraw")
async def withdraw_offer(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw an offer (draft or sent)."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(403, "company_id not found in token")

    repo = JobOfferRepository(db)
    offer = await repo.get_by_id(company_id, offer_id)
    if not offer:
        raise HTTPException(404, "Oferta não encontrada")
    if offer.status not in ("draft", "sent"):
        raise HTTPException(409, f"Não é possível retirar oferta com status: {offer.status}")

    updated = await repo.withdraw(offer)
    await db.commit()

    logger.info("[Offer] Withdrawn offer=%s", offer_id)
    return _to_response(updated)
