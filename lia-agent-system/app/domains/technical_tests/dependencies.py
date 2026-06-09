"""
Dependency injection for technical_tests domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.technical_tests_repository import (
    TechnicalTestsRepository,
)


def get_technical_tests_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> TechnicalTestsRepository:
    return TechnicalTestsRepository(db)
