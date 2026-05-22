"""IntelligenceRepository — DB access layer for intelligence-layer tables.

Extracted from analytics services per ADR-001.
Tables covered:
  - correction_patterns
  - success_profiles
  - outcome_correlations
  - pattern_cache
  - intelligence_insights
  - job_outcomes (cross-table reads for correlator)
  - wizard_feedback (cross-table reads for pattern detector)
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.feedback_learning import JobOutcome, WizardFeedback
from lia_models.intelligence_layer import (
    CorrectionPattern,
    IntelligenceInsight,
    OutcomeCorrelation,
    PatternCache,
    SuccessProfile,
)

logger = logging.getLogger(__name__)


class IntelligenceRepository:
    """Repository for intelligence-layer data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: Any) -> Any:
        if not company_id:
            raise ValueError("company_id is required for fail-closed multi-tenancy")
        return company_id

    # ---------- CorrectionPattern ----------

    async def list_active_correction_patterns(
        self,
        company_id: Any,
        seniority: str | None = None,
    ) -> list[CorrectionPattern]:
        company_id = self._require_company_id(company_id)
        stmt = select(CorrectionPattern).where(
            and_(
                CorrectionPattern.company_id == company_id,
                CorrectionPattern.is_active,
            )
        )
        if seniority:
            stmt = stmt.where(
                (CorrectionPattern.seniority == seniority)
                | (CorrectionPattern.seniority.is_(None))
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_all_correction_patterns(
        self,
        company_id: Any,
    ) -> list[CorrectionPattern]:
        company_id = self._require_company_id(company_id)
        stmt = select(CorrectionPattern).where(
            CorrectionPattern.company_id == company_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- SuccessProfile ----------

    async def find_top_success_profile(
        self,
        company_id: Any,
        seniority: str | None = None,
    ) -> SuccessProfile | None:
        company_id = self._require_company_id(company_id)
        stmt = select(SuccessProfile).where(
            SuccessProfile.company_id == company_id
        )
        if seniority:
            stmt = stmt.where(
                (SuccessProfile.seniority == seniority)
                | (SuccessProfile.seniority.is_(None))
            )
        stmt = stmt.order_by(SuccessProfile.sample_size.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- OutcomeCorrelation ----------

    async def list_outcome_correlations(
        self, company_id: Any
    ) -> list[OutcomeCorrelation]:
        company_id = self._require_company_id(company_id)
        stmt = select(OutcomeCorrelation).where(
            OutcomeCorrelation.company_id == company_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_correlation_by_factor(
        self,
        company_id: Any,
        factor: str,
    ) -> OutcomeCorrelation | None:
        company_id = self._require_company_id(company_id)
        stmt = select(OutcomeCorrelation).where(
            and_(
                OutcomeCorrelation.company_id == company_id,
                OutcomeCorrelation.factor == factor,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- PatternCache ----------

    async def find_active_cache(
        self,
        company_id: Any,
        pattern_type: str,
    ) -> PatternCache | None:
        company_id = self._require_company_id(company_id)
        stmt = select(PatternCache).where(
            and_(
                PatternCache.company_id == company_id,
                PatternCache.pattern_type == pattern_type,
                PatternCache.expires_at > datetime.utcnow(),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- IntelligenceInsight ----------

    async def find_insight_by_id(
        self, insight_id: UUID
    ) -> IntelligenceInsight | None:
        # TENANT-EXEMPT: intelligence insights use dynamic conditions builder; sensor AST cannot trace; T-RATCHET tenant_filter
        stmt = select(IntelligenceInsight).where(
            IntelligenceInsight.id == insight_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- JobOutcome (cross-table for correlator/detector) ----------

    async def list_filled_outcomes(self, company_id: Any) -> list[JobOutcome]:
        from lia_models.feedback_learning import JobOutcomeType

        company_id = self._require_company_id(company_id)
        stmt = select(JobOutcome).where(
            and_(
                JobOutcome.company_id == company_id,
                JobOutcome.outcome == JobOutcomeType.FILLED,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_outcomes_for_company(self, company_id: Any) -> list[JobOutcome]:
        company_id = self._require_company_id(company_id)
        stmt = select(JobOutcome).where(JobOutcome.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- WizardFeedback (cross-table for pattern_detector) ----------

    async def list_wizard_feedback_with_corrections(
        self, company_id: Any
    ) -> list[WizardFeedback]:
        company_id = self._require_company_id(company_id)
        stmt = select(WizardFeedback).where(
            and_(
                WizardFeedback.company_id == company_id,
                WizardFeedback.field_corrected.isnot(None),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_filled_outcomes_since(
        self, company_id: Any, cutoff_date: datetime
    ) -> list[JobOutcome]:
        from lia_models.feedback_learning import JobOutcomeType

        company_id = self._require_company_id(company_id)
        stmt = select(JobOutcome).where(
            and_(
                JobOutcome.company_id == company_id,
                JobOutcome.outcome == JobOutcomeType.FILLED,
                JobOutcome.created_at >= cutoff_date,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_filled_with_time_to_fill(self, company_id: Any) -> list[JobOutcome]:
        from lia_models.feedback_learning import JobOutcomeType

        company_id = self._require_company_id(company_id)
        stmt = select(JobOutcome).where(
            and_(
                JobOutcome.company_id == company_id,
                JobOutcome.outcome == JobOutcomeType.FILLED,
                JobOutcome.time_to_fill_days.isnot(None),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_correlation(
        self,
        company_id: Any,
        factor: str,
        outcome_metric: str,
    ) -> OutcomeCorrelation | None:
        company_id = self._require_company_id(company_id)
        stmt = select(OutcomeCorrelation).where(
            and_(
                OutcomeCorrelation.company_id == company_id,
                OutcomeCorrelation.factor == factor,
                OutcomeCorrelation.outcome_metric == outcome_metric,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_correlations_filtered(
        self,
        company_id: Any,
        factor: str | None = None,
        outcome_metric: str | None = None,
    ) -> list[OutcomeCorrelation]:
        company_id = self._require_company_id(company_id)
        conditions = [OutcomeCorrelation.company_id == company_id]
        if factor:
            conditions.append(OutcomeCorrelation.factor == factor)
        if outcome_metric:
            conditions.append(OutcomeCorrelation.outcome_metric == outcome_metric)
        # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
        stmt = select(OutcomeCorrelation).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_wizard_feedback_filtered(
        self,
        company_id: Any,
        cutoff_date: datetime,
        field: str | None = None,
        seniority: str | None = None,
        role_pattern: str | None = None,
    ) -> list[WizardFeedback]:
        company_id = self._require_company_id(company_id)
        conditions = [
            WizardFeedback.company_id == company_id,
            WizardFeedback.created_at >= cutoff_date,
        ]
        if field:
            conditions.append(WizardFeedback.field_corrected == field)
        if seniority:
            conditions.append(func.lower(WizardFeedback.seniority) == seniority.lower())
        if role_pattern:
            conditions.append(WizardFeedback.role.ilike(f"%{role_pattern}%"))
        # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
        stmt = select(WizardFeedback).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_filled_outcomes_filtered(
        self,
        company_id: Any,
        cutoff_date: datetime,
        seniority: str | None = None,
        role_pattern: str | None = None,
    ) -> list[JobOutcome]:
        from lia_models.feedback_learning import JobOutcomeType

        company_id = self._require_company_id(company_id)
        conditions = [
            JobOutcome.company_id == company_id,
            JobOutcome.outcome == JobOutcomeType.FILLED,
            JobOutcome.created_at >= cutoff_date,
        ]
        if seniority:
            conditions.append(func.lower(JobOutcome.seniority) == seniority.lower())
        if role_pattern:
            conditions.append(JobOutcome.role.ilike(f"%{role_pattern}%"))
        # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
        stmt = select(JobOutcome).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_active_pattern_caches(
        self,
        company_id: Any,
        pattern_type: str | None = None,
        pattern_key: str | None = None,
    ) -> list[PatternCache]:
        company_id = self._require_company_id(company_id)
        conditions = [
            PatternCache.company_id == company_id,
            PatternCache.expires_at > datetime.utcnow(),
        ]
        if pattern_type:
            conditions.append(PatternCache.pattern_type == pattern_type)
        if pattern_key:
            conditions.append(PatternCache.pattern_key == pattern_key)
        # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
        stmt = select(PatternCache).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_correction_pattern_by_field(
        self,
        company_id: Any,
        field: str,
        seniority: Any,
    ) -> CorrectionPattern | None:
        company_id = self._require_company_id(company_id)
        stmt = select(CorrectionPattern).where(
            and_(
                CorrectionPattern.company_id == company_id,
                CorrectionPattern.field == field,
                CorrectionPattern.seniority == seniority,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
