"""
Dependency injection functions for the recruitment_journey domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.recruitment_journey.repositories.recruitment_journey_repository import (
    RecruitmentJourneyRepository,
)


def get_recruitment_journey_repo(
    db: AsyncSession = Depends(get_db),
) -> RecruitmentJourneyRepository:
    return RecruitmentJourneyRepository(db)
