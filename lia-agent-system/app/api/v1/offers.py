"""
REST endpoints for offer proposals.

Routes:
  POST   /api/v1/offers/drafts                  create/get draft
  GET    /api/v1/offers/drafts/{id}              get draft
  PATCH  /api/v1/offers/drafts/{id}              update fields
  POST   /api/v1/offers/drafts/{id}/send-auto    send automatically
  POST   /api/v1/offers/drafts/{id}/prepare-manual  prepare for manual send
  DELETE /api/v1/offers/drafts/{id}              cancel
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.auth.dependencies import get_current_user
from app.schemas.offer import (
    OfferCancelRequest,
    OfferDraftCreate,
    OfferDraftResponse,
    OfferDraftListResponse,
    OfferDraftUpdate,
    OfferPrepareManualResponse,
    OfferSendAutoResponse,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter(prefix="/offers", tags=["offers"])
logger = logging.getLogger(__name__)


@router.get("/drafts", response_model=OfferDraftListResponse)
async def list_offer_drafts(
    job_vacancy_id: UUID = Query(..., description="Filter by job vacancy"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
    company_id: str = Depends(require_company_id),
):
    """List all offer proposals for a job vacancy (multi-tenant scoped)."""
    company_id = current_user.company_id
    from app.domains.offer.repositories.offer_repository import OfferRepository
    repo = OfferRepository(db)
    proposals = await repo.list_by_job(company_id, job_vacancy_id, limit=limit)
    items = [OfferDraftResponse.model_validate(p) for p in proposals]
    return OfferDraftListResponse(offers=items)


@router.post("/drafts", response_model=OfferDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_offer_draft(
    data: OfferDraftCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create offer draft (or return existing draft for same candidate+job)."""
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id missing from auth token")

    # Fetch snapshots
    from app.domains.offer.tools.create_offer_draft import _fetch_job_snapshot, _fetch_candidate_snapshot
    from app.domains.base import DomainContext
    ctx = DomainContext(
        domain_id="offer",
        session_id=str(current_user.id),
        user_id=current_user.id,
        tenant_id=company_id,
        metadata={"auth_token": getattr(current_user, "_raw_token", "")},
    )
    job_snapshot = await _fetch_job_snapshot(data.job_id, company_id, ctx)
    candidate_snapshot = await _fetch_candidate_snapshot(str(data.candidate_id), company_id, ctx)

    from app.domains.offer.services.offer_service import OfferService
    svc = OfferService(db)
    draft = await svc.create_or_get_draft(
        data=data,
        company_id=company_id,
        user_id=current_user.id,
        job_snapshot=job_snapshot,
        candidate_snapshot=candidate_snapshot,
    )
    await db.commit()
    return draft


