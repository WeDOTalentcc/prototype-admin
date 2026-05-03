"""
Silver Medalist Service - Sprint 1E.

Queries candidates who reached the interview stage in past vacancies but
were not hired, and re-surfaces them as "warm" candidates for new similar
vacancies — reducing sourcing time and increasing pipeline quality.

A Silver Medalist is a candidate who:
  - Reached at least 'interview_hr' in a past vacancy (any interview stage)
  - Was not hired in that vacancy (final stage != 'hired', status != 'hired')
  - Is not currently active in the target vacancy

The service scores each medalist by:
  - Time since last process (recency — more recent = more relevant)
  - LIA score in previous vacancy (quality signal)
  - Stage reached (deeper = stronger signal)
"""

from __future__ import annotations

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "silver_medalist_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)


import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Stages considered as "interview reached" (minimum bar for silver medalist)
INTERVIEW_STAGES = {
    "interview_hr",
    "entrevista_hr",
    "entrevista_rh",
    "interview_technical",
    "entrevista_tecnica",
    "interview_manager",
    "interview_final",
    "entrevista_gestor",
    "entrevista_final",
    "offer",
    "proposta",
}

# Stage weights for relevance scoring (higher = better signal)
STAGE_WEIGHTS = {
    "offer": 1.0,
    "proposta": 1.0,
    "interview_final": 0.9,
    "entrevista_final": 0.9,
    "interview_manager": 0.8,
    "entrevista_gestor": 0.8,
    "interview_technical": 0.7,
    "entrevista_tecnica": 0.7,
    "interview_hr": 0.5,
    "entrevista_hr": 0.5,
    "entrevista_rh": 0.5,
}


def _stage_weight(stage: str) -> float:
    return STAGE_WEIGHTS.get((stage or "").lower(), 0.5)


def _recency_score(days_ago: float) -> float:
    """Decay recency score: 1.0 at 0 days → 0.1 at 180 days."""
    if days_ago <= 0:
        return 1.0
    return max(0.1, 1.0 - (days_ago / 180.0))


