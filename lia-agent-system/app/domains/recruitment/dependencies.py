"""
Dependency injection functions for recruitment domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db

from .repositories.ats_mapping_repository import ATSMappingRepository
from .repositories.recruitment_stage_repository import RecruitmentStageRepository
from .repositories.screening_question_repository import ScreeningQuestionRepository
from .repositories.stage_history_repository import StageHistoryRepository
from .repositories.sub_status_repository import SubStatusRepository


def get_stage_repo(db: AsyncSession = Depends(get_tenant_db)) -> RecruitmentStageRepository:
    return RecruitmentStageRepository(db)


def get_sub_status_repo(db: AsyncSession = Depends(get_tenant_db)) -> SubStatusRepository:
    return SubStatusRepository(db)


def get_ats_mapping_repo(db: AsyncSession = Depends(get_tenant_db)) -> ATSMappingRepository:
    return ATSMappingRepository(db)


def get_screening_question_repo(db: AsyncSession = Depends(get_tenant_db)) -> ScreeningQuestionRepository:
    return ScreeningQuestionRepository(db)


def get_stage_history_repo(db: AsyncSession = Depends(get_tenant_db)) -> StageHistoryRepository:
    return StageHistoryRepository(db)


from .repositories.application_repository import ApplicationRepository


def get_application_repo(db: AsyncSession = Depends(get_tenant_db)) -> ApplicationRepository:
    return ApplicationRepository(db)
