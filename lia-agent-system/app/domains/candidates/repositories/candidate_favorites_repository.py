"""
CandidateFavoritesRepository and CandidateHiddenRepository —
session-in-constructor pattern.
"""
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import CandidateFavorite, CandidateHidden

logger = logging.getLogger(__name__)


class CandidateFavoritesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, candidate_id: str, user_id: str) -> CandidateFavorite | None:
        result = await self.db.execute(
            select(CandidateFavorite).where(
                CandidateFavorite.candidate_id == candidate_id,
                CandidateFavorite.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, favorite: CandidateFavorite) -> CandidateFavorite:
        self.db.add(favorite)
        await self.db.commit()
        await self.db.refresh(favorite)
        return favorite

    async def update(self, favorite: CandidateFavorite) -> CandidateFavorite:
        await self.db.commit()
        await self.db.refresh(favorite)
        return favorite

    async def remove(self, favorite: CandidateFavorite) -> None:
        await self.db.delete(favorite)
        await self.db.commit()

    async def list_for_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[CandidateFavorite], int]:
        query = (
            select(CandidateFavorite)
            .where(CandidateFavorite.user_id == user_id)
            .order_by(
                CandidateFavorite.is_pinned.desc(),
                CandidateFavorite.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(CandidateFavorite.id)).where(CandidateFavorite.user_id == user_id)
        )
        total = count_result.scalar() or 0
        return items, total


class CandidateHiddenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, candidate_id: str, user_id: str) -> CandidateHidden | None:
        result = await self.db.execute(
            select(CandidateHidden).where(
                CandidateHidden.candidate_id == candidate_id,
                CandidateHidden.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, hidden: CandidateHidden) -> CandidateHidden:
        self.db.add(hidden)
        await self.db.commit()
        await self.db.refresh(hidden)
        return hidden

    async def remove(self, hidden: CandidateHidden) -> None:
        await self.db.delete(hidden)
        await self.db.commit()

    async def list_for_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[CandidateHidden], int]:
        query = (
            select(CandidateHidden)
            .where(CandidateHidden.user_id == user_id)
            .order_by(CandidateHidden.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(CandidateHidden.id)).where(CandidateHidden.user_id == user_id)
        )
        total = count_result.scalar() or 0
        return items, total
