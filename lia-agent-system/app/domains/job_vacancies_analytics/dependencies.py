"""
Dependency injection for job_vacancies_analytics domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.job_vacancies_analytics.repositories.job_vacancies_analytics_repository import (
    JobVacanciesAnalyticsRepository,
)


def get_job_vacancies_analytics_repo(
    db: AsyncSession = Depends(get_db),
) -> JobVacanciesAnalyticsRepository:
    return JobVacanciesAnalyticsRepository(db)
