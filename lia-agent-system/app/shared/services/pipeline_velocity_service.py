"""
Pipeline Velocity Service - Sprint 1B.

Computes time-in-stage metrics using the stage_entered_at column (added in
migration 023). Detects bottlenecks per stage and per vacancy so that:
  - ProactiveAgentWorker can alert recruiters proactively
  - Kanban/JobsManagement agents can reason about pipeline health
  - Analytics can compare velocity across vacancies and companies

Benchmark thresholds per stage (business days — conservative for Brazilian market):
  applied / initial    : 2 days
  screening / triagem  : 3 days
  interview_hr         : 5 days
  interview_tech       : 7 days
  proposal / offer     : 3 days
  (any other stage)    : 5 days
"""

from __future__ import annotations

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "pipeline_velocity_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)


import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Days before a stage is flagged as a bottleneck
_STAGE_THRESHOLDS: dict[str, int] = {
    "applied": 2,
    "initial": 2,
    "novo": 2,
    "screening": 3,
    "triagem": 3,
    "interview_hr": 5,
    "entrevista_rh": 5,
    "entrevista_hr": 5,
    "interview_tech": 7,
    "interview_technical": 7,
    "entrevista_tecnica": 7,
    "technical": 7,
    "proposal": 3,
    "offer": 3,
    "proposta": 3,
}
_DEFAULT_THRESHOLD = 5


def _threshold_for_stage(stage: str) -> int:
    return _STAGE_THRESHOLDS.get((stage or "").lower(), _DEFAULT_THRESHOLD)


class PipelineVelocityService:
    """Velocity analytics based on stage_entered_at."""

    async def get_velocity_metrics(
        self,
        vacancy_id: str | None = None,
        company_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Return per-stage velocity metrics for a vacancy or whole company.

        Metrics per stage:
          avg_days, median_days, max_days, candidate_count, bottleneck (bool),
          threshold_days
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            filters = []
            params: dict[str, Any] = {}

            if vacancy_id:
                filters.append("vc.vacancy_id::text = :vacancy_id")
                params["vacancy_id"] = vacancy_id
            if company_id:
                filters.append("jv.company_id::text = :company_id")
                params["company_id"] = company_id

            where = ("WHERE " + " AND ".join(filters)) if filters else ""
            join_jv = "JOIN job_vacancies jv ON jv.id = vc.vacancy_id" if company_id else ""

            result = await db.execute(
                text(f"""
                    SELECT
                        vc.stage,
                        AVG(EXTRACT(EPOCH FROM (NOW() - vc.stage_entered_at)) / 86400) AS avg_days,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (
                            ORDER BY EXTRACT(EPOCH FROM (NOW() - vc.stage_entered_at)) / 86400
                        ) AS median_days,
                        MAX(EXTRACT(EPOCH FROM (NOW() - vc.stage_entered_at)) / 86400) AS max_days,
                        COUNT(*) AS candidate_count
                    FROM vacancy_candidates vc
                    {join_jv}
                    {where}
                      AND vc.stage_entered_at IS NOT NULL
                      AND vc.status NOT IN ('rejected', 'hired', 'withdrawn')
                    GROUP BY vc.stage
                    ORDER BY avg_days DESC
                """),
                params,
            )
            rows = result.mappings().fetchall()

            per_stage: dict[str, dict[str, Any]] = {}
            bottleneck_stages: list[str] = []

            for row in rows:
                stage = row["stage"] or "unknown"
                avg_d = round(float(row["avg_days"] or 0), 1)
                median_d = round(float(row["median_days"] or 0), 1)
                max_d = round(float(row["max_days"] or 0), 1)
                count = int(row["candidate_count"])
                threshold = _threshold_for_stage(stage)
                is_bottleneck = avg_d > threshold

                per_stage[stage] = {
                    "avg_days": avg_d,
                    "median_days": median_d,
                    "max_days": max_d,
                    "candidate_count": count,
                    "threshold_days": threshold,
                    "is_bottleneck": is_bottleneck,
                }
                if is_bottleneck:
                    bottleneck_stages.append(stage)

            overall_health = "healthy"
            if len(bottleneck_stages) >= 3:
                overall_health = "critical"
            elif bottleneck_stages:
                overall_health = "warning"

            return {
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "per_stage": per_stage,
                "bottleneck_stages": bottleneck_stages,
                "overall_health": overall_health,
                "total_stages_tracked": len(per_stage),
            }

        except Exception as e:
            logger.warning(f"PipelineVelocityService.get_velocity_metrics error: {e}")
            return {
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "per_stage": {},
                "bottleneck_stages": [],
                "overall_health": "unknown",
                "error": str(e),
            }
        finally:
            if should_close:
                await db.close()

    async def get_bottlenecked_candidates(
        self,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return candidates currently stuck beyond their stage threshold.

        Used by ProactiveAgentWorker.check_velocity_bottleneck().
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            result = await db.execute(
                text("""
                    SELECT
                        vc.id AS vacancy_candidate_id,
                        vc.candidate_id,
                        vc.vacancy_id,
                        vc.stage,
                        vc.stage_entered_at,
                        EXTRACT(EPOCH FROM (NOW() - vc.stage_entered_at)) / 86400 AS days_in_stage,
                        c.name AS candidate_name,
                        jv.title AS vacancy_title
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE jv.company_id::text = :company_id
                      AND vc.stage_entered_at IS NOT NULL
                      AND vc.status NOT IN ('rejected', 'hired', 'withdrawn')
                      AND jv.status = 'open'
                    ORDER BY days_in_stage DESC
                """),
                {"company_id": company_id},
            )
            rows = result.mappings().fetchall()

            bottlenecked = []
            for row in rows:
                stage = row["stage"] or "unknown"
                days = round(float(row["days_in_stage"] or 0), 1)
                threshold = _threshold_for_stage(stage)
                if days > threshold:
                    bottlenecked.append({
                        "vacancy_candidate_id": str(row["vacancy_candidate_id"]),
                        "candidate_id": str(row["candidate_id"]),
                        "vacancy_id": str(row["vacancy_id"]),
                        "candidate_name": row["candidate_name"],
                        "vacancy_title": row["vacancy_title"],
                        "stage": stage,
                        "days_in_stage": days,
                        "threshold_days": threshold,
                        "overdue_days": round(days - threshold, 1),
                    })

            return bottlenecked

        except Exception as e:
            logger.warning(f"PipelineVelocityService.get_bottlenecked_candidates error: {e}")
            return []
        finally:
            if should_close:
                await db.close()


pipeline_velocity_service = PipelineVelocityService()
