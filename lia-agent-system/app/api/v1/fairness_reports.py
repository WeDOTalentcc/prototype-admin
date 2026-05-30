
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
from app.schemas.envelope import ResponseEnvelope, ok_envelope
from app.shared.security.require_company_id import require_company_id
from app.api.v1._path_patterns import reorder_collection_before_item

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


@router.get("/reports/summary", response_model=ResponseEnvelope[FairnessSummaryResponse])
# TODO(phase2): extract to repository — complex fairness aggregation
async def get_fairness_summary(
    days: int = Query(30, ge=1, le=365, description="Look-back period in days"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    company_id: str = Depends(require_company_id)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id) — P1-W1-03 fix
    """
    Summary of FairnessGuard events grouped by bias category.

    Returns total blocks and warnings per category for the specified period.
    Useful for recruiter coaching and compliance dashboards.

    P1-W1-03 fix (2026-05-24): company_id agora exclusivamente do JWT via
    require_company_id. Removido Query(None) que permitia cross-tenant:
    qualquer usuario podia passar company_id de outra empresa como query
    param e obter relatorio alheio. require_company_id_strict_match era gate
    parcial — canonical eh remover o Query param inteiramente (CLAUDE.md REGRA 2).
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

    return ok_envelope(FairnessSummaryResponse(
        period_days=days,
        company_id=company_id,
        total_blocks=total_blocks,
        total_events=total_events,
        by_category=by_category,
    ))


@router.get("/reports/trend", response_model=FairnessTrendResponse)
async def get_fairness_trend(
    days: int = Query(90, ge=7, le=365, description="Look-back period in days"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    company_id: str = Depends(require_company_id)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id) — P1-W1-03 fix
    """
    Daily trend of FairnessGuard events over time.

    Returns a time-series suitable for charting bias detection trends.
    Useful for identifying if training/coaching is reducing discrimination attempts.

    P1-W1-03 fix (2026-05-24): company_id do JWT somente. Query param removido.
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
    category: str | None = Query(None, description="Filter by bias category"),
    blocked_only: bool = Query(False, description="Return only blocked events"),
    days: int = Query(30, ge=1, le=365, description="Look-back period in days"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    company_id: str = Depends(require_company_id)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id) — P1-W1-03 fix
    """
    Paginado audit trail do FairnessGuard — EU AI Act / LGPD compliance.

    Retorna eventos de bloqueio e soft-warning com metadados de contexto.
    Queries originais NÃO são expostas (apenas query_hash SHA-256).

    P1-W1-03 fix (2026-05-24): company_id do JWT somente. Query param removido.
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


@router.get("/reports/export", response_model=None)
async def export_fairness_report(
    days: int = Query(30, ge=1, le=365),
    format: str = Query("csv", regex="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    company_id: str = Depends(require_company_id)):
    # multi-tenancy: company_id JWT-only via Depends(require_company_id) — P1-W1-03 fix
    """
    Export FairnessGuard report as CSV or JSON (EU AI Act compliance).

    CSV format: category,total_blocks,total_warnings,last_occurrence
    JSON format: FairnessSummaryResponse schema

    P1-W1-03 fix (2026-05-24): company_id do JWT somente. Query param removido.
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

reorder_collection_before_item(router)
