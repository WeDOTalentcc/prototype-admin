"""
CreditsRepository: Encapsulates all direct database access for credits.
Wraps CreditService methods and owns the DB session.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.credits.services.credit_service import ACTION_CREDIT_COSTS, CreditService
from lia_models.billing import CreditTransactionType

logger = logging.getLogger(__name__)

_credit_service = CreditService()


class CreditsRepository:
    """Repository for credits-related database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_balance(self, company_id: str) -> dict:
        """Return the credit balance dict for the given company."""
        data = await _credit_service.get_balance(self.db, company_id)
        await self.db.commit()
        return data

    async def add_credits(
        self,
        company_id: str,
        amount: int,
        transaction_type: CreditTransactionType,
        description: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        performed_by: str | None = None,
    ) -> dict:
        """Add credits and return the updated balance dict."""
        await _credit_service.add_credits(
            self.db,
            company_id,
            amount,
            transaction_type,
            description,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
        )
        await self.db.commit()
        data = await _credit_service.get_balance(self.db, company_id)
        return data

    async def consume(
        self,
        company_id: str,
        amount: int,
        description: str,
        action_type: str | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
        performed_by: str | None = None,
    ) -> tuple[bool, int]:
        """Consume credits. Returns (success, remaining_balance)."""
        success, remaining = await _credit_service.consume(
            self.db,
            company_id,
            amount,
            description,
            action_type=action_type,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
        )
        if success:
            await self.db.commit()
        return success, remaining

    async def consume_action(
        self,
        company_id: str,
        action_type: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        performed_by: str | None = None,
    ) -> tuple[bool, int]:
        """Consume credits for a specific action. Returns (success, remaining_balance)."""
        success, remaining = await _credit_service.consume_action(
            self.db,
            company_id,
            action_type,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
        )
        if success:
            await self.db.commit()
        return success, remaining

    async def get_transactions(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Return list of credit transactions for the given company."""
        return await _credit_service.get_transactions(self.db, company_id, limit, offset)
