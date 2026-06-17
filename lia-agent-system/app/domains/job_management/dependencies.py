from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_tenant_db
from app.domains.job_management.repositories.job_vacancy_lifecycle_repository import JobVacancyLifecycleRepository


def get_job_vacancy_lifecycle_repo(db: AsyncSession = Depends(get_tenant_db)) -> JobVacancyLifecycleRepository:
    return JobVacancyLifecycleRepository(db)
from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository


def get_job_vacancy_crud_repo(db: AsyncSession = Depends(get_tenant_db)) -> JobVacancyCRUDRepository:
    return JobVacancyCRUDRepository(db)
from app.domains.job_management.repositories.job_vacancy_public_repository import JobVacancyPublicRepository


def get_job_vacancy_public_repo(db: AsyncSession = Depends(get_tenant_db)) -> JobVacancyPublicRepository:
    return JobVacancyPublicRepository(db)
from app.domains.job_management.repositories.job_vacancy_screening_repository import JobVacancyScreeningRepository


def get_job_vacancy_screening_repo(db: AsyncSession = Depends(get_tenant_db)) -> JobVacancyScreeningRepository:
    return JobVacancyScreeningRepository(db)
