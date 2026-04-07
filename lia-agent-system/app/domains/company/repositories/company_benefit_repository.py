"""
CompanyBenefit Repository — data access layer for company-specific benefits.
Extracted from app/api/v1/company_benefits.py as part of Phase 2 refactor.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_benefit import DEFAULT_BRAZILIAN_BENEFITS, CompanyBenefit

logger = logging.getLogger(__name__)


class CompanyBenefitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        active_only: bool = True,
        category: str | None = None,
        search: str | None = None,
    ) -> list[CompanyBenefit]:
        query = select(CompanyBenefit).where(CompanyBenefit.company_id == company_id)
        if active_only:
            query = query.where(CompanyBenefit.is_active.is_(True))
        if category:
            query = query.where(CompanyBenefit.category == category)
        if search:
            term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(CompanyBenefit.name).like(term),
                    func.lower(CompanyBenefit.description).like(term),
                )
            )
        query = query.order_by(CompanyBenefit.order, CompanyBenefit.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, benefit_id: UUID) -> CompanyBenefit | None:
        result = await self.db.execute(
            select(CompanyBenefit).where(CompanyBenefit.id == benefit_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, company_id: str, name: str) -> CompanyBenefit | None:
        result = await self.db.execute(
            select(CompanyBenefit).where(
                CompanyBenefit.company_id == company_id,
                CompanyBenefit.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, company_id: str, data: dict) -> CompanyBenefit:
        benefit = CompanyBenefit(company_id=company_id, **data)
        self.db.add(benefit)
        await self.db.flush()
        await self.db.refresh(benefit)
        return benefit

    async def update(self, benefit: CompanyBenefit, data: dict) -> CompanyBenefit:
        data["updated_at"] = datetime.utcnow()
        for key, value in data.items():
            setattr(benefit, key, value)
        await self.db.flush()
        await self.db.refresh(benefit)
        return benefit

    async def soft_delete(self, benefit: CompanyBenefit) -> None:
        benefit.is_active = False
        benefit.updated_at = datetime.utcnow()

    async def hard_delete(self, benefit: CompanyBenefit) -> None:
        await self.db.delete(benefit)

    async def count_for_company(self, company_id: str) -> int:
        result = await self.db.execute(
            select(func.count(CompanyBenefit.id)).where(
                CompanyBenefit.company_id == company_id
            )
        )
        return result.scalar() or 0

    async def seed_defaults(self, company_id: str) -> int:
        created = 0
        for bdata in DEFAULT_BRAZILIAN_BENEFITS:
            if not await self.get_by_name(company_id, bdata["name"]):
                self.db.add(CompanyBenefit(company_id=company_id, **bdata))
                created += 1
        return created
