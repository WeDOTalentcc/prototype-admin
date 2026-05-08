"""
BillingRepository: Encapsulates all direct database access for billing.
"""
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Invoice, PaymentMethod, Subscription
from app.models.client_account import ClientAccount


class BillingRepository:
    """Repository for billing-related database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Subscription queries
    # ------------------------------------------------------------------

    async def list_subscriptions(
        self,
        conditions: list,
        limit: int,
        offset: int,
    ) -> list:
        """Return a paginated list of subscriptions matching conditions."""
        query = select(Subscription)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(Subscription.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_subscriptions(self, conditions: list) -> int:
        """Return total count of subscriptions matching conditions."""
        count_query = select(func.count(Subscription.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        return count_result.scalar() or 0

    async def get_latest_subscription_by_client(self, client_uuid: UUID):
        """Return the most recently created subscription for a client, or None."""
        query = (
            select(Subscription)
            .where(Subscription.client_id == client_uuid)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_subscription_by_id(self, subscription_id: UUID):
        """Return a single Subscription by primary key, or None."""
        query = select(Subscription).where(Subscription.id == subscription_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_subscription_for_client(
        self,
        client_id: UUID,
        active_statuses: list[str],
    ):
        """Return the active/trialing subscription for a client, or None."""
        query = select(Subscription).where(
            and_(
                Subscription.client_id == client_id,
                Subscription.status.in_(active_statuses),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_subscription_by_external_and_provider(
        self,
        external_id: str,
        provider: str,
    ):
        """Return a Subscription matching (external_id, provider), or None."""
        query = select(Subscription).where(
            and_(
                Subscription.external_id == external_id,
                Subscription.provider == provider,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def flush_and_refresh_subscription(self, subscription) -> None:
        """Flush pending changes and refresh the subscription instance."""
        await self.db.flush()
        await self.db.refresh(subscription)

    # ------------------------------------------------------------------
    # Invoice queries
    # ------------------------------------------------------------------

    async def list_invoices(
        self,
        conditions: list,
        limit: int,
        offset: int,
    ) -> list:
        """Return a paginated list of invoices matching conditions."""
        query = select(Invoice)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(Invoice.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_invoices_for_client(
        self,
        client_id: UUID,
        status: str | None = None,
        limit: int = 50,
    ) -> list:
        """Return invoices for a client, optionally filtered by status, ordered desc."""
        query = select(Invoice).where(Invoice.client_id == client_id)
        if status:
            query = query.where(Invoice.status == status)
        query = query.order_by(Invoice.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_invoice_by_external_and_provider(
        self,
        external_id: str,
        provider: str,
    ):
        """Return an Invoice matching (external_id, provider), or None."""
        query = select(Invoice).where(
            and_(
                Invoice.external_id == external_id,
                Invoice.provider == provider,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_invoices(self, conditions: list) -> int:
        """Return total count of invoices matching conditions."""
        count_query = select(func.count(Invoice.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        return count_result.scalar() or 0

    async def get_invoice_by_id(self, inv_uuid: UUID):
        """Return a single Invoice by primary key, or None."""
        query = select(Invoice).where(Invoice.id == inv_uuid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def flush_and_refresh_invoice(self, invoice) -> None:
        """Flush pending changes and refresh the invoice instance."""
        await self.db.flush()
        await self.db.refresh(invoice)

    # ------------------------------------------------------------------
    # PaymentMethod queries
    # ------------------------------------------------------------------

    async def get_active_payment_methods_by_client(self, client_uuid: UUID) -> list:
        """Return active payment methods for a client, ordered by default first."""
        query = (
            select(PaymentMethod)
            .where(
                and_(
                    PaymentMethod.client_id == client_uuid,
                    PaymentMethod.is_active,
                )
            )
            .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_payment_method_by_id(self, pm_uuid: UUID):
        """Return a single PaymentMethod by primary key, or None."""
        query = select(PaymentMethod).where(PaymentMethod.id == pm_uuid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # ClientAccount queries
    # ------------------------------------------------------------------

    async def get_client_by_id(self, client_uuid: UUID):
        """Return a ClientAccount by primary key (non-deleted), or None."""
        query = select(ClientAccount).where(
            and_(
                ClientAccount.id == client_uuid,
                not ClientAccount.is_deleted,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def flush_and_refresh_client(self, client) -> None:
        """Flush pending changes and refresh the client instance."""
        await self.db.flush()
        await self.db.refresh(client)

    def mark_client_settings_modified(self, client) -> None:
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(client, "settings")

