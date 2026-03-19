"""
FairnessGuard reports API — EU AI Act compliance reporting.

Endpoints:
- GET /fairness/reports/summary   — hits por categoria (últimos N dias)
- GET /fairness/reports/trend     — série temporal de bloqueios
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/fairness", tags=["fairness-reports"])


class FairnessCategorySummary(BaseModel):
    category: str
    total_blocks: int
    total_warnings: int
    last_occurrence: Optional[datetime]


class FairnessSummaryResponse(BaseModel):
    period_days: int
    company_id: Optional[str]
    total_blocks: int
    total_events: int
    by_category: List[FairnessCategorySummary]


class FairnessTrendPoint(BaseModel):
    date: str  # ISO date YYYY-MM-DD
    blocks: int
    warnings: int


class FairnessTrendResponse(BaseModel):
    period_days: int
    company_id: Optional[str]
    trend: List[FairnessTrendPoint]


@router.get("/reports/summary", response_model=FairnessSummaryResponse)
async def get_fairness_summary(
    company_id: Optional[str] = Query(None, description="Filter by company UUID"),
    days: int = Query(30, ge=1, le=365, description="Look-back period in days"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Summary of FairnessGuard events grouped by bias category.

    Returns total blocks and warnings per category for the specified period.
    Useful for recruiter coaching and compliance dashboards.
    """
    from app.models.fairness_audit import FairnessAuditLog

    since = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = select(
        FairnessAuditLog.category,
        func.count().filter(FairnessAuditLog.is_blocked.is_(True)).label("blocks"),
        func.count().filter(FairnessAuditLog.is_blocked.is_(False)).label("warnings"),
        func.max(FairnessAuditLog.created_at).label("last_occurrence"),
    ).where(
        FairnessAuditLog.created_at >= since
    )

    if company_id:
        import uuid
        stmt = stmt.where(FairnessAuditLog.company_id == uuid.UUID(company_id))

    stmt = stmt.group_by(FairnessAuditLog.category)

    result = await db.execute(stmt)
    rows = result.all()

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
    company_id: Optional[str] = Query(None, description="Filter by company UUID"),
    days: int = Query(90, ge=7, le=365, description="Look-back period in days"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Daily trend of FairnessGuard events over time.

    Returns a time-series suitable for charting bias detection trends.
    Useful for identifying if training/coaching is reducing discrimination attempts.
    """
    from app.models.fairness_audit import FairnessAuditLog
    from sqlalchemy import cast, Date

    since = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = select(
        cast(FairnessAuditLog.created_at, Date).label("day"),
        func.count().filter(FairnessAuditLog.is_blocked.is_(True)).label("blocks"),
        func.count().filter(FairnessAuditLog.is_blocked.is_(False)).label("warnings"),
    ).where(
        FairnessAuditLog.created_at >= since
    )

    if company_id:
        import uuid
        stmt = stmt.where(FairnessAuditLog.company_id == uuid.UUID(company_id))

    stmt = stmt.group_by(cast(FairnessAuditLog.created_at, Date)).order_by("day")

    result = await db.execute(stmt)
    rows = result.all()

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


@router.get("/reports/export")
async def export_fairness_report(
    company_id: Optional[str] = Query(None),
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
    from fastapi.responses import StreamingResponse, JSONResponse
    import csv
    import io

    # Reuse summary logic
    from app.models.fairness_audit import FairnessAuditLog
    since = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = select(
        FairnessAuditLog.category,
        func.count().filter(FairnessAuditLog.is_blocked.is_(True)).label("blocks"),
        func.count().filter(FairnessAuditLog.is_blocked.is_(False)).label("warnings"),
        func.max(FairnessAuditLog.created_at).label("last_occurrence"),
    ).where(FairnessAuditLog.created_at >= since)

    if company_id:
        import uuid
        stmt = stmt.where(FairnessAuditLog.company_id == uuid.UUID(company_id))

    stmt = stmt.group_by(FairnessAuditLog.category)

    result = await db.execute(stmt)
    rows = result.all()

    if format == "json":
        data = {
            "period_days": days,
            "company_id": company_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
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
    filename = f"fairness_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
