from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository


def get_screening_repo(db: AsyncSession = Depends(get_db)) -> ScreeningRepository:
    return ScreeningRepository(db)

from app.domains.cv_screening.services.screening_question_set_service import (
    ScreeningQuestionSetService,
    get_screening_question_set_service,
)

__all__ = [
    "get_screening_repo",
    "ScreeningQuestionSetService",
    "get_screening_question_set_service",
]
