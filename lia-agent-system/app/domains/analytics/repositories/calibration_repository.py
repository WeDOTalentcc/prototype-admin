"""CalibrationRepository — DB access layer for calibration loop tables.

Extracted from app/domains/analytics/services/calibration_service.py per ADR-001.
Tables covered:
  - calibration_events
  - calibration_suggestions
  - calibration_weights
"""
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import desc

from lia_models.calibration import (
    CalibrationEvent,
    CalibrationSuggestion,
    CalibrationWeight,
    FeedbackType,
)


class CalibrationRepository:
    """Repository for calibration loop data access.

    # CROSS-TENANT-INTENTIONAL: CalibrationEvent/CalibrationWeight tables
    # are TENANT-NULLABLE-DELIBERATE per ADR-LGPD-001. Cross-tenant analytics
    # (divergence detection, agree/disagree counts, weight calibration) are
    # legitimate aggregate reads — N>=10 hired threshold + decay enforce
    # anonymization (Art. 12 §1 + ANPD Guia §3). Per-tenant overrides happen
    # in higher-level service (CalibrationService applies company_id scoping
    # when computing personalized weights).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- CalibrationEvent reads ----

    async def list_divergences(
        self,
        since: datetime,
        limit: int = 20,
    ) -> list[CalibrationEvent]:
        """Return events that represent divergences (explicit disagree, high-score reject, low-score advance)."""
        stmt = (
            # TENANT-EXEMPT: calibration events/weights are per-company learning state; dynamic conditions builder upstream; T-RATCHET tenant_filter
            select(CalibrationEvent)
            .where(
                and_(
                    CalibrationEvent.created_at >= since,
                    or_(
                        CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_DISAGREE,
                        and_(
                            CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_REJECT,
                            CalibrationEvent.lia_score > 70,
                        ),
                        and_(
                            CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_ADVANCE,
                            CalibrationEvent.lia_score < 60,
                        ),
                    ),
                )
            )
            .order_by(desc(CalibrationEvent.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_total_events(self, since: datetime) -> int:
        """Count all calibration events since a given datetime."""
        stmt = select(func.count(CalibrationEvent.id)).where(
            CalibrationEvent.created_at >= since
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_explicit_agree(self, since: datetime) -> int:
        """Count EXPLICIT_AGREE events since a given datetime."""
        stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_AGREE,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_explicit_disagree(self, since: datetime) -> int:
        """Count EXPLICIT_DISAGREE events since a given datetime."""
        stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_DISAGREE,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_implicit_advances(self, since: datetime) -> int:
        """Count IMPLICIT_ADVANCE events since a given datetime."""
        stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_ADVANCE,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_implicit_rejects(self, since: datetime) -> int:
        """Count IMPLICIT_REJECT events since a given datetime."""
        stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_REJECT,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_high_score_rejects(self, since: datetime) -> int:
        """Count IMPLICIT_REJECT events where lia_score > 70."""
        stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_REJECT,
                CalibrationEvent.lia_score > 70,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_low_score_advances(self, since: datetime) -> int:
        """Count IMPLICIT_ADVANCE events where lia_score < 60."""
        stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_ADVANCE,
                CalibrationEvent.lia_score < 60,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def list_recent_events(
        self,
        limit: int = 50,
        feedback_types: list[FeedbackType] | None = None,
    ) -> list[CalibrationEvent]:
        """Return recent calibration events optionally filtered by feedback_type."""
        stmt = (
            # TENANT-EXEMPT: calibration events/weights are per-company learning state; dynamic conditions builder upstream; T-RATCHET tenant_filter
            select(CalibrationEvent)
            .order_by(desc(CalibrationEvent.created_at))
            .limit(limit)
        )
        if feedback_types:
            stmt = stmt.where(CalibrationEvent.feedback_type.in_(feedback_types))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---- CalibrationSuggestion reads ----

    async def list_pending_suggestions(self) -> list[CalibrationSuggestion]:
        """Return suggestions with status='pending', newest first."""
        stmt = (
            select(CalibrationSuggestion)
            .where(CalibrationSuggestion.status == "pending")
            .order_by(desc(CalibrationSuggestion.created_at))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_suggestion_by_id(self, suggestion_id: str) -> CalibrationSuggestion | None:
        """Return a suggestion by its id, or None."""
        stmt = select(CalibrationSuggestion).where(
            CalibrationSuggestion.id == suggestion_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---- CalibrationWeight reads ----

    async def get_active_weight_by_dimension(
        self, dimension: str
    ) -> CalibrationWeight | None:
        """Return the active CalibrationWeight for a given dimension, or None."""
        # TENANT-EXEMPT: calibration events/weights are per-company learning state; dynamic conditions builder upstream; T-RATCHET tenant_filter
        stmt = select(CalibrationWeight).where(
            and_(
                CalibrationWeight.dimension == dimension,
                CalibrationWeight.is_active,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_weights(
        self, job_id: str | None = None
    ) -> list[CalibrationWeight]:
        """Return active calibration weights, optionally scoped to a job_id (with global fallback)."""
        # TENANT-EXEMPT: calibration events/weights are per-company learning state; dynamic conditions builder upstream; T-RATCHET tenant_filter
        stmt = select(CalibrationWeight).where(CalibrationWeight.is_active)
        if job_id:
            stmt = stmt.where(
                or_(
                    CalibrationWeight.job_id == job_id,
                    CalibrationWeight.job_id.is_(None),
                )
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    async def list_events_by_job(
        self,
        job_id,
        since: datetime,
        limit: int = 200,
    ) -> list[CalibrationEvent]:
        """List CalibrationEvent rows for a job_id since a cutoff.

        Note: CalibrationEvent has no company_id column — multi-tenancy is enforced
        upstream via job_id ownership.
        """
        stmt = (
            # TENANT-EXEMPT: calibration events/weights are per-company learning state; dynamic conditions builder upstream; T-RATCHET tenant_filter
            select(CalibrationEvent)
            .where(
                and_(
                    CalibrationEvent.job_id == job_id,
                    CalibrationEvent.created_at >= since,
                )
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

