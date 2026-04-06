"""
Dependency injection for technical_tests domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.technical_tests.repositories.technical_tests_repository import (
    TechnicalTestsRepository,
)


def get_technical_tests_repo(
    db: AsyncSession = Depends(get_db),
) -> TechnicalTestsRepository:
    return TechnicalTestsRepository(db)
