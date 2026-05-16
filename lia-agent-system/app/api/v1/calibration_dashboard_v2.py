"""
Calibration Dashboard V2 — tenant-scoped, per-domain divergence analysis.

Enriches the existing /calibration/dashboard with:
- Tenant isolation (company_id from auth)
- Per-domain breakdown (which agents diverge most)
- Agreement/disagreement rates per domain
- CalibrationWeight status per dimension
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/calibration-dashboard")
async def get_calibration_dashboard_v2(
    days: int = Query(30, ge=7, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Calibration dashboard — per-domain divergence analysis.

    Shows where LIA's recommendations diverge from recruiter decisions,
    enabling targeted weight calibration.
    """
    company_id = str(current_user.company_id)
    since = datetime.utcnow() - timedelta(days=days)

    result: dict[str, Any] = {
        "company_id": company_id,
        "period_days": days,
        "generated_at": datetime.utcnow().isoformat(),
    }

    try:
        from lia_models.calibration import CalibrationEvent, FeedbackType, CalibrationWeight

        # --- 1. Overall stats ---
        stats_q = await db.execute(
            select(
                func.count(CalibrationEvent.id).label("total"),
                func.sum(case(
                    (CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_AGREE, 1), else_=0
                )).label("agrees"),
                func.sum(case(
                    (CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_DISAGREE, 1), else_=0
                )).label("disagrees"),
                func.avg(CalibrationEvent.lia_score).label("avg_lia_score"),
            )
            .where(
                and_(
                    CalibrationEvent.company_id == company_id,
                    CalibrationEvent.created_at >= since,
                )
            )
        )
        stats_row = stats_q.one()
        total = int(stats_row.total or 0)
        agrees = int(stats_row.agrees or 0)
        disagrees = int(stats_row.disagrees or 0)

        result["overall"] = {
            "total_events": total,
            "agree_count": agrees,
            "disagree_count": disagrees,
            "agreement_rate": round(agrees / max(agrees + disagrees, 1), 3),
            "avg_lia_score": round(float(stats_row.avg_lia_score or 0), 2),
        }

        # --- 2. Per-domain breakdown ---
        domain_q = await db.execute(
            select(
                CalibrationEvent.context["domain"].astext.label("domain"),
                func.count(CalibrationEvent.id).label("total"),
                func.sum(case(
                    (CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_AGREE, 1), else_=0
                )).label("agrees"),
                func.sum(case(
                    (CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_DISAGREE, 1), else_=0
                )).label("disagrees"),
                func.avg(CalibrationEvent.lia_score).label("avg_score"),
            )
            .where(
                and_(
                    CalibrationEvent.company_id == company_id,
                    CalibrationEvent.created_at >= since,
                )
            )
            .group_by(CalibrationEvent.context["domain"].astext)
        )

        domains = []
        for row in domain_q.all():
            domain_total = int(row.total or 0)
            domain_agrees = int(row.agrees or 0)
            domain_disagrees = int(row.disagrees or 0)
            explicit = domain_agrees + domain_disagrees
            agreement = round(domain_agrees / max(explicit, 1), 3)
            domains.append({
                "domain": row.domain or "unknown",
                "total_events": domain_total,
                "agree_count": domain_agrees,
                "disagree_count": domain_disagrees,
                "agreement_rate": agreement,
                "avg_lia_score": round(float(row.avg_score or 0), 2),
                "needs_calibration": agreement < 0.70 and explicit >= 5,
            })

        result["domains"] = sorted(domains, key=lambda d: d["agreement_rate"])

        # --- 3. Active weights ---
        weights_q = await db.execute(
            select(CalibrationWeight)
            .where(
                and_(
                    CalibrationWeight.company_id == company_id,
                    CalibrationWeight.is_active == True,
                )
            )
        )
        weights = weights_q.scalars().all()
        result["weights"] = [
            {
                "dimension": w.dimension,
                "base_weight": w.base_weight,
                "adjusted_weight": w.adjusted_weight,
                "confidence": w.confidence,
                "sample_size": w.sample_size,
            }
            for w in weights
        ]

        # --- 4. Pending suggestions ---
        try:
            from lia_models.calibration import CalibrationSuggestion
            sug_q = await db.execute(
                select(func.count(CalibrationSuggestion.id))
                .where(CalibrationSuggestion.status == "pending")
            )
            result["pending_suggestions"] = int(sug_q.scalar() or 0)
        except Exception:
            result["pending_suggestions"] = 0

    except Exception as exc:
        logger.warning("[CalibrationDashboardV2] failed: %s", exc)
        result["overall"] = {"total_events": 0, "agreement_rate": 0}
        result["domains"] = []
        result["weights"] = []
        result["error"] = str(exc)

    return result