class SilverMedalistService:
    """
    Surfaces warm candidates from previous processes for new vacancies.

    Usage by agents:
    ```python
    medalists = await silver_medalist_service.find_for_vacancy(
        target_vacancy_id="...",
        company_id="...",
        limit=20,
    )
    ```
    """

    async def find_for_vacancy(
        self,
        target_vacancy_id: str,
        company_id: str,
        limit: int = 20,
        max_days_lookback: int = 180,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find silver medalists relevant to the target vacancy.

        Returns candidates ranked by a composite relevance score combining:
        - Stage reached (interview_hr=0.5 ... offer=1.0)
        - Recency (recent processes score higher)
        - LIA score from previous vacancy
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            cutoff = datetime.utcnow() - timedelta(days=max_days_lookback)

            # Silver Medalists: reached interview stage, not hired, not in current vacancy
            result = await db.execute(
                text("""
                    SELECT
                        vc.candidate_id,
                        c.name AS candidate_name,
                        c.email AS candidate_email,
                        c.phone AS candidate_phone,
                        vc.vacancy_id AS past_vacancy_id,
                        jv.title AS past_vacancy_title,
                        vc.stage AS reached_stage,
                        COALESCE(vc.lia_score, vc.match_percentage) AS past_lia_score,
                        EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400 AS days_since_process,
                        vc.updated_at AS last_activity
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE jv.company_id::text = :company_id
                      AND vc.vacancy_id::text != :target_vacancy_id
                      AND vc.stage NOT IN ('hired', 'contratado')
                      AND vc.status NOT IN ('hired', 'contratado')
                      AND vc.updated_at >= :cutoff
                      AND vc.stage IN (
                          'interview_hr', 'entrevista_hr', 'entrevista_rh',
                          'interview_technical', 'entrevista_tecnica',
                          'interview_manager', 'entrevista_gestor',
                          'interview_final', 'entrevista_final',
                          'offer', 'proposta'
                      )
                      AND vc.candidate_id NOT IN (
                          SELECT candidate_id FROM vacancy_candidates
                          WHERE vacancy_id::text = :target_vacancy_id
                      )
                    ORDER BY vc.updated_at DESC
                    LIMIT :limit
                """),
                {
                    "company_id": company_id,
                    "target_vacancy_id": target_vacancy_id,
                    "cutoff": cutoff,
                    "limit": limit * 3,  # fetch more, rank, then trim
                },
            )
            rows = result.mappings().fetchall()

            medalists = []
            seen_candidates: set = set()

            for row in rows:
                cid = str(row["candidate_id"])
                if cid in seen_candidates:
                    continue  # keep only the best past process per candidate
                seen_candidates.add(cid)

                days_ago = float(row["days_since_process"] or 0)
                raw_score = float(row["past_lia_score"] or 0)
                lia_score = raw_score / 100.0 if raw_score > 1.0 else raw_score
                stage = row["reached_stage"] or ""

                # Composite relevance score [0..1]
                relevance = round(
                    0.4 * _stage_weight(stage)
                    + 0.35 * _recency_score(days_ago)
                    + 0.25 * lia_score,
                    3,
                )

                medalists.append({
                    "candidate_id": cid,
                    "candidate_name": row["candidate_name"],
                    "candidate_email": row["candidate_email"],
                    "candidate_phone": row["candidate_phone"],
                    "past_vacancy_id": str(row["past_vacancy_id"]),
                    "past_vacancy_title": row["past_vacancy_title"],
                    "reached_stage": stage,
                    "past_lia_score": round(lia_score, 3),
                    "days_since_process": round(days_ago),
                    "relevance_score": relevance,
                    "last_activity": row["last_activity"].isoformat() if row["last_activity"] else None,
                })

            # Rank by relevance and return top N
            medalists.sort(key=lambda x: x["relevance_score"], reverse=True)
            return medalists[:limit]

        except Exception as e:
            logger.warning(f"SilverMedalistService.find_for_vacancy error: {e}")
            return []
        finally:
            if should_close:
                await db.close()

    async def find_for_company(
        self,
        company_id: str,
        limit: int = 50,
        max_days_lookback: int = 90,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return all silver medalists in the company pool (not vacancy-specific).

        Used by ProactiveAgentWorker to surface talent for active vacancies.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            cutoff = datetime.utcnow() - timedelta(days=max_days_lookback)

            result = await db.execute(
                text("""
                    SELECT
                        vc.candidate_id,
                        c.name AS candidate_name,
                        c.email AS candidate_email,
                        vc.vacancy_id AS past_vacancy_id,
                        jv.title AS past_vacancy_title,
                        jv.department,
                        vc.stage AS reached_stage,
                        COALESCE(vc.lia_score, vc.match_percentage) AS past_lia_score,
                        EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400 AS days_since_process
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE jv.company_id::text = :company_id
                      AND vc.stage NOT IN ('hired', 'contratado')
                      AND vc.status NOT IN ('hired', 'contratado')
                      AND vc.updated_at >= :cutoff
                      AND vc.stage IN (
                          'interview_hr', 'entrevista_hr', 'entrevista_rh',
                          'interview_technical', 'entrevista_tecnica',
                          'interview_manager', 'entrevista_gestor',
                          'interview_final', 'entrevista_final',
                          'offer', 'proposta'
                      )
                    ORDER BY vc.updated_at DESC
                    LIMIT :limit
                """),
                {"company_id": company_id, "cutoff": cutoff, "limit": limit},
            )
            rows = result.mappings().fetchall()

            medalists = []
            seen: set = set()
            for row in rows:
                cid = str(row["candidate_id"])
                if cid in seen:
                    continue
                seen.add(cid)
                medalists.append({
                    "candidate_id": cid,
                    "candidate_name": row["candidate_name"],
                    "candidate_email": row["candidate_email"],
                    "past_vacancy_id": str(row["past_vacancy_id"]),
                    "past_vacancy_title": row["past_vacancy_title"],
                    "department": row["department"],
                    "reached_stage": row["reached_stage"],
                    "past_lia_score": float(row["past_lia_score"] or 0),
                    "days_since_process": round(float(row["days_since_process"] or 0)),
                })
            return medalists

        except Exception as e:
            logger.warning(f"SilverMedalistService.find_for_company error: {e}")
            return []
        finally:
            if should_close:
                await db.close()


silver_medalist_service = SilverMedalistService()
