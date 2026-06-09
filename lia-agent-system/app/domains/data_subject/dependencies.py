"""Dependency injection factories for the data_subject domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.data_subject_repository import DataSubjectRepository


def get_data_subject_repo(db: AsyncSession = Depends(get_tenant_db)) -> DataSubjectRepository:
    return DataSubjectRepository(db)
