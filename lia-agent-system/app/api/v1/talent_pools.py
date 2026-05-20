"""
Talent Pools API endpoints.

CRUD for talent pools and pool candidates, with JSONAPI-style responses
for frontend compatibility.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.models.talent_pool import TalentPool, TalentPoolCandidate
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/talent_pools", tags=["Talent Pools"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class TalentPoolCreate(WeDoBaseModel):
    name: str
    description: str | None = None
    screening_questions: list[dict[str, Any]] | None = None
    screening_config: dict[str, Any] | None = None
    agent_sourcing_enabled: bool = False
    agent_config: dict[str, Any] | None = None


class TalentPoolUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    screening_questions: list[dict[str, Any]] | None = None
    screening_config: dict[str, Any] | None = None
    agent_sourcing_enabled: bool | None = None
    agent_config: dict[str, Any] | None = None


class AddCandidatesRequest(WeDoBaseModel):
    candidate_ids: list[int]
    origin: str = "manual"


class MoveToJobRequest(WeDoBaseModel):
    job_id: int
    candidate_ids: list[int]
    target_stage: str = "applied"


class CreateJobFromPoolRequest(WeDoBaseModel):
    title: str | None = None


# ---------------------------------------------------------------------------
# Response Models (R-028)
# ---------------------------------------------------------------------------

class TalentPoolResponse(BaseModel):
    data: dict[str, Any]


class TalentPoolListResponse(BaseModel):
    data: list[dict[str, Any]]


class TalentPoolCandidateListResponse(BaseModel):
    data: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jsonapi_pool(pool: TalentPool) -> dict:
    """Format a TalentPool as a JSONAPI resource object."""
    d = pool.to_dict()
    pool_id = d.pop("id")
    return {"id": pool_id, "type": "talent_pool", "attributes": d}


def _jsonapi_candidate(c: TalentPoolCandidate) -> dict:
    """Format a TalentPoolCandidate as a JSONAPI resource object."""
    d = c.to_dict()
    cid = d.pop("id")
    return {"id": cid, "type": "talent_pool_candidate", "attributes": d}


async def _get_pool_or_404(
    pool_id: UUID, company_id: str | int, db: AsyncSession
) -> TalentPool:
    result = await db.execute(
        select(TalentPool).where(
            TalentPool.id == pool_id,
            TalentPool.company_id == company_id,
        )
    )
    pool = result.scalars().first()
    if not pool:
        raise HTTPException(status_code=404, detail="Talent pool not found")
    return pool


async def _refresh_counts(pool_id: UUID, db: AsyncSession) -> None:
    """Recalculate aggregate counts on the pool."""
    total = await db.scalar(
        select(func.count()).where(TalentPoolCandidate.talent_pool_id == pool_id)
    )
    screened = await db.scalar(
        select(func.count()).where(
            TalentPoolCandidate.talent_pool_id == pool_id,
            TalentPoolCandidate.stage == "screened",
        )
    )
    ready = await db.scalar(
        select(func.count()).where(
            TalentPoolCandidate.talent_pool_id == pool_id,
            TalentPoolCandidate.stage == "ready",
        )
    )
    await db.execute(
        update(TalentPool)
        .where(TalentPool.id == pool_id)
        .values(
            candidates_count=total or 0,
            screened_count=screened or 0,
            ready_count=ready or 0,
        )
    )


# ---------------------------------------------------------------------------
# Pool CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=TalentPoolListResponse)
async def list_pools(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """List talent pools for the current account."""
    company_id = get_user_company_id(current_user)
    stmt = select(TalentPool).where(
        TalentPool.company_id == company_id,
    ).order_by(TalentPool.created_at.desc())
    if status:
        stmt = stmt.where(TalentPool.status == status)
    result = await db.execute(stmt)
    pools = result.scalars().all()
    return {"data": [_jsonapi_pool(p) for p in pools]}


@router.post("", status_code=201, response_model=TalentPoolResponse)
async def create_pool(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Create a new talent pool."""
    company_id = get_user_company_id(current_user)
    body = payload.get("talent_pool", payload)
    data = TalentPoolCreate(**body)

    pool = TalentPool(
        company_id=company_id,
        name=data.name,
        description=data.description,
        screening_questions=data.screening_questions or [],
        screening_config=data.screening_config or {},
        agent_sourcing_enabled=data.agent_sourcing_enabled,
        agent_config=data.agent_config or {},
    )
    db.add(pool)
    await db.commit()
    await db.refresh(pool)
    return {"data": _jsonapi_pool(pool)}


