"""
Dependency injection for job_vacancies_analytics domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.job_vacancies_analytics_repository import (
    JobVacanciesAnalyticsRepository,
)


def get_job_vacancies_analytics_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> JobVacanciesAnalyticsRepository:
    return JobVacanciesAnalyticsRepository(db)
