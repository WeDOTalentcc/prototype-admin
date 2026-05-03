"""
Dependency injection factories for the interview_scheduling domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.interview_scheduling.repositories.interview_repository import (
    InterviewRepository,
)


def get_interview_repo(db: AsyncSession = Depends(get_tenant_db)) -> InterviewRepository:
    return InterviewRepository(db)

from app.domains.interview_scheduling.repositories.scheduling_repository import (
    SchedulingRepository,
)


def get_scheduling_repo(db: AsyncSession = Depends(get_tenant_db)) -> SchedulingRepository:
    return SchedulingRepository(db)