@router.get("/{pool_id}", response_model=TalentPoolResponse)
async def get_pool(
    pool_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Get a single talent pool."""
    company_id = get_user_company_id(current_user)
    pool = await _get_pool_or_404(pool_id, company_id, db)
    return {"data": _jsonapi_pool(pool)}


@router.patch("/{pool_id}")
async def update_pool(
    pool_id: UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Update a talent pool."""
    company_id = get_user_company_id(current_user)
    pool = await _get_pool_or_404(pool_id, company_id, db)
    body = payload.get("talent_pool", payload)
    updates = TalentPoolUpdate(**body)

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(pool, field, value)

    await db.commit()
    await db.refresh(pool)
    return {"data": _jsonapi_pool(pool)}


@router.delete("/{pool_id}")
async def delete_pool(
    pool_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Soft-delete (archive) a talent pool."""
    company_id = get_user_company_id(current_user)
    pool = await _get_pool_or_404(pool_id, company_id, db)
    pool.status = "archived"
    await db.commit()
    return {"data": _jsonapi_pool(pool)}


# ---------------------------------------------------------------------------
# Candidate operations
# ---------------------------------------------------------------------------

@router.get("/{pool_id}/candidates", response_model=TalentPoolCandidateListResponse)
async def list_candidates(
    pool_id: UUID,
    stage: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """List candidates in a talent pool."""
    company_id = get_user_company_id(current_user)
    await _get_pool_or_404(pool_id, company_id, db)

    stmt = select(TalentPoolCandidate).where(
        TalentPoolCandidate.talent_pool_id == pool_id,
    ).order_by(TalentPoolCandidate.created_at.desc())
    if stage:
        stmt = stmt.where(TalentPoolCandidate.stage == stage)

    result = await db.execute(stmt)
    candidates = result.scalars().all()
    return {"data": [_jsonapi_candidate(c) for c in candidates]}


@router.post("/{pool_id}/add_candidates", status_code=201)
async def add_candidates(
    pool_id: UUID,
    payload: AddCandidatesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Add candidates to a talent pool."""
    company_id = get_user_company_id(current_user)
    await _get_pool_or_404(pool_id, company_id, db)

    added = []
    skipped = []
    for cid in payload.candidate_ids:
        # Check for existing entry
        existing = await db.execute(
            select(TalentPoolCandidate).where(
                TalentPoolCandidate.talent_pool_id == pool_id,
                TalentPoolCandidate.candidate_id == cid,
            )
        )
        if existing.scalars().first():
            skipped.append(cid)
            continue

        candidate = TalentPoolCandidate(
            talent_pool_id=pool_id,
            candidate_id=cid,
            origin=payload.origin,
        )
        db.add(candidate)
        added.append(cid)

    await _refresh_counts(pool_id, db)
    await db.commit()

    return {
        "data": {"added": added, "skipped": skipped, "total_added": len(added)},
    }


@router.post("/{pool_id}/move_to_job")
async def move_to_job(
    pool_id: UUID,
    payload: MoveToJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Move candidates from pool to a job vacancy."""
    company_id = get_user_company_id(current_user)
    await _get_pool_or_404(pool_id, company_id, db)

    moved = []
    now = datetime.utcnow()
    for cid in payload.candidate_ids:
        result = await db.execute(
            select(TalentPoolCandidate).where(
                TalentPoolCandidate.talent_pool_id == pool_id,
                TalentPoolCandidate.candidate_id == cid,
            )
        )
        entry = result.scalars().first()
        if entry:
            entry.moved_to_job_id = payload.job_id
            entry.moved_at = now
            entry.moved_to_stage = payload.target_stage
            moved.append(cid)

    await db.commit()
    return {
        "data": {
            "moved": moved,
            "job_id": payload.job_id,
            "target_stage": payload.target_stage,
        },
    }


@router.post("/{pool_id}/create_job_from_pool")
async def create_job_from_pool(
    pool_id: UUID,
    payload: CreateJobFromPoolRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Placeholder — job creation requires Rails integration."""
    company_id = get_user_company_id(current_user)
    await _get_pool_or_404(pool_id, company_id, db)
    return {
        "job_id": None,
        "message": "Job creation requires Rails integration",
    }
