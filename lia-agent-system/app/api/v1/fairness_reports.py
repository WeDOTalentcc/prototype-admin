
"""
FairnessGuard reports API — EU AI Act compliance reporting.

Endpoints:
- GET /fairness/reports/summary   — hits por categoria (últimos N dias)
- GET /fairness/reports/trend     — série temporal de bloqueios
- GET /fairness/audit/logs        — audit trail paginado (FAR-2/B)
"""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.domains.analytics.repositories.fairness_report_repository import FairnessReportRepository
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

router = APIRouter(prefix="/fairness", tags=["fairness-reports"])


class FairnessCategorySummary(BaseModel):
    category: str
    total_blocks: int
    total_warnings: int
    last_occurrence: datetime | None


class FairnessSummaryResponse(BaseModel):
    period_days: int
    company_id: str | None
    total_blocks: int
    total_events: int
    by_category: list[FairnessCategorySummary]


class FairnessTrendPoint(BaseModel):
    date: str  # ISO date YYYY-MM-DD
    blocks: int
    warnings: int


class FairnessTrendResponse(BaseModel):
    period_days: int
    company_id: str | None
    trend: list[FairnessTrendPoint]


@router.get("/reports/summary", response_model=FairnessSummaryResponse)
# TODO(phase2): extract to repository — complex fairness aggregation
async def get_fairness_summary(
    company_id: str | None = Query(None, description="Filter by company UUID"),
    days: int = Query(30, ge=1, le=365, description="Look-back period in days"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Summary of FairnessGuard events grouped by bias category.

    Returns total blocks and warnings per category for the specified period.
    Useful for recruiter coaching and compliance dashboards.
    """
    since = datetime.now(UTC) - timedelta(days=days)
    repo = FairnessReportRepository(db)
    rows = await repo.get_summary_by_category(since, company_id)

    total_blocks = sum(r.blocks for r in rows)
    total_events = sum(r.blocks + r.warnings for r in rows)

    by_category = [
        FairnessCategorySummary(
            category=r.category or "unknown",
            total_blocks=r.blocks,
            total_warnings=r.warnings,
            last_occurrence=r.last_occurrence,
        )
        for r in rows
    ]
    by_category.sort(key=lambda x: x.total_blocks, reverse=True)

    return FairnessSummaryResponse(
        period_days=days,
        company_id=company_id,
        total_blocks=total_blocks,
        total_events=total_events,
        by_category=by_category,
    )


@router.get("/reports/trend", response_model=FairnessTrendResponse)
async def get_fairness_trend(
    company_id: str | None = Query(None, description="Filter by company UUID"),
    days: int = Query(90, ge=7, le=365, description="Look-back period in days"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Daily trend of FairnessGuard events over time.

    Returns a time-series suitable for charting bias detection trends.
    Useful for identifying if training/coaching is reducing discrimination attempts.
    """
    since = datetime.now(UTC) - timedelta(days=days)
    repo = FairnessReportRepository(db)
    rows = await repo.get_daily_trend(since, company_id)

    trend = [
        FairnessTrendPoint(
            date=str(r.day),
            blocks=r.blocks,
            warnings=r.warnings,
        )
        for r in rows
    ]

    return FairnessTrendResponse(
        period_days=days,
        company_id=company_id,
        trend=trend,
    )


class FairnessAuditLogEntry(BaseModel):
    id: str
    category: str | None
    is_blocked: bool
    blocked_terms: list[str] | None
    soft_warnings: list[str] | None
    context: str | None
    recruiter_id: str | None
    job_id: str | None
    created_at: datetime


class FairnessAuditLogsResponse(BaseModel):
    company_id: str | None
    total: int
    limit: int
    offset: int
    items: list[FairnessAuditLogEntry]


@router.get("/audit/logs", response_model=FairnessAuditLogsResponse)
async def get_fairness_audit_logs(
    company_id: str | None = Query(None, description="Filter by company UUID"),
    category: str | None = Query(None, description="Filter by bias category"),
    blocked_only: bool = Query(False, description="Return only blocked events"),
    days: int = Query(30, ge=1, le=365, description="Look-back period in days"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Paginado audit trail do FairnessGuard — EU AI Act / LGPD compliance.

    Retorna eventos de bloqueio e soft-warning com metadados de contexto.
    Queries originais NÃO são expostas (apenas query_hash SHA-256).
    """
    since = datetime.now(UTC) - timedelta(days=days)
    repo = FairnessReportRepository(db)
    total, rows = await repo.get_audit_logs_paginated(
        since=since,
        company_id=company_id,
        category=category,
        blocked_only=blocked_only,
        limit=limit,
        offset=offset,
    )

    items = [
        FairnessAuditLogEntry(
            id=str(row.id),
            category=row.category,
            is_blocked=row.is_blocked,
            blocked_terms=row.blocked_terms or [],
            soft_warnings=row.soft_warnings or [],
            context=row.context if isinstance(row.context, str) else None,
            recruiter_id=str(row.recruiter_id) if row.recruiter_id else None,
            job_id=str(row.job_id) if row.job_id else None,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return FairnessAuditLogsResponse(
        company_id=company_id,
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


class JobFairnessBlockEntry(BaseModel):
    id: str
    category: str | None
    educational_message: str | None
    blocked_terms: list[str]
    soft_warnings: list[str]
    is_blocked: bool
    context: str | None
    created_at: datetime


class JobFairnessBlocksResponse(BaseModel):
    job_id: str
    total: int
    limit: int
    offset: int
    latest_block: JobFairnessBlockEntry | None
    items: list[JobFairnessBlockEntry]


@router.get("/jobs/{job_id}/blocks", response_model=JobFairnessBlocksResponse)
async def get_job_fairness_blocks(
    job_id: _DualId,
    include_warnings: bool = Query(False, description="Also include soft-warning events"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    FairnessGuard blocks recorded for a single job vacancy.

    Surfaces the category and educational message of the most recent block
    (so recruiters understand why a sourcing search returned no candidates)
    plus a paginated history of past events.

    Multi-tenant safe: the job_id is first verified to belong to the caller's
    company. Returns 404 (not 403) for jobs in other tenants to avoid leaking
    existence of foreign UUIDs.
    """
    from fastapi import HTTPException
    import uuid as _uuid

    from app.auth.dependencies import get_user_company_id
    from app.shared.compliance.fairness_guard import get_educational_message_for_category
    from lia_models.job_vacancy import JobVacancy

    try:
        job_uuid = _uuid.UUID(job_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    user_company = get_user_company_id(current_user)
    if not user_company:
        raise HTTPException(status_code=403, detail="Usuário sem empresa associada")

    job_row = (
        await db.execute(
            select(JobVacancy.id).where(
                JobVacancy.id == job_uuid,
                JobVacancy.company_id == user_company,
            )
        )
    ).first()
    if job_row is None:
        raise HTTPException(status_code=404, detail="Job vacancy not found")

    repo = FairnessReportRepository(db)
    total, rows = await repo.get_blocks_for_job(
        job_id=job_id,
        limit=limit,
        offset=offset,
        blocked_only=not include_warnings,
    )

    def _to_entry(row) -> JobFairnessBlockEntry:
        return JobFairnessBlockEntry(
            id=str(row.id),
            category=row.category,
            educational_message=get_educational_message_for_category(row.category),
            blocked_terms=list(row.blocked_terms or []),
            soft_warnings=list(row.soft_warnings or []),
            is_blocked=bool(row.is_blocked),
            context=row.context if isinstance(row.context, str) else None,
            created_at=row.created_at,
        )

    items = [_to_entry(row) for row in rows]

    latest_row = await repo.get_latest_block_for_job(job_id)
    latest_block = _to_entry(latest_row) if latest_row is not None else None

    return JobFairnessBlocksResponse(
        job_id=job_id,
        total=total,
        limit=limit,
        offset=offset,
        latest_block=latest_block,
        items=items,
    )


@router.get("/reports/export", response_model=None)
async def export_fairness_report(
    company_id: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    format: str = Query("csv", regex="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Export FairnessGuard report as CSV or JSON (EU AI Act compliance).

    CSV format: category,total_blocks,total_warnings,last_occurrence
    JSON format: FairnessSummaryResponse schema
    """
    import csv
    import io

    from fastapi.responses import JSONResponse, StreamingResponse

    # Reuse summary logic via repository
    since = datetime.now(UTC) - timedelta(days=days)
    repo = FairnessReportRepository(db)
    rows = await repo.get_export_data(since, company_id)

    if format == "json":
        data = {
            "period_days": days,
            "company_id": company_id,
            "exported_at": datetime.now(UTC).isoformat(),
            "total_blocks": sum(r.blocks for r in rows),
            "total_events": sum(r.blocks + r.warnings for r in rows),
            "by_category": [
                {
                    "category": r.category or "unknown",
                    "total_blocks": r.blocks,
                    "total_warnings": r.warnings,
                    "last_occurrence": r.last_occurrence.isoformat() if r.last_occurrence else None,
                }
                for r in rows
            ],
        }
        return JSONResponse(content=data)

    # CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["category", "total_blocks", "total_warnings", "last_occurrence"])
    for r in rows:
        writer.writerow([
            r.category or "unknown",
            r.blocks,
            r.warnings,
            r.last_occurrence.isoformat() if r.last_occurrence else "",
        ])
    output.seek(0)
    filename = f"fairness_report_{datetime.now(UTC).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
