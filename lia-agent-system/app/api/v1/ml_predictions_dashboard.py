"""
ML Predictions Dashboard — time-to-fill estimates per vacancy.

Uses heuristic based on tenant's historical data (avg TTF by seniority).
Falls back to Brazilian market defaults when insufficient data.
Will switch to "ml_model" source when Sprint 11 trains real model.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Brazilian market defaults (days) when no tenant data available
_MARKET_DEFAULTS = {
    "estagiário": 20, "estagiario": 20,
    "júnior": 25, "junior": 25,
    "pleno": 35,
    "sênior": 45, "senior": 45,
    "especialista": 50,
    "lead": 55,
    "gerente": 60,
    "diretor": 90,
    "vp": 120, "c-level": 120, "clevel": 120,
}
_MARKET_GLOBAL_AVG = 42  # days


@router.get("/ml-predictions")
async def get_ml_predictions(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Time-to-fill predictions for open vacancies.

    Heuristic: avg TTF by seniority from tenant's closed vacancies (90d).
    Falls back to market defaults when insufficient data.
    """
    company_id = str(current_user.company_id)
    cutoff = datetime.utcnow() - timedelta(days=365)

    try:
        from lia_models.job_vacancy import JobVacancy

        # --- 1. Historical TTF by seniority (closed vacancies) ---
        # NOTE: build the seniority expression ONCE and reuse the same object in
        # both SELECT and GROUP BY. Creating two separate coalesce(..., "pleno")
        # calls makes SQLAlchemy emit two distinct bind params, and Postgres then
        # rejects the GROUP BY ("column must appear in the GROUP BY clause").
        seniority_expr = func.lower(func.coalesce(JobVacancy.seniority_level, "pleno"))
        hist_result = await db.execute(
            select(
                seniority_expr.label("seniority"),
                func.avg(
                    extract("epoch", JobVacancy.closed_at) - extract("epoch", JobVacancy.created_at)
                ).label("avg_seconds"),
                func.count(JobVacancy.id).label("sample_size"),
            )
            .where(
                and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.closed_at.isnot(None),
                    JobVacancy.created_at >= cutoff,
                )
            )
            .group_by(seniority_expr)
        )

        tenant_avgs: dict[str, dict] = {}
        for row in hist_result.all():
            seniority = (row.seniority or "pleno").strip().lower()
            avg_days = round((row.avg_seconds or 0) / 86400, 1)
            tenant_avgs[seniority] = {
                "avg_days": avg_days,
                "sample_size": int(row.sample_size or 0),
            }

        # Company-wide average
        company_avg = round(
            sum(v["avg_days"] * v["sample_size"] for v in tenant_avgs.values())
            / max(sum(v["sample_size"] for v in tenant_avgs.values()), 1),
            1,
        ) if tenant_avgs else _MARKET_GLOBAL_AVG

        # --- 2. Open vacancies with predictions ---
        open_result = await db.execute(
            select(
                JobVacancy.id,
                JobVacancy.title,
                JobVacancy.seniority_level,
                JobVacancy.target_sector,
                JobVacancy.created_at,
            )
            .where(
                and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.status.in_(["Ativa", "open", "active"]),
                    JobVacancy.closed_at.is_(None),
                )
            )
            .order_by(JobVacancy.created_at.desc())
            .limit(50)
        )

        vacancies = []
        now = datetime.utcnow()

        for row in open_result.all():
            seniority = (row.seniority_level or "pleno").strip().lower()
            days_open = (now - row.created_at).days if row.created_at else 0

            # Try ML model first, then tenant heuristic, then market default
            try:
                from app.shared.ml.ttf_predictor import ttf_predictor
                ml_result = ttf_predictor.predict({
                    "seniority_level": seniority,
                    "work_model": getattr(row, "work_model", None) or "presencial",
                    "urgency_level": getattr(row, "urgency_level", 3) or 3,
                })
                if ml_result.source == "ml_model":
                    predicted_ttf = ml_result.predicted_days
                    confidence = ml_result.confidence
                    source = "ml_model"
                    factors = [f"modelo ML v{ml_result.model_version}"] + ml_result.features_used
                else:
                    raise ValueError("ML model not available")
            except Exception:
                # Fallback to tenant heuristic → market default
                tenant_data = tenant_avgs.get(seniority)
                if tenant_data and tenant_data["sample_size"] >= 3:
                    predicted_ttf = tenant_data["avg_days"]
                    confidence = min(0.5 + tenant_data["sample_size"] * 0.05, 0.90)
                    source = "heuristic"
                    factors = [
                        f"senioridade: {seniority}",
                        f"histórico empresa: {predicted_ttf:.0f}d média ({tenant_data['sample_size']} vagas)",
                    ]
                else:
                    predicted_ttf = _MARKET_DEFAULTS.get(seniority, 35)
                    confidence = 0.40
                    source = "market_default"
                    factors = [
                        f"senioridade: {seniority}",
                        f"default mercado BR: {predicted_ttf}d",
                    ]

            if row.target_sector:
                factors.append(f"setor: {row.target_sector}")

            vacancies.append({
                "job_id": str(row.id),
                "title": row.title or "Sem título",
                "seniority": seniority,
                "days_open": days_open,
                "predicted_ttf_days": round(predicted_ttf),
                "confidence": round(confidence, 2),
                "source": source,
                "factors": factors,
                "is_overdue": days_open > predicted_ttf,
            })

        return {
            "vacancies": vacancies,
            "company_avg_ttf": round(company_avg),
            "market_avg_ttf": _MARKET_GLOBAL_AVG,
            "total_open": len(vacancies),
            "overdue_count": sum(1 for v in vacancies if v["is_overdue"]),
            "period": "last_365_days",
            "company_id": company_id,
            "generated_at": now.isoformat(),
        }

    except Exception as exc:
        logger.warning("[MLPredictions] failed: %s", exc)
        return {
            "vacancies": [],
            "company_avg_ttf": _MARKET_GLOBAL_AVG,
            "market_avg_ttf": _MARKET_GLOBAL_AVG,
            "total_open": 0,
            "overdue_count": 0,
            "period": "last_365_days",
            "error": str(exc),
        }
