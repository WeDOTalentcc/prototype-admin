"""Job Readiness Hub API (Task #429).

Endpoints under ``/api/v1/job-readiness`` for the recruiter Hub. Every
handler is scoped by ``company_id`` from the authenticated user — no
cross-tenant leakage (regression guard for tasks #5 / #329 / #330).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.domains.job_management.services.job_audit_service import JobAuditService
from app.domains.job_management.services.job_readiness_service import (
    AUDIENCE_POLICIES,
    CANONICAL_STAGES,
    HITL_STAGES,
    JobReadinessService,
    NEXT_ACTION_BY_STAGE,
    STAGE_LABELS_PT,
    classify,
    compute_blockers,
    next_action,
    requires_human,
)
from app.shared.async_processing.task_manager import DomainTaskManager
from lia_models.job_vacancy import JobVacancy
from lia_models.job_vacancy_audit import JobVacancyAuditLog
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCrudRepository,
)
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCrudRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-readiness", tags=["job-readiness"])


# ── Schemas ─────────────────────────────────────────────────────────────────

class StageCount(BaseModel):
    stage: str
    label: str
    count: int
    requires_human: bool


class OverviewResponse(BaseModel):
    total: int
    by_stage: list[StageCount]
    action_required: int
    queued_actions: int
    last_event_at: Optional[str] = None


class JobCard(BaseModel):
    id: str
    title: str
    job_id: Optional[str] = None
    department: Optional[str] = None
    source_system: Optional[str] = None
    status: Optional[str] = None
    readiness_stage: str
    readiness_label: str
    readiness_blockers: list[str] = []
    requires_human: bool
    next_action: Optional[str] = None
    last_event_at: Optional[str] = None


class BoardResponse(BaseModel):
    total: int
    items: list[JobCard]


class TimelineEvent(BaseModel):
    id: str
    at: str
    actor: str
    action: str
    field: Optional[str] = None
    summary: str
    old_value: Any | None = None
    new_value: Any | None = None


class JobDetailResponse(JobCard):
    description: Optional[str] = None
    enriched_jd: Optional[dict] = None
    behavioral_competencies: list[Any] = []
    screening_questions: list[Any] = []
    assigned_audience_policy: Optional[str] = None
    timeline: list[TimelineEvent] = []


class RunRequest(WeDoBaseModel):
    job_ids: list[UUID] = Field(default_factory=list, max_length=200)


class RunResponse(BaseModel):
    enqueued: list[str]
    skipped_human_required: list[str]
    errors: list[dict]
    total: int


class StageActionRequest(WeDoBaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


class DispatchRequest(WeDoBaseModel):
    audience_policy: str


# ── Helpers ─────────────────────────────────────────────────────────────────

def _service(db: AsyncSession) -> JobReadinessService:
    try:
        tm = DomainTaskManager.get_instance()
    except Exception:  # noqa: BLE001
        tm = None
    return JobReadinessService(db, audit_service=JobAuditService(), task_manager=tm)


async def _load_job(db: AsyncSession, job_id: UUID, company_id: str) -> JobVacancy:
    res = await db.execute(
        select(JobVacancy).where(
            JobVacancy.id == job_id,
            JobVacancy.company_id == company_id,
        )
    )
    job = res.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


def _to_card(job: JobVacancy) -> JobCard:
    stage = job.readiness_stage or classify(job)
    return JobCard(
        id=str(job.id),
        title=job.title or "(sem título)",
        job_id=job.job_id,
        department=job.department,
        source_system=job.source_system,
        status=job.status,
        readiness_stage=stage,
        readiness_label=STAGE_LABELS_PT.get(stage, stage),
        readiness_blockers=list(job.readiness_blockers or []),
        requires_human=stage in HITL_STAGES,
        next_action=NEXT_ACTION_BY_STAGE.get(stage),
        last_event_at=job.last_readiness_event_at.isoformat() if job.last_readiness_event_at else None,
    )


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/overview", response_model=OverviewResponse)
async def overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> OverviewResponse:
    company_id = get_user_company_id(user)

    rows = await db.execute(
        select(
            JobVacancy.readiness_stage,
            func.count(JobVacancy.id),
        )
        .where(JobVacancy.company_id == company_id)
        .group_by(JobVacancy.readiness_stage)
    )
    counts: dict[str, int] = {}
    total = 0
    for stage, n in rows.all():
        n = int(n or 0)
        total += n
        counts[stage or "importada"] = counts.get(stage or "importada", 0) + n

    by_stage = [
        StageCount(
            stage=s,
            label=STAGE_LABELS_PT[s],
            count=counts.get(s, 0),
            requires_human=s in HITL_STAGES,
        )
        for s in CANONICAL_STAGES
    ]
    action_required = sum(c.count for c in by_stage if c.requires_human)
    queued_actions = sum(
        c.count for c in by_stage
        if NEXT_ACTION_BY_STAGE.get(c.stage) is not None
    )

    last_event_row = await db.execute(
        select(func.max(JobVacancy.last_readiness_event_at))
        .where(JobVacancy.company_id == company_id)
    )
    last_event = last_event_row.scalar_one_or_none()
    return OverviewResponse(
        total=total,
        by_stage=by_stage,
        action_required=action_required,
        queued_actions=queued_actions,
        last_event_at=last_event.isoformat() if last_event else None,
    )


@router.get("/board", response_model=BoardResponse)
async def board(
    stage: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> BoardResponse:
    company_id = get_user_company_id(user)

    from sqlalchemy import and_, or_

    filters = [JobVacancy.company_id == company_id]
    if stage:
        if stage not in CANONICAL_STAGES:
            raise HTTPException(status_code=400, detail=f"invalid stage {stage!r}")
        filters.append(JobVacancy.readiness_stage == stage)
    if search and len(search.strip()) >= 2:
        like = f"%{search.strip()}%"
        filters.append(or_(JobVacancy.title.ilike(like), JobVacancy.job_id.ilike(like)))

    # TENANT-EXEMPT: filters list built dynamically above with
    # JobVacancy.company_id == company_id as first filter (sensor AST cannot follow
    # indirection); endpoint gated via Depends(require_company_id)
    stmt = (
        select(JobVacancy)
        .where(and_(*filters))
        .order_by(
            JobVacancy.last_readiness_event_at.desc().nullslast(),
            JobVacancy.created_at.desc(),
        )
        .offset(skip)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()

    # Total count uses the same filters (including search) but no offset/limit.
    count_stmt = select(func.count(JobVacancy.id)).where(and_(*filters))
    total = (await db.execute(count_stmt)).scalar() or 0

    return BoardResponse(total=int(total), items=[_to_card(r) for r in rows])


def _summarize_audit(row: JobVacancyAuditLog) -> str:
    field = row.field_changed or ""
    if field == "readiness_stage":
        old = (row.old_value or {}).get("old") if isinstance(row.old_value, dict) else row.old_value
        new = (row.new_value or {}).get("new") if isinstance(row.new_value, dict) else row.new_value
        if old or new:
            return f"Estágio: {old or '—'} → {new or '—'}"
    if row.action:
        return f"{row.action}{f' · {field}' if field else ''}"
    return field or "evento"


async def _load_timeline(
    db: AsyncSession, job_id: UUID, company_id: str, limit: int = 50,
) -> list[TimelineEvent]:
    """Load the most recent audit-log entries for this job, tenant-scoped."""
    try:
        res = await db.execute(
            select(JobVacancyAuditLog)
            .where(
                JobVacancyAuditLog.job_vacancy_id == job_id,
                JobVacancyAuditLog.company_id == company_id,
            )
            .order_by(JobVacancyAuditLog.changed_at.desc())
            .limit(limit)
        )
        rows = res.scalars().all()
    except Exception as exc:  # noqa: BLE001 — timeline is best-effort
        logger.debug("[job-readiness] timeline load skipped: %s", exc)
        return []

    out: list[TimelineEvent] = []
    for row in rows:
        out.append(TimelineEvent(
            id=str(row.id),
            at=row.changed_at.isoformat() if row.changed_at else "",
            actor=row.changed_by or "—",
            action=row.action or "",
            field=row.field_changed,
            summary=_summarize_audit(row),
            old_value=row.old_value,
            new_value=row.new_value,
        ))
    return out


@router.get("/job/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(
    job_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> JobDetailResponse:
    company_id = get_user_company_id(user)
    job = await _load_job(db, job_id, company_id)
    timeline = await _load_timeline(db, job_id, company_id)
    card = _to_card(job).model_dump()
    return JobDetailResponse(
        **card,
        description=job.description,
        enriched_jd=job.enriched_jd,
        behavioral_competencies=list(job.behavioral_competencies or []),
        screening_questions=list(job.screening_questions or []),
        assigned_audience_policy=job.assigned_audience_policy,
        timeline=timeline,
    )


@router.post("/run-all", response_model=RunResponse)
async def run_all(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> RunResponse:
    company_id = get_user_company_id(user)
    actor = (user.email or str(user.id)) if user else "lia"

    # Only enqueue rows that have an automatable next action.
    # Include rows whose readiness_stage is NULL (e.g. just imported, not yet
    # backfilled / reclassified) — the service's classifier handles them.
    actionable_stages = [s for s, a in NEXT_ACTION_BY_STAGE.items() if a is not None]
    from sqlalchemy import or_
    res = await db.execute(
        select(JobVacancy).where(
            JobVacancy.company_id == company_id,
            or_(
                JobVacancy.readiness_stage.in_(actionable_stages),
                JobVacancy.readiness_stage.is_(None),
            ),
        )
    )
    jobs = res.scalars().all()
    # Reclassify lazy/null rows in-memory so run_batch sees the right stage
    # (avoids enqueueing a no-op for rows that are actually HITL-gated).
    svc = _service(db)
    actionable: list[JobVacancy] = []
    for j in jobs:
        if not j.readiness_stage:
            await svc.reclassify_and_persist(j, actor=actor)
        if next_action(j) is not None:
            actionable.append(j)
    summary = await svc.run_batch(actionable, actor=actor)
    await db.commit()
    return RunResponse(**summary)


@router.post("/run-batch", response_model=RunResponse)
async def run_batch(
    payload: RunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> RunResponse:
    if not payload.job_ids:
        raise HTTPException(status_code=400, detail="job_ids must not be empty")
    company_id = get_user_company_id(user)
    actor = (user.email or str(user.id)) if user else "lia"

    res = await db.execute(
        select(JobVacancy).where(
            JobVacancy.company_id == company_id,
            JobVacancy.id.in_([str(j) for j in payload.job_ids]),
        )
    )
    jobs = res.scalars().all()
    if len(jobs) != len(payload.job_ids):
        # Silently dropping IDs that don't belong to the tenant is the right
        # multi-tenant behavior — never confirm or deny existence cross-tenant.
        logger.info(
            "[job-readiness] run_batch: %d/%d ids resolved for company=%s",
            len(jobs), len(payload.job_ids), company_id,
        )
    summary = await _service(db).run_batch(jobs, actor=actor)
    await db.commit()
    return RunResponse(**summary)


@router.post("/job/{job_id}/approve-stage", response_model=JobDetailResponse)
async def approve_stage(
    job_id: UUID,
    payload: StageActionRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> JobDetailResponse:
    company_id = get_user_company_id(user)
    actor = (user.email or str(user.id)) if user else "recruiter"
    job = await _load_job(db, job_id, company_id)
    try:
        job = await _service(db).approve_stage(job, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return await get_job_detail(job_id, user=user, db=db)


@router.post("/job/{job_id}/reject-stage", response_model=JobDetailResponse)
async def reject_stage(
    job_id: UUID,
    payload: StageActionRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> JobDetailResponse:
    company_id = get_user_company_id(user)
    actor = (user.email or str(user.id)) if user else "recruiter"
    job = await _load_job(db, job_id, company_id)
    reason = (payload.reason if payload else None) or ""
    try:
        job = await _service(db).reject_stage(job, actor=actor, reason=reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return await get_job_detail(job_id, user=user, db=db)


@router.post("/job/{job_id}/dispatch-screening", response_model=JobDetailResponse)
async def dispatch_screening(
    job_id: UUID,
    payload: DispatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> JobDetailResponse:
    company_id = get_user_company_id(user)
    actor = (user.email or str(user.id)) if user else "recruiter"
    job = await _load_job(db, job_id, company_id)
    try:
        job = await _service(db).dispatch_screening(
            job,
            actor=actor,
            audience_policy=payload.audience_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return await get_job_detail(job_id, user=user, db=db)

@router.post("/job/{job_id}/reactivate")
async def reactivate_job_vacancy(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Reactivate a closed vacancy back to Ativa status."""
    vacancy = await JobVacancyCrudRepository(db).get_vacancy_by_id_and_company(job_id, company_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    if vacancy.status not in ("Concluída", "Cancelada", "Arquivada", "Pausada"):
        raise HTTPException(
            status_code=422,
            detail=f"Cannot reactivate vacancy in status '{vacancy.status}'",
        )
    vacancy.status = "Ativa"
    await db.commit()
    await db.refresh(vacancy)
    return {"success": True, "job_id": job_id, "new_status": "Ativa"}
