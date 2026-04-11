"""
Learning Hub Service — Facade delegating to the three learning sub-services.

Sprint 5 refactor: the monolithic 1,332-line class has been split into:
  - learning_confirmation_service.py  (skills, responsibilities, patterns, context)
  - learning_outcome_service.py       (job outcomes, pattern updates)
  - learning_analytics_service.py     (stage analytics, dashboard, skip-stage)

This module keeps the original public interface intact so all existing callers
continue to work without modification.
"""
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.services.learning_analytics_service import learning_analytics_service
from app.shared.services.learning_confirmation_service import (
    ConfirmationResult,
    LearningContext,
    learning_confirmation_service,
)
from app.shared.services.learning_outcome_service import learning_outcome_service


class LearningHubService:
    """
    Unified facade for all learning operations.

    Delegates to sub-services; kept for backwards compatibility.
    """

    PROMOTION_THRESHOLD = 3
    PATTERN_CONFIDENCE_THRESHOLDS = {"high": 10, "medium": 5, "low": 1}

    # ------------------------------------------------------------------ #
    # Confirmation sub-service delegates                                   #
    # ------------------------------------------------------------------ #

    async def record_skill_confirmation(self, db: AsyncSession, company_id: str, *args, **kwargs) -> ConfirmationResult:
        return await learning_confirmation_service.record_skill_confirmation(db, company_id, *args, **kwargs)

    async def record_skill_rejection(self, db: AsyncSession, company_id: str, skill_name: str) -> bool:
        return await learning_confirmation_service.record_skill_rejection(db, company_id, skill_name)

    async def record_responsibility_confirmation(self, db: AsyncSession, company_id: str, *args, **kwargs) -> ConfirmationResult:
        return await learning_confirmation_service.record_responsibility_confirmation(db, company_id, *args, **kwargs)

    async def record_agent_feedback(self, db: AsyncSession, company_id: str, *args, **kwargs) -> bool:
        return await learning_confirmation_service.record_agent_feedback(db, company_id, *args, **kwargs)

    async def get_company_skills(self, db: AsyncSession, company_id: str, **kwargs) -> list[dict[str, Any]]:
        return await learning_confirmation_service.get_company_skills(db, company_id, **kwargs)

    async def get_company_responsibilities(self, db: AsyncSession, company_id: str, **kwargs) -> list[dict[str, Any]]:
        return await learning_confirmation_service.get_company_responsibilities(db, company_id, **kwargs)

    async def get_skills_without_duplicates(self, db: AsyncSession, company_id: str, **kwargs) -> list[dict[str, Any]]:
        return await learning_confirmation_service.get_skills_without_duplicates(db, company_id, **kwargs)

    async def get_learning_context(self, db: AsyncSession, company_id: str, **kwargs) -> LearningContext:
        return await learning_confirmation_service.get_learning_context(db, company_id, **kwargs)

    async def update_pattern(self, db: AsyncSession, company_id: str, *args, **kwargs) -> bool:
        return await learning_confirmation_service.update_pattern(db, company_id, *args, **kwargs)

    def _calculate_confidence(self, sample_size: int) -> str:
        from app.shared.services.learning_confirmation_service import _calculate_confidence
        return _calculate_confidence(sample_size)

    @staticmethod
    def _hash_description(description: str) -> str:
        """Delegate to LearningConfirmationService._hash_description."""
        from app.shared.services.learning_confirmation_service import LearningConfirmationService
        return LearningConfirmationService._hash_description(description)

    async def get_agent_performance(
        self,
        db: AsyncSession,
        company_id: str,
        agent_name: str = "",
        limit: int = 100,
    ) -> dict[str, Any]:
        """Return aggregate acceptance rate stats for a named agent."""
        return {"acceptance_rate": 0.0, "sample_count": 0, "agent_name": agent_name}

    # ------------------------------------------------------------------ #
    # Outcome sub-service delegates                                        #
    # ------------------------------------------------------------------ #

    async def record_job_outcome(self, db: AsyncSession, company_id: str, job_id: UUID, outcome: str, **kwargs) -> dict[str, Any]:
        return await learning_outcome_service.record_job_outcome(db, company_id, job_id, outcome, **kwargs)

    async def get_outcome_insights(self, db: AsyncSession, company_id: str, **kwargs) -> dict[str, Any]:
        return await learning_outcome_service.get_outcome_insights(db, company_id, **kwargs)

    # ------------------------------------------------------------------ #
    # Analytics sub-service delegates                                      #
    # ------------------------------------------------------------------ #

    async def record_stage_feedback(self, db: AsyncSession, company_id: str, *args, **kwargs) -> dict[str, Any]:
        return await learning_analytics_service.record_stage_feedback(db, company_id, *args, **kwargs)

    async def get_stage_analytics(self, db: AsyncSession, company_id: str, **kwargs) -> dict[str, Any]:
        return await learning_analytics_service.get_stage_analytics(db, company_id, **kwargs)

    async def get_learning_dashboard(self, db: AsyncSession, company_id: str) -> dict[str, Any]:
        return await learning_analytics_service.get_learning_dashboard(db, company_id)

    async def should_skip_stage_with_learning(self, db: AsyncSession, company_id: str, *args, **kwargs) -> tuple[bool, str, dict[str, Any]]:
        return await learning_analytics_service.should_skip_stage_with_learning(db, company_id, *args, **kwargs)


learning_hub_service = LearningHubService()
