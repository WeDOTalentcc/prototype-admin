from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.job_management.repositories.job_vacancy_lifecycle_repository import JobVacancyLifecycleRepository


def get_job_vacancy_lifecycle_repo(db: AsyncSession = Depends(get_db)) -> JobVacancyLifecycleRepository:
    return JobVacancyLifecycleRepository(db)
