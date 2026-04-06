"""
Dependency injection functions for the company_culture domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.company_culture.repositories.company_culture_repository import (
    CompanyCultureRepository,
)


def get_company_culture_repo(
    db: AsyncSession = Depends(get_db),
) -> CompanyCultureRepository:
    return CompanyCultureRepository(db)
