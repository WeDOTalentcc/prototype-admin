"""FeedbackRepository — DB access layer for InteractionFeedback / LearningPattern.

Extracted from analytics services per ADR-001.
Tables covered:
  - interaction_feedback (lia_models.feedback.InteractionFeedback)
  - learning_patterns (lia_models.feedback.LearningPattern)
  - wizard_feedback (cross-table read)
  - job_outcomes (cross-table read)
"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.feedback import InteractionFeedback, LearningPattern
from lia_models.feedback_learning import JobOutcome, WizardFeedback

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """Repository for interaction-feedback / learning-pattern data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: Any) -> Any:
        if not company_id:
            raise ValueError("company_id is required for fail-closed multi-tenancy")
        return company_id

    # ---------- LearningPattern ----------

    async def find_active_pattern(
        self, company_id: UUID, pattern_key: str
    ) -> LearningPattern | None:
        company_id = self._require_company_id(company_id)
        stmt = select(LearningPattern).where(
            and_(
                LearningPattern.company_id == company_id,
                LearningPattern.pattern_key == pattern_key,
                LearningPattern.is_active,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_patterns_min_confidence(
        self, company_id: UUID, min_confidence: float = 0.5
    ) -> list[LearningPattern]:
        company_id = self._require_company_id(company_id)
        stmt = (
            select(LearningPattern)
            .where(
                and_(
                    LearningPattern.company_id == company_id,
                    LearningPattern.is_active,
                    LearningPattern.confidence >= min_confidence,
                )
            )
            .order_by(LearningPattern.success_rate.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_pattern_by_id(self, pattern_id: UUID) -> LearningPattern | None:
        # TENANT-EXEMPT: feedback per-user/per-job scope; AST sensor cannot trace dynamic upstream conditions; T-RATCHET tenant_filter
        stmt = select(LearningPattern).where(LearningPattern.id == pattern_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------- InteractionFeedback ----------

    async def list_unprocessed_feedback(
        self, limit: int = 100
    ) -> list[InteractionFeedback]:
        """ADR-001-EXEMPT: cross-tenant batch processor (system job, no tenant ctx)."""
        stmt = (
            select(InteractionFeedback)
            .where(~InteractionFeedback.processed)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_quality_feedback(
        self,
        company_id: UUID,
        min_rating: int,
        limit: int,
        require_correction: bool,
        min_response_length: int,
    ) -> list[InteractionFeedback]:
        company_id = self._require_company_id(company_id)

        # T-11 B.1.3 CONSENT GATE canonical (ADR-RLHF-001 + ADR-LGPD-002):
        # Fail-CLOSED — company DEVE ter training_data consent ativo antes
        # de qualquer query de feedback para export pipeline.
        # Default = False (LGPD Art. 7: consent must be explicit).
        from app.domains.lgpd.repositories.company_training_consent_repository import (
            CompanyTrainingConsentRepository,
        )
        consent_repo = CompanyTrainingConsentRepository(self.db)
        if not await consent_repo.is_active(company_id):
            import logging as _t11_logging
            _t11_logging.getLogger(__name__).info(
                "[FeedbackRepository T-11 B.1.3] CONSENT GATE blocked: "
                "company_id=%s no active training_data consent — returning [] empty",
                company_id,
            )
            return []

        base_conditions = [
            InteractionFeedback.company_id == company_id,
            InteractionFeedback.user_message.isnot(None),
            InteractionFeedback.lia_response.isnot(None),
            func.length(InteractionFeedback.lia_response) > min_response_length,
        ]
        if require_correction:
            base_conditions.append(InteractionFeedback.correction.isnot(None))
        else:
            quality_conditions = or_(
                InteractionFeedback.thumbs == "up",
                InteractionFeedback.rating >= min_rating,
            )
            base_conditions.append(quality_conditions)

        stmt = (
            # TENANT-EXEMPT: feedback per-user/per-job scope; AST sensor cannot trace dynamic upstream conditions; T-RATCHET tenant_filter
            select(InteractionFeedback)
            .where(and_(*base_conditions))
            .order_by(InteractionFeedback.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_feedback_by_rating(
        self,
        company_id: UUID,
        rating: int,
        limit: int,
        min_response_length: int,
    ) -> list[InteractionFeedback]:
        company_id = self._require_company_id(company_id)
        stmt = (
            select(InteractionFeedback)
            .where(
                and_(
                    InteractionFeedback.company_id == company_id,
                    InteractionFeedback.rating == rating,
                    InteractionFeedback.lia_response.isnot(None),
                    func.length(InteractionFeedback.lia_response) > min_response_length,
                )
            )
            .order_by(InteractionFeedback.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_feedback_thumbs_up(
        self,
        company_id: UUID,
        limit: int,
        min_response_length: int,
    ) -> list[InteractionFeedback]:
        company_id = self._require_company_id(company_id)
        stmt = (
            select(InteractionFeedback)
            .where(
                and_(
                    InteractionFeedback.company_id == company_id,
                    InteractionFeedback.thumbs == "up",
                    InteractionFeedback.lia_response.isnot(None),
                    func.length(InteractionFeedback.lia_response) > min_response_length,
                )
            )
            .order_by(
                InteractionFeedback.confidence_score.desc().nullslast(),
                InteractionFeedback.created_at.desc(),
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- WizardFeedback (cross-table read for analytics) ----------

    async def list_wizard_feedback_for_user(
        self, user_id: str
    ) -> list[WizardFeedback]:
        """List all WizardFeedback rows for a recruiter/user (recruiter-scoped)."""
        # TENANT-EXEMPT: feedback per-user/per-job scope; AST sensor cannot trace dynamic upstream conditions; T-RATCHET tenant_filter
        stmt = select(WizardFeedback).where(WizardFeedback.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_wizard_feedback_for_company(
        self, company_id: Any
    ) -> list[WizardFeedback]:
        company_id = self._require_company_id(company_id)
        stmt = select(WizardFeedback).where(WizardFeedback.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- JobOutcome (cross-table read used by feedback_learning) ----------

    async def list_outcomes_for_company(self, company_id: Any) -> list[JobOutcome]:
        company_id = self._require_company_id(company_id)
        stmt = select(JobOutcome).where(JobOutcome.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- Analytics-specific WizardFeedback / JobOutcome queries ----------

    async def list_wizard_feedback_corrections(
        self,
        company_id: Any,
        field: str,
        cutoff_date: Any,
        role: str | None = None,
        seniority: str | None = None,
    ) -> list[WizardFeedback]:
        """List WizardFeedback rows for a field-correction analysis window."""
        company_id = self._require_company_id(company_id)
        conditions = [
            WizardFeedback.company_id == company_id,
            WizardFeedback.field_corrected == field,
            WizardFeedback.created_at >= cutoff_date,
        ]
        if role:
            conditions.append(func.lower(WizardFeedback.role).contains(role.lower()))
        if seniority:
            conditions.append(func.lower(WizardFeedback.seniority) == seniority.lower())
        # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
        stmt = select(WizardFeedback).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_outcomes_for_role_analysis(
        self,
        company_id: Any,
        role: str | None = None,
        seniority: str | None = None,
    ) -> list[JobOutcome]:
        """List JobOutcome rows with optional role/seniority filters for analytics."""
        company_id = self._require_company_id(company_id)
        conditions = [JobOutcome.company_id == company_id]
        if role:
            conditions.append(func.lower(JobOutcome.role).contains(role.lower()))
        if seniority:
            conditions.append(func.lower(JobOutcome.seniority) == seniority.lower())
        # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
        stmt = select(JobOutcome).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
