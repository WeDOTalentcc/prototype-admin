"""
Recruitment Campaigns API endpoints.

Phase 2 implementation: replaces 501 stubs with real DB-backed CRUD.
All endpoints are multi-tenancy fail-closed via require_company_id.
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.repositories.campaign_repository import CampaignRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from fastapi import Path
from lia_models.recruitment_campaign import DEFAULT_CAMPAIGN_STAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruitment_campaigns", tags=["Recruitment Campaigns"])


# ── Schemas ────────────────────────────────────────────────────────────────

class CampaignCreate(WeDoBaseModel):
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    job_id: str | None = None
    talent_pool_id: str | None = None
    automation_level: str = "semi"
    stages: list[dict] | None = None


class CampaignUpdate(WeDoBaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    status: str | None = None
    automation_level: str | None = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _serialize(campaign) -> dict:
    """Serialize to the JSONAPI envelope consumed by the frontend."""
    stages_raw = campaign.stages or []
    current_idx = campaign.current_stage_index or 0
    campaign_status = campaign.status or "active"
    all_completed = campaign_status == "completed"

    _LABEL_MAP = {
        "sourcing": "Sourcing",
        "screening": "Triagem",
        "outreach": "Contato",
        "interview": "Entrevista",
        "evaluation": "Avaliação",
        "offer": "Oferta",
    }

    projected_stages = []
    for i, stage in enumerate(stages_raw):
        name = stage.get("name", "") if isinstance(stage, dict) else ""
        label = _LABEL_MAP.get(name, name.replace("_", " ").title())
        if all_completed:
            status = "completed"
        elif i < current_idx:
            status = "completed"
        elif i == current_idx:
            status = "in_progress"
        else:
            status = "pending"
        projected_stages.append({"name": name, "label": label, "status": status})

    progress_pct = 0.0
    if stages_raw:
        if all_completed:
            progress_pct = 100.0
        else:
            progress_pct = round((current_idx / len(stages_raw)) * 100, 1)

    created_at = campaign.created_at
    updated_at = campaign.updated_at

    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "description": campaign.description,
        "status": campaign.status,
        "job_id": campaign.job_id,
        "talent_pool_id": campaign.talent_pool_id,
        "automation_level": campaign.automation_level,
        "current_stage_index": current_idx,
        "current_stage": stages_raw[current_idx].get("name") if stages_raw and 0 <= current_idx < len(stages_raw) else None,
        "stages": projected_stages,
        "progress_pct": progress_pct,
        "total_candidates": campaign.total_candidates or 0,
        "candidates_screened": campaign.candidates_screened or 0,
        "candidates_contacted": campaign.candidates_contacted or 0,
        "candidates_interviewed": campaign.candidates_interviewed or 0,
        "candidates_offered": campaign.candidates_offered or 0,
        "candidates_hired": campaign.candidates_hired or 0,
        "created_by": campaign.created_by,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("")
async def list_campaigns(
    status: str | None = Query(None),
    job_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    repo = CampaignRepository(db)
    campaigns, total = await repo.list_by_company(
        company_id=company_id,
        status=status,
        job_id=job_id,
        limit=limit,
        offset=offset,
    )
    return {
        "data": [_serialize(c) for c in campaigns],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", status_code=201)
async def create_campaign(
    payload: CampaignCreate,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    from app.services.quota_enforcement import enforce_quota
    await enforce_quota("campaigns", company_id, db)

    stages = payload.stages if payload.stages is not None else list(DEFAULT_CAMPAIGN_STAGES)
    repo = CampaignRepository(db)
    campaign = await repo.create({
        "company_id": company_id,
        "created_by": current_user.email or current_user.id or "system",
        "name": payload.name,
        "description": payload.description,
        "job_id": payload.job_id,
        "talent_pool_id": payload.talent_pool_id,
        "automation_level": payload.automation_level,
        "stages": stages,
        "current_stage_index": 0,
        "status": "active",
    })
    await db.commit()
    return _serialize(campaign)


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    repo = CampaignRepository(db)
    try:
        cid = UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = await repo.get_by_id(cid, company_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _serialize(campaign)


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: CampaignUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    repo = CampaignRepository(db)
    try:
        cid = UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Campaign not found")
    updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    campaign = await repo.update(cid, company_id, updates)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await db.commit()
    return _serialize(campaign)


@router.post("/{campaign_id}/advance-stage")
async def advance_stage(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict | None = None,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    repo = CampaignRepository(db)
    try:
        cid = UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = await repo.advance_stage(cid, company_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await db.commit()
    return _serialize(campaign)


@router.post("/{campaign_id}/complete-stage", status_code=501)
async def complete_stage(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict | None = None,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    return {"status": "not_implemented", "message": "Use advance-stage to progress the campaign."}


@router.post("/{campaign_id}/add-checkpoint", status_code=501)
async def add_checkpoint(
    campaign_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict | None = None,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    return {"status": "not_implemented", "message": "Checkpoint support coming in Phase 3."}


reorder_collection_before_item(router)
