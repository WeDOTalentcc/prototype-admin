"""
Credit Service — manages credit accounts, consumption, and transaction ledger.

Credits are scoped per company_id (multi-tenant).
Every balance change is recorded as an immutable CreditTransaction.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_for_update

from lia_models.billing import (
    CreditAccount,
    CreditTransaction,
    CreditTransactionType,
)

logger = logging.getLogger(__name__)

INITIAL_FREE_CREDITS = 100


class CreditService:

    async def get_or_create_account(
        self, db: AsyncSession, company_id: str
    ) -> CreditAccount:
        result = await db.execute(
            select(CreditAccount).where(CreditAccount.company_id == company_id)
        )
        account = result.scalars().first()
        if account:
            return account

        account = CreditAccount(
            company_id=company_id,
            balance=INITIAL_FREE_CREDITS,
            lifetime_bonus=INITIAL_FREE_CREDITS,
        )
        db.add(account)

        tx = CreditTransaction(
            company_id=company_id,
            transaction_type=CreditTransactionType.BONUS.value,
            amount=INITIAL_FREE_CREDITS,
            balance_after=INITIAL_FREE_CREDITS,
            description="Initial free credits on account creation",
            performed_by="system",
        )
        db.add(tx)
        await db.flush()
        return account

    async def get_balance(self, db: AsyncSession, company_id: str) -> dict:
        account = await self.get_or_create_account(db, company_id)
        return {
            "balance": account.balance,
            "lifetime_purchased": account.lifetime_purchased,
            "lifetime_consumed": account.lifetime_consumed,
            "lifetime_bonus": account.lifetime_bonus,
            "updated_at": (
                account.updated_at.isoformat() if account.updated_at else None
            ),
        }

    async def consume(
        self,
        db: AsyncSession,
        company_id: str,
        amount: int,
        description: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        performed_by: str | None = None,
    ) -> tuple[bool, int]:
        """
        Deduct credits. Returns (success, remaining_balance).
        Fails if insufficient balance.
        """
        if amount <= 0:
            raise ValueError("Consumption amount must be positive")

        result = await db.execute(
            select(CreditAccount)
            .where(CreditAccount.company_id == company_id)
            .with_for_update()
        )
        account = result.scalars().first()
        if not account:
            account = await self.get_or_create_account(db, company_id)

        if account.balance < amount:
            logger.warning(
                "[Credits] Insufficient balance for %s: needs %d, has %d",
                company_id,
                amount,
                account.balance,
            )
            return False, account.balance

        account.balance -= amount
        account.lifetime_consumed += amount
        account.updated_at = datetime.utcnow()

        tx = CreditTransaction(
            company_id=company_id,
            transaction_type=CreditTransactionType.CONSUMPTION.value,
            amount=-amount,
            balance_after=account.balance,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
        )
        db.add(tx)
        await db.flush()

        logger.info(
            "[Credits] Consumed %d credits for %s — remaining: %d",
            amount,
            company_id,
            account.balance,
        )
        return True, account.balance

    async def add_credits(
        self,
        db: AsyncSession,
        company_id: str,
        amount: int,
        transaction_type: CreditTransactionType,
        description: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        performed_by: str | None = None,
    ) -> int:
        """Add credits (purchase, bonus, refund, subscription grant). Returns new balance."""
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        result = await db.execute(
            select(CreditAccount)
            .where(CreditAccount.company_id == company_id)
            .with_for_update()
        )
        account = result.scalars().first()
        if not account:
            account = await self.get_or_create_account(db, company_id)

        account.balance += amount
        account.updated_at = datetime.utcnow()

        if transaction_type == CreditTransactionType.PURCHASE:
            account.lifetime_purchased += amount
        elif transaction_type in (
            CreditTransactionType.BONUS,
            CreditTransactionType.SUBSCRIPTION_GRANT,
        ):
            account.lifetime_bonus += amount

        tx = CreditTransaction(
            company_id=company_id,
            transaction_type=transaction_type.value,
            amount=amount,
            balance_after=account.balance,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
        )
        db.add(tx)
        await db.flush()

        logger.info(
            "[Credits] Added %d credits (%s) for %s — new balance: %d",
            amount,
            transaction_type.value,
            company_id,
            account.balance,
        )
        return account.balance

    async def get_transactions(
        self,
        db: AsyncSession,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.company_id == company_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [t.to_dict() for t in result.scalars().all()]
