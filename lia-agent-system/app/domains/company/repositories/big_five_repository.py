"""BigFiveRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import BigFiveQuestion, BigFiveRoleProfile

logger = logging.getLogger(__name__)


class BigFiveRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_questions(self, trait: str | None = None) -> list[BigFiveQuestion]:
        query = select(BigFiveQuestion).where(BigFiveQuestion.is_active)
        if trait:
            query = query.where(BigFiveQuestion.trait == trait)
        query = query.order_by(BigFiveQuestion.trait, BigFiveQuestion.order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_question(self, q_id: UUID) -> BigFiveQuestion | None:
        result = await self.db.execute(
            select(BigFiveQuestion).where(BigFiveQuestion.id == q_id)
        )
        return result.scalar_one_or_none()

    async def create_question(self, data: dict) -> BigFiveQuestion:
        q = BigFiveQuestion(**data)
        self.db.add(q)
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def update_question(self, q_id: UUID, data: dict) -> BigFiveQuestion | None:
        q = await self.get_question(q_id)
        if not q:
            return None
        for key, value in data.items():
            if hasattr(q, key):
                setattr(q, key, value)
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def delete_question(self, q_id: UUID) -> bool:
        q = await self.get_question(q_id)
        if not q:
            return False
        q.is_active = False
        await self.db.commit()
        return True

    async def list_role_profiles(self, company_id: UUID) -> list[BigFiveRoleProfile]:
        result = await self.db.execute(
            select(BigFiveRoleProfile)
            .where(
                or_(
                    BigFiveRoleProfile.company_id == company_id,
                    BigFiveRoleProfile.company_id.is_(None),
                )
            )
            .order_by(BigFiveRoleProfile.name)
        )
        return list(result.scalars().all())

    async def get_role_profile(
        self,
        rp_id: UUID,
        company_id: UUID | None = None,
    ) -> BigFiveRoleProfile | None:
        """Get role profile by id. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1).

        Note: shared profiles (company_id IS NULL) são default templates;
        quando company_id é passado, retorna o tenant profile específico.
        """
        # TENANT-EXEMPT: dynamic builder — BigFiveRoleProfile.company_id ==
        # company_id é appended conditionally below quando company_id passado.
        query = select(BigFiveRoleProfile).where(BigFiveRoleProfile.id == rp_id)
        if company_id:
            query = query.where(
                or_(
                    BigFiveRoleProfile.company_id == company_id,
                    BigFiveRoleProfile.company_id.is_(None),
                )
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_role_profile(self, data: dict) -> BigFiveRoleProfile:
        rp = BigFiveRoleProfile(**data)
        self.db.add(rp)
        await self.db.commit()
        await self.db.refresh(rp)
        return rp

    async def update_role_profile(
        self, rp_id: UUID, data: dict
    ) -> BigFiveRoleProfile | None:
        rp = await self.get_role_profile(rp_id)
        if not rp:
            return None
        for key, value in data.items():
            if hasattr(rp, key):
                setattr(rp, key, value)
        await self.db.commit()
        await self.db.refresh(rp)
        return rp

    async def delete_role_profile(self, rp_id: UUID) -> bool:
        rp = await self.get_role_profile(rp_id)
        if not rp:
            return False
        rp.is_active = False
        await self.db.commit()
        return True
