"""
FastAPI dependency providers for the candidate_lists domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.candidate_list_repository import (
    CandidateListRepository,
)


def get_candidate_list_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> CandidateListRepository:
    return CandidateListRepository(db)
