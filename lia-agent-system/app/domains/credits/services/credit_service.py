"""
Credit Service — manages credit accounts, consumption, and transaction ledger.

Credits are scoped per company_id (multi-tenant).
Every balance change is recorded as an immutable CreditTransaction.
"""
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.credits.repositories.credits_data_repository import CreditsDataRepository
from lia_models.billing import (
    CreditAccount,
    CreditTransaction,
    CreditTransactionType,
)

logger = logging.getLogger(__name__)

INITIAL_FREE_CREDITS = 100  # Free-tier bootstrap; billing system overrides via add_credits(subscription_grant)

DEFAULT_LOW_BALANCE_THRESHOLD = 20

ACTION_CREDIT_COSTS: dict[str, int] = {
    "search": 2,
    "analysis": 5,
    "screening": 10,
    "report": 8,
    "ai_chat": 1,
    "email_send": 1,
    "interview_schedule": 3,
    "cv_parsing": 3,
    "bulk_search": 5,
    "pearch_search": 2,
    "apify_enrichment": 1,
}


def get_action_cost(action_type: str) -> int:
    return ACTION_CREDIT_COSTS.get(action_type, 1)


class CreditService:

    async def get_or_create_account(
        self, db: AsyncSession, company_id: str
    ) -> CreditAccount:
        repo = CreditsDataRepository(db)
        account = await repo.get_account_by_company(company_id)
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
        threshold = account.low_balance_threshold or DEFAULT_LOW_BALANCE_THRESHOLD
        low_balance_warning = account.balance <= threshold
        return {
            "balance": account.balance,
            "plan_type": account.plan_type or "free",
            "lifetime_purchased": account.lifetime_purchased,
            "lifetime_consumed": account.lifetime_consumed,
            "lifetime_bonus": account.lifetime_bonus,
            "low_balance_warning": low_balance_warning,
            "low_balance_threshold": threshold,
            "reset_date": (
                account.reset_date.isoformat() if account.reset_date else None
            ),
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
        action_type: str | None = None,
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

        repo = CreditsDataRepository(db)
        account = await repo.get_account_by_company_for_update(company_id)
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
            action_type=action_type,
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
            "[Credits] Consumed %d credits for %s (action=%s) — remaining: %d",
            amount,
            company_id,
            action_type or "manual",
            account.balance,
        )
        return True, account.balance

    async def consume_action(
        self,
        db: AsyncSession,
        company_id: str,
        action_type: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        performed_by: str | None = None,
    ) -> tuple[bool, int]:
        """
        Deduct credits for a specific action type using the configured cost.
        Returns (success, remaining_balance).
        """
        cost = get_action_cost(action_type)
        description = f"{action_type} ({cost} credits)"
        return await self.consume(
            db,
            company_id,
            cost,
            description,
            action_type=action_type,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
        )

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

        repo = CreditsDataRepository(db)
        account = await repo.get_account_by_company_for_update(company_id)
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
            action_type=None,
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
        repo = CreditsDataRepository(db)
        transactions = await repo.list_transactions_by_company(
            company_id, limit=limit, offset=offset
        )
        return [t.to_dict() for t in transactions]


credit_service = CreditService()


def get_credit_service() -> "CreditService":
    return credit_service