@router.get("/drafts/{offer_id}", response_model=OfferDraftResponse)
async def get_offer_draft(
    offer_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.domains.offer.services.offer_service import OfferService
    company_id = current_user.company_id
    svc = OfferService(db)
    draft = await svc.get_draft(offer_id, company_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Proposta nao encontrada")
    return draft


@router.patch("/drafts/{offer_id}", response_model=OfferDraftResponse)
async def update_offer_draft(
    offer_id: UUID,
    data: OfferDraftUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.domains.offer.services.offer_service import OfferService
    company_id = current_user.company_id
    svc = OfferService(db)
    try:
        draft = await svc.update_draft(offer_id, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not draft:
        raise HTTPException(status_code=404, detail="Proposta nao encontrada")
    await db.commit()
    return draft


@router.post("/drafts/{offer_id}/send-auto", response_model=OfferSendAutoResponse)
async def send_offer_auto(
    offer_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Send offer automatically via email template."""
    from app.domains.offer.tools.send_offer import run as send_run
    from app.domains.base import DomainContext
    company_id = current_user.company_id
    ctx = DomainContext(
        domain_id="offer",
        session_id=str(current_user.id),
        user_id=current_user.id,
        tenant_id=company_id,
        metadata={"auth_token": getattr(current_user, "_raw_token", "")},
    )
    result = await send_run({"offer_id": str(offer_id)}, ctx)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Send failed"))
    from datetime import datetime
    from uuid import UUID as _UUID
    return OfferSendAutoResponse(
        offer_id=offer_id,
        status="sent",
        email_log_id=_UUID(result["email_log_id"]) if result.get("email_log_id") else None,
        sent_at=datetime.utcnow(),
        message=result.get("message", "Enviado"),
        offer_link=result.get("offer_link"),
    )


@router.post("/drafts/{offer_id}/prepare-manual", response_model=OfferPrepareManualResponse)
async def prepare_offer_manual(
    offer_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.domains.offer.tools.prepare_offer_manual_send import run as prep_run
    from app.domains.base import DomainContext
    company_id = current_user.company_id
    ctx = DomainContext(
        domain_id="offer",
        session_id=str(current_user.id),
        user_id=current_user.id,
        tenant_id=company_id,
        metadata={"auth_token": getattr(current_user, "_raw_token", "")},
    )
    result = await prep_run({"offer_id": str(offer_id)}, ctx)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Prep failed"))
    return OfferPrepareManualResponse(
        offer_id=offer_id,
        template_id=result.get("template_id"),
        subject_pre_filled=result["subject_pre_filled"],
        body_pre_filled=result["body_pre_filled"],
        variables=result["variables"],
        message=result["message"],
    )


@router.delete("/drafts/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_offer_draft(
    offer_id: UUID,
    body: OfferCancelRequest | None = None,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.domains.offer.services.offer_service import OfferService
    company_id = current_user.company_id
    svc = OfferService(db)
    try:
        cancelled = await svc.cancel_draft(
            offer_id, company_id, current_user.id,
            reason=body.reason if body else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not cancelled:
        raise HTTPException(status_code=404, detail="Proposta nao encontrada")
    await db.commit()


class OfferStatusResponse(BaseModel):
    offer_id: UUID
    status: str
    sent_at: "datetime | None" = None
    candidate_viewed_at: "datetime | None" = None
    accepted_at: "datetime | None" = None
    declined_at: "datetime | None" = None
    response_deadline: "datetime | None" = None
    offer_link: str | None = None


@router.get("/drafts/{offer_id}/status", response_model=OfferStatusResponse)
async def get_offer_status(
    offer_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: company_id from current_user (sensor false positive)
    """Lightweight status endpoint — polled by OfferStatusTracker FE component."""
    from app.domains.offer.services.offer_service import OfferService
    company_id = current_user.company_id
    svc = OfferService(db)
    proposal = await svc.get_draft(offer_id, company_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta nao encontrada")
    return OfferStatusResponse(
        offer_id=proposal.id,
        status=proposal.status,
        sent_at=proposal.sent_at,
        candidate_viewed_at=proposal.candidate_viewed_at,
        accepted_at=proposal.accepted_at,
        declined_at=proposal.declined_at,
        response_deadline=proposal.response_deadline,
        offer_link=proposal.acceptance_url,
    )


@router.get("/by-candidate/{candidate_id}", response_model=OfferStatusResponse | None)
async def get_offer_by_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: company_id from current_user (sensor false positive)
    """Latest offer for a candidate — polled by OfferStatusBadge in kanban."""
    from app.domains.offer.repositories.offer_repository import OfferRepository
    company_id = current_user.company_id
    repo = OfferRepository(db)
    proposals = await repo.list_by_candidate(company_id, candidate_id)
    if not proposals:
        return None
    # Prefer most-recent non-draft (sent/accepted/etc)
    proposal = next((p for p in proposals if p.status != "draft"), proposals[0])
    return OfferStatusResponse(
        offer_id=proposal.id,
        status=proposal.status,
        sent_at=proposal.sent_at,
        candidate_viewed_at=proposal.candidate_viewed_at,
        accepted_at=proposal.accepted_at,
        declined_at=proposal.declined_at,
        response_deadline=proposal.response_deadline,
        offer_link=proposal.acceptance_url,
    )
