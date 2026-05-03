"""
Dependency injection for candidates domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.candidates.repositories.candidate_favorites_repository import (
    CandidateFavoritesRepository,
    CandidateHiddenRepository,
)
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository


def get_candidate_repo(db: AsyncSession = Depends(get_tenant_db)) -> CandidateRepository:
    return CandidateRepository(db)


def get_vacancy_candidate_repo(db: AsyncSession = Depends(get_tenant_db)) -> VacancyCandidateRepository:
    return VacancyCandidateRepository(db)


def get_candidate_favorites_repo(db: AsyncSession = Depends(get_tenant_db)) -> CandidateFavoritesRepository:
    return CandidateFavoritesRepository(db)


def get_candidate_hidden_repo(db: AsyncSession = Depends(get_tenant_db)) -> CandidateHiddenRepository:
    return CandidateHiddenRepository(db)
