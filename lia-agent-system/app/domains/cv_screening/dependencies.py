from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_tenant_db
from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository


def get_screening_repo(db: AsyncSession = Depends(get_tenant_db)) -> ScreeningRepository:
    return ScreeningRepository(db)

from app.domains.cv_screening.services.cv_parser import CVParserService, get_cv_parser_service
from app.domains.cv_screening.services.screening_question_set_service import (
    ScreeningQuestionSetService,
    get_screening_question_set_service,
)
from app.domains.cv_screening.services.wsi_service import WSIService, wsi_service as _wsi_singleton


def get_wsi_service() -> WSIService:
    return _wsi_singleton


from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService, rubric_evaluation_service as _rubric_singleton


def get_rubric_evaluation_service() -> RubricEvaluationService:
    return _rubric_singleton


__all__ = [
    "get_screening_repo",
    "CVParserService",
    "get_cv_parser_service",
    "ScreeningQuestionSetService",
    "get_screening_question_set_service",
    "WSIService",
    "get_wsi_service",
    "RubricEvaluationService",
    "get_rubric_evaluation_service",
]
