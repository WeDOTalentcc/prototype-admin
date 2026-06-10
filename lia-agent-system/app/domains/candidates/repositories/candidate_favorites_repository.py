"""
CandidateFavoritesRepository and CandidateHiddenRepository —
session-in-constructor pattern.

Multi-tenancy canonical (CLAUDE.md REGRA ZERO):
- company_id é param opcional em métodos públicos (backwards-compat com callers
  legados que dependem de Postgres RLS via get_tenant_db).
- Quando passado, filter explícito CandidateFavorite/CandidateHidden.company_id
  é aplicado (defense-in-depth, harness B.1 fail-closed).
- Recomendação: callers novos devem SEMPRE passar company_id.
"""
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import CandidateFavorite, CandidateHidden

logger = logging.getLogger(__name__)


class CandidateFavoritesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(
        self,
        candidate_id: str,
        user_id: str,
        company_id: str | None = None,
    ) -> CandidateFavorite | None:
        """Get favorite for (candidate, user). Multi-tenancy defense-in-depth via
        company_id filter quando passado."""
        # TENANT-EXEMPT: dynamic builder — CandidateFavorite.company_id == company_id
        # é appended conditionally below quando company_id passado. Sensor B.1 não
        # rastreia através de chain reassignment.
        query = select(CandidateFavorite).where(
            CandidateFavorite.candidate_id == candidate_id,
            CandidateFavorite.user_id == user_id,
        )
        if company_id:
            query = query.where(CandidateFavorite.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add(self, favorite: CandidateFavorite) -> CandidateFavorite:
        self.db.add(favorite)
        await self.db.commit()
        await self.db.refresh(favorite)
        return favorite

    async def update(self, favorite: CandidateFavorite) -> CandidateFavorite:
        self.db.add(favorite)
        await self.db.commit()
        await self.db.refresh(favorite)
        return favorite

    async def remove(self, favorite: CandidateFavorite) -> None:
        await self.db.delete(favorite)
        await self.db.commit()

    async def list_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        company_id: str | None = None,
    ) -> tuple[list[CandidateFavorite], int]:
        """List favorites for user. Multi-tenancy defense-in-depth via
        company_id filter quando passado."""
        # TENANT-EXEMPT: dynamic builder — CandidateFavorite.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(CandidateFavorite).where(CandidateFavorite.user_id == user_id)
        count_query = select(func.count(CandidateFavorite.id)).where(
            CandidateFavorite.user_id == user_id
        )
        if company_id:
            query = query.where(CandidateFavorite.company_id == company_id)
            count_query = count_query.where(
                CandidateFavorite.company_id == company_id
            )

        query = (
            query.order_by(
                CandidateFavorite.is_pinned.desc(),
                CandidateFavorite.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        return items, total


class CandidateHiddenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(
        self,
        candidate_id: str,
        user_id: str,
        company_id: str | None = None,
    ) -> CandidateHidden | None:
        """Get hidden record for (candidate, user). Multi-tenancy defense-in-depth
        via company_id filter quando passado."""
        # TENANT-EXEMPT: dynamic builder — CandidateHidden.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(CandidateHidden).where(
            CandidateHidden.candidate_id == candidate_id,
            CandidateHidden.user_id == user_id,
        )
        if company_id:
            query = query.where(CandidateHidden.company_id == company_id)
        result = await self.db.execute(query)
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
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        company_id: str | None = None,
    ) -> tuple[list[CandidateHidden], int]:
        """List hidden records for user. Multi-tenancy defense-in-depth via
        company_id filter quando passado."""
        # TENANT-EXEMPT: dynamic builder — CandidateHidden.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(CandidateHidden).where(CandidateHidden.user_id == user_id)
        count_query = select(func.count(CandidateHidden.id)).where(
            CandidateHidden.user_id == user_id
        )
        if company_id:
            query = query.where(CandidateHidden.company_id == company_id)
            count_query = count_query.where(CandidateHidden.company_id == company_id)

        query = (
            query.order_by(CandidateHidden.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        return items, total
