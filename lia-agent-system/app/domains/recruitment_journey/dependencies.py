"""
Dependency injection functions for the recruitment_journey domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.recruitment_journey_repository import (
    RecruitmentJourneyRepository,
)


def get_recruitment_journey_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> RecruitmentJourneyRepository:
    return RecruitmentJourneyRepository(db)
