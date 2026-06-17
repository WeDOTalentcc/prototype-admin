"""
CreditsDataRepository: raw SQL repository for credits data.

Distinct from ``CreditsRepository`` (which wraps service-level business
operations). This module owns the queries so ``CreditService`` is free of
inline SQL (ADR-001) and stays free of circular imports with the wrapper.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.billing import CreditAccount, CreditTransaction


class CreditsDataRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_account_by_company(self, company_id: str) -> CreditAccount | None:
        """Return CreditAccount for the given company, or None."""
        result = await self.db.execute(
            select(CreditAccount).where(CreditAccount.company_id == company_id)
        )
        return result.scalars().first()

    async def get_account_by_company_for_update(
        self, company_id: str
    ) -> CreditAccount | None:
        """Return CreditAccount with FOR UPDATE row lock, or None.

        Used by consume/add_credits to serialize concurrent balance updates
        within a transaction.
        """
        result = await self.db.execute(
            select(CreditAccount)
            .where(CreditAccount.company_id == company_id)
            .with_for_update()
        )
        return result.scalars().first()

    async def list_transactions_by_company(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CreditTransaction]:
        """Return CreditTransactions for the given company, newest first."""
        result = await self.db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.company_id == company_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
