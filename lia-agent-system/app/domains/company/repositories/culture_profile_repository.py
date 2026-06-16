"""CultureProfileRepository - for CompanyCultureProfile model."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_culture import CompanyCultureProfile

logger = logging.getLogger(__name__)


class CultureProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_company(self, company_id: UUID) -> CompanyCultureProfile | None:
        result = await self.db.execute(
            select(CompanyCultureProfile).where(CompanyCultureProfile.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> CompanyCultureProfile:
        cp = CompanyCultureProfile(**data)
        self.db.add(cp)
        await self.db.commit()
        await self.db.refresh(cp)
        return cp

    async def update(self, company_id: UUID, data: dict) -> CompanyCultureProfile | None:
        cp = await self.get_for_company(company_id)
        if not cp:
            return None
        for key, value in data.items():
            if hasattr(cp, key):
                setattr(cp, key, value)
        await self.db.commit()
        await self.db.refresh(cp)
        return cp

    async def create_or_update(self, company_id: UUID, data: dict) -> CompanyCultureProfile:
        cp = await self.get_for_company(company_id)
        if cp:
            for key, value in data.items():
                if hasattr(cp, key):
                    setattr(cp, key, value)
        else:
            cp = CompanyCultureProfile(company_id=company_id, **data)
            self.db.add(cp)
        await self.db.commit()
        await self.db.refresh(cp)
        return cp

    async def get_for_agent_context(
        self, company_id: UUID
    ) -> CompanyCultureProfile | None:
        """Approval gate (Fase 5.1, 2026-06-04). Return the culture profile ONLY
        when eligible to feed agent prompts: human-authored (source != 'auto') OR
        an auto profile a human has approved (is_approved). Auto profiles pending
        approval are WITHHELD — ghost-context gate (LGPD/bias). UI/approval flows
        must call get_for_company() to see pending profiles."""
        profile = await self.get_for_company(company_id)
        if profile is None:
            return None
        if getattr(profile, "source", None) == "auto" and not getattr(
            profile, "is_approved", False
        ):
            return None
        return profile

    async def set_approval(
        self, company_id: UUID, *, approved: bool, user_id: UUID | None = None
    ) -> CompanyCultureProfile | None:
        """Approve/reject the company's auto culture profile (HITL gate)."""
        from datetime import datetime

        cp = await self.get_for_company(company_id)
        if cp is None:
            return None
        cp.is_approved = approved
        cp.approved_at = datetime.utcnow() if approved else None
        cp.approved_by_user_id = user_id if approved else None
        await self.db.commit()
        await self.db.refresh(cp)
        return cp
