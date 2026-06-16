"""BenefitTemplateRepository — DB operations for BenefitTemplate model.

Extracted from app/api/v1/benefits.py as part of Phase 2 refactor.
Note: benefit_repository.py covers the Benefit model (company-specific benefits).
"""
import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import BenefitTemplate

logger = logging.getLogger(__name__)


class BenefitTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_templates(
        self,
        *,
        category: str | None = None,
        search: str | None = None,
        popular_only: bool = False,
    ) -> list[BenefitTemplate]:
        """List active benefit templates with optional filters."""
        query = select(BenefitTemplate).where(BenefitTemplate.is_active)

        if category:
            query = query.where(BenefitTemplate.category == category)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(BenefitTemplate.name).like(search_term),
                    func.lower(BenefitTemplate.description).like(search_term),
                )
            )

        if popular_only:
            query = query.where(BenefitTemplate.is_popular)

        query = query.order_by(
            BenefitTemplate.category, BenefitTemplate.order, BenefitTemplate.name
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, template_id: UUID) -> BenefitTemplate | None:
        result = await self.db.execute(
            select(BenefitTemplate).where(BenefitTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count(BenefitTemplate.id)))
        return result.scalar() or 0

    async def get_by_name(self, name: str) -> BenefitTemplate | None:
        result = await self.db.execute(
            select(BenefitTemplate).where(BenefitTemplate.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, template: BenefitTemplate) -> BenefitTemplate:
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template
