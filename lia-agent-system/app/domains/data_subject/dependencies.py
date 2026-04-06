"""Dependency injection factories for the data_subject domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.data_subject.repositories.data_subject_repository import DataSubjectRepository


def get_data_subject_repo(db: AsyncSession = Depends(get_db)) -> DataSubjectRepository:
    return DataSubjectRepository(db)
