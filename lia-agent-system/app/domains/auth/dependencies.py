"""Dependency injection functions for auth domain repositories."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lia_config.database import get_db
from app.domains.auth.repositories.user_repository import UserRepository
from app.domains.auth.repositories.workos_repository import WorkOSRepository


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_workos_repo(db: AsyncSession = Depends(get_db)) -> WorkOSRepository:
    return WorkOSRepository(db)
