"""
Dependency injection factories for the interview_scheduling domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.interview_scheduling.repositories.interview_repository import (
    InterviewRepository,
)


def get_interview_repo(db: AsyncSession = Depends(get_db)) -> InterviewRepository:
    return InterviewRepository(db)
