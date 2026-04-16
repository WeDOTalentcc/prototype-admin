"""
CompanyRetentionRepository — data access for company data retention policies.
Extracted from app/api/v1/company_retention.py as part of Phase 2 refactor.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CompanyRetentionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_company_id(self, company_id: str):
        """Return CompanyRetentionPolicy for company, or None."""
        from lia_models.retention_policy import CompanyRetentionPolicy

        result = await self.db.execute(
            select(CompanyRetentionPolicy).where(
                CompanyRetentionPolicy.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        company_id: str,
        retention_months: int,
        auto_anonymize: bool,
        activated_by: str | None,
    ):
        """Create or update CompanyRetentionPolicy; flush and refresh; return instance."""
        from lia_models.retention_policy import CompanyRetentionPolicy

        policy = await self.get_by_company_id(company_id)
        now = datetime.now(UTC)

        if policy is None:
            policy = CompanyRetentionPolicy(
                id=str(uuid4()),
                company_id=company_id,
                retention_months=retention_months,
                auto_anonymize=auto_anonymize,
                activated_at=now if auto_anonymize else None,
                activated_by=activated_by if auto_anonymize else None,
            )
            self.db.add(policy)
        else:
            if auto_anonymize and not policy.auto_anonymize:
                policy.activated_at = now
                policy.activated_by = activated_by
            policy.retention_months = retention_months
            policy.auto_anonymize = auto_anonymize

        await self.db.flush()
        await self.db.refresh(policy)
        return policy
