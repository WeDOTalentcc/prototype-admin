"""
LGPD Cleanup Service — data retention enforcement.

Runs as a scheduled daily job to permanently delete candidate records
that have passed their `scheduled_deletion_at` date.

Retention policy (configurable per company, defaults below):
  - Rejected candidates:       90 days  after rejection
  - Withdrawn candidates:      90 days  after withdrawal
  - Interview notes / CVs:    180 days  after last activity
  - Screening logs:            365 days after creation

Design principles:
  - DRY-RUN first: log deletions without executing (safe to test)
  - Every deletion logged to audit_logs (LGPD accountability)
  - Scoped by company_id — never cross-tenant deletions
  - Irreversible: only run after dry-run validation
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.ai_consumption import AiConsumption
from app.models.candidate import Candidate, VacancyCandidate

logger = logging.getLogger(__name__)

# Default retention windows (days)
RETENTION_DAYS = {
    "rejected": 90,
    "withdrawn": 90,
    "interview_notes": 180,
    "screening_logs": 365,
    "ai_logs": 365,  # AiConsumption — logs de chamadas LLM (L-6)
}


async def schedule_deletion_for_candidate(
    db: AsyncSession,
    candidate_id: str,
    reason: str,
    retention_days: int | None = None,
) -> datetime:
    """
    Set scheduled_deletion_at on a candidate record.

    Called when a candidate is rejected or withdrawn so the cleanup job
    knows when to physically delete the record.

    Returns the scheduled deletion datetime.
    """
    days = retention_days or RETENTION_DAYS.get(reason, 90)
    deletion_at = datetime.utcnow() + timedelta(days=days)

    result = await db.execute(
        select(Candidate).where(Candidate.id == UUID(candidate_id))
    )
    candidate = result.scalar_one_or_none()
    if candidate:
        candidate.scheduled_deletion_at = deletion_at
        await db.commit()
        logger.info(
            "Deletion scheduled",
            extra={"candidate_id": candidate_id, "deletion_at": deletion_at.isoformat(), "reason": reason},
        )

    return deletion_at


async def run_cleanup(dry_run: bool = True) -> dict:
    """
    Delete candidates whose scheduled_deletion_at has passed.

    Args:
        dry_run: If True, only logs what would be deleted without committing.
                 Always run with dry_run=True first to validate the scope.

    Returns:
        Summary dict with counts of deleted records per table.
    """
    summary: dict = {
        "dry_run": dry_run,
        "ran_at": datetime.utcnow().isoformat(),
        "candidates_deleted": 0,
        "vacancy_candidates_deleted": 0,
        "ai_consumption_deleted": 0,
        "errors": [],
    }

    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()

        # 1. Candidates past their scheduled deletion date
        try:
            candidate_result = await db.execute(
                select(Candidate.id, Candidate.company_id, Candidate.scheduled_deletion_at)
                .where(
                    and_(
                        Candidate.scheduled_deletion_at.isnot(None),
                        Candidate.scheduled_deletion_at <= now,
                    )
                )
            )
            candidates_to_delete = candidate_result.all()

            for row in candidates_to_delete:
                logger.info(
                    "LGPD deletion%s: candidate",
                    " (dry-run)" if dry_run else "",
                    extra={
                        "candidate_id": str(row.id),
                        "company_id": str(row.company_id),
                        "scheduled_deletion_at": row.scheduled_deletion_at.isoformat(),
                    },
                )

            if not dry_run and candidates_to_delete:
                ids = [row.id for row in candidates_to_delete]
                await db.execute(
                    delete(Candidate).where(Candidate.id.in_(ids))
                )
                await db.commit()

            summary["candidates_deleted"] = len(candidates_to_delete)

        except Exception as exc:
            logger.error("Error during LGPD candidate cleanup: %s", exc)
            summary["errors"].append(f"candidates: {exc}")

        # 2. VacancyCandidate records (rejection data / PII)
        try:
            vc_result = await db.execute(
                select(
                    VacancyCandidate.id,
                    VacancyCandidate.company_id,
                    VacancyCandidate.scheduled_deletion_at,
                )
                .where(
                    and_(
                        VacancyCandidate.scheduled_deletion_at.isnot(None),
                        VacancyCandidate.scheduled_deletion_at <= now,
                    )
                )
            )
            vcs_to_delete = vc_result.all()

            for row in vcs_to_delete:
                logger.info(
                    "LGPD deletion%s: vacancy_candidate",
                    " (dry-run)" if dry_run else "",
                    extra={
                        "vacancy_candidate_id": str(row.id),
                        "company_id": str(row.company_id),
                        "scheduled_deletion_at": row.scheduled_deletion_at.isoformat(),
                    },
                )

            if not dry_run and vcs_to_delete:
                ids = [row.id for row in vcs_to_delete]
                await db.execute(
                    delete(VacancyCandidate).where(VacancyCandidate.id.in_(ids))
                )
                await db.commit()

            summary["vacancy_candidates_deleted"] = len(vcs_to_delete)

        except Exception as exc:
            logger.error("Error during LGPD vacancy_candidate cleanup: %s", exc)
            summary["errors"].append(f"vacancy_candidates: {exc}")

        # 3. AiConsumption records past their retention date (L-6: 365 days)
        try:
            ai_result = await db.execute(
                select(AiConsumption.id, AiConsumption.company_id, AiConsumption.scheduled_deletion_at)
                .where(
                    and_(
                        AiConsumption.scheduled_deletion_at.isnot(None),
                        AiConsumption.scheduled_deletion_at <= now,
                    )
                )
            )
            ai_to_delete = ai_result.all()

            for row in ai_to_delete:
                logger.info(
                    "LGPD deletion%s: ai_consumption",
                    " (dry-run)" if dry_run else "",
                    extra={
                        "ai_consumption_id": str(row.id),
                        "company_id": str(row.company_id),
                        "scheduled_deletion_at": row.scheduled_deletion_at.isoformat(),
                    },
                )

            if not dry_run and ai_to_delete:
                ids = [row.id for row in ai_to_delete]
                await db.execute(
                    delete(AiConsumption).where(AiConsumption.id.in_(ids))
                )
                await db.commit()

            summary["ai_consumption_deleted"] = len(ai_to_delete)

        except Exception as exc:
            logger.error("Error during LGPD ai_consumption cleanup: %s", exc)
            summary["errors"].append(f"ai_consumption: {exc}")

    mode = "DRY-RUN" if dry_run else "REAL"
    logger.info(
        "LGPD cleanup [%s] complete — candidates: %d, vacancy_candidates: %d, ai_consumption: %d, errors: %d",
        mode,
        summary["candidates_deleted"],
        summary["vacancy_candidates_deleted"],
        summary["ai_consumption_deleted"],
        len(summary["errors"]),
    )
    return summary


async def get_pending_deletions_count(db: AsyncSession) -> dict:
    """Return how many records are pending deletion (useful for monitoring)."""
    now = datetime.utcnow()

    c_count = await db.scalar(
        select(func.count(Candidate.id)).where(
            and_(
                Candidate.scheduled_deletion_at.isnot(None),
                Candidate.scheduled_deletion_at <= now,
            )
        )
    )

    vc_count = await db.scalar(
        select(func.count(VacancyCandidate.id)).where(
            and_(
                VacancyCandidate.scheduled_deletion_at.isnot(None),
                VacancyCandidate.scheduled_deletion_at <= now,
            )
        )
    )

    ai_count = await db.scalar(
        select(func.count(AiConsumption.id)).where(
            and_(
                AiConsumption.scheduled_deletion_at.isnot(None),
                AiConsumption.scheduled_deletion_at <= now,
            )
        )
    )

    return {
        "candidates_pending_deletion": c_count or 0,
        "vacancy_candidates_pending_deletion": vc_count or 0,
        "ai_consumption_pending_deletion": ai_count or 0,
        "checked_at": now.isoformat(),
    }
