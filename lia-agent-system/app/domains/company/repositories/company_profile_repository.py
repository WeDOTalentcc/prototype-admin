"""
CompanyProfileRepository - session-in-constructor pattern.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Benefit, CompanyProfile, CultureValue, Department

logger = logging.getLogger(__name__)


class CompanyProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, profile_id: UUID) -> CompanyProfile | None:
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client_account(self, client_account_id: str) -> CompanyProfile | None:
        result = await self.db.execute(
            select(CompanyProfile).where(
                CompanyProfile.client_account_id == client_account_id
            )
        )
        return result.scalars().first()

    async def get_default(self) -> CompanyProfile | None:
        result = await self.db.execute(
            select(CompanyProfile)
            .where(CompanyProfile.is_default)
            .order_by(CompanyProfile.created_at)
            .limit(1)
        )
        return result.scalars().first()

    async def get_latest_default(self) -> CompanyProfile | None:
        """Most recently created default profile (created_at desc)."""
        result = await self.db.execute(
            select(CompanyProfile)
            .where(CompanyProfile.is_default)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def get_latest_active(self) -> CompanyProfile | None:
        """Most recently created active profile (created_at desc)."""
        result = await self.db.execute(
            select(CompanyProfile)
            .where(CompanyProfile.is_active)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def list_for_company(
        self, company_id: str, skip: int = 0, limit: int = 100
    ) -> list[CompanyProfile]:
        result = await self.db.execute(
            select(CompanyProfile)
            .where(CompanyProfile.client_account_id == company_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, data: dict, set_default: bool = True) -> CompanyProfile:
        existing_default = await self.get_default()
        profile = CompanyProfile(**data)
        if set_default and not existing_default:
            profile.is_default = True
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update(self, profile_id: UUID, data: dict) -> CompanyProfile | None:
        profile = await self.get_by_id(profile_id)
        if not profile:
            return None
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def delete(self, profile_id: UUID) -> bool:
        profile = await self.get_by_id(profile_id)
        if not profile:
            return False
        await self.db.delete(profile)
        await self.db.commit()
        return True

    async def get_with_relations(self, profile_id: UUID) -> dict:
        profile = await self.get_by_id(profile_id)
        if not profile:
            return {}

        deps_result = await self.db.execute(
            select(Department).where(
                Department.company_id == profile_id,
                Department.is_active,
            )
        )
        departments = list(deps_result.scalars().all())

        bens_result = await self.db.execute(
            select(Benefit).where(
                Benefit.company_id == profile_id,
                Benefit.is_active,
            )
        )
        benefits = list(bens_result.scalars().all())

        vals_result = await self.db.execute(
            select(CultureValue).where(
                CultureValue.company_id == profile_id,
                CultureValue.is_active,
            )
        )
        culture_values = list(vals_result.scalars().all())

        return {
            "profile": profile,
            "departments": departments,
            "benefits": benefits,
            "culture_values": culture_values,
        }
