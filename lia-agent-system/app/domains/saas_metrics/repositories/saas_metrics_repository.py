"""SaasMetricsRepository - session-in-constructor pattern."""
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_consumption import AiConsumption, AiCreditsBalance
from app.models.client_account import ClientAccount, ClientStatus
from app.models.client_user import ClientUser, ClientUserStatus
from app.models.saas_metrics import (
    ChurnRisk,
    ClientHealthMetrics,
    ClientSaasMetrics,
    ClientUsageMetrics,
    PaymentHistory,
    PaymentStatus,
)

logger = logging.getLogger(__name__)


class SaasMetricsRepository:
    """Repository for SaaS metrics queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── ClientAccount queries ─────────────────────────────────────────────────

    async def list_all_clients(self) -> list[ClientAccount]:
        result = await self.db.execute(
            select(ClientAccount).where(not ClientAccount.is_deleted)
        )
        return list(result.scalars().all())

    async def count_clients_total(self) -> int:
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(not ClientAccount.is_deleted)
        )
        return result.scalar() or 0

    async def count_clients_by_status(self, status: str) -> int:
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(
                and_(
                    not ClientAccount.is_deleted,
                    ClientAccount.status == status,
                )
            )
        )
        return result.scalar() or 0

    async def count_clients_created_before(self, cutoff: datetime) -> int:
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(
                and_(
                    not ClientAccount.is_deleted,
                    ClientAccount.created_at <= cutoff,
                )
            )
        )
        return result.scalar() or 0

    async def count_clients_churned_between(
        self, start: datetime, end: datetime | None = None
    ) -> int:
        conditions = [
            ClientAccount.status == ClientStatus.CHURNED.value,
            ClientAccount.updated_at >= start,
        ]
        if end is not None:
            conditions.append(ClientAccount.updated_at < end)
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(and_(*conditions))
        )
        return result.scalar() or 0

    async def count_clients_suspended(self) -> int:
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(
                and_(
                    not ClientAccount.is_deleted,
                    ClientAccount.status == ClientStatus.SUSPENDED.value,
                )
            )
        )
        return result.scalar() or 0

    async def get_client_by_id(self, client_id: UUID) -> ClientAccount | None:
        result = await self.db.execute(
            select(ClientAccount).where(
                and_(
                    ClientAccount.id == client_id,
                    not ClientAccount.is_deleted,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_clients_filtered(
        self,
        *,
        status_filter: str | None = None,
        plan_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClientAccount]:
        conditions: list = [not ClientAccount.is_deleted]
        if status_filter:
            conditions.append(ClientAccount.status == status_filter)
        if plan_filter:
            conditions.append(ClientAccount.plan_id == plan_filter)
        result = await self.db.execute(
            select(ClientAccount)
            .where(and_(*conditions))
            .order_by(ClientAccount.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_clients_filtered(
        self,
        *,
        status_filter: str | None = None,
        plan_filter: str | None = None,
    ) -> int:
        conditions: list = [not ClientAccount.is_deleted]
        if status_filter:
            conditions.append(ClientAccount.status == status_filter)
        if plan_filter:
            conditions.append(ClientAccount.plan_id == plan_filter)
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(and_(*conditions))
        )
        return result.scalar() or 0

    async def get_plan_counts_active(self) -> list:
        """Return rows with (plan_id, count) for active non-deleted clients."""
        result = await self.db.execute(
            select(
                ClientAccount.plan_id,
                func.count(ClientAccount.id).label("count"),
            )
            .where(
                and_(
                    not ClientAccount.is_deleted,
                    ClientAccount.status == ClientStatus.ACTIVE.value,
                    ClientAccount.plan_id.isnot(None),
                )
            )
            .group_by(ClientAccount.plan_id)
        )
        return list(result.all())

    async def get_company_size_counts_active(self) -> list:
        """Return rows with (company_size, count) for active non-deleted clients."""
        result = await self.db.execute(
            select(
                ClientAccount.company_size,
                func.count(ClientAccount.id).label("count"),
            )
            .where(
                and_(
                    not ClientAccount.is_deleted,
                    ClientAccount.status == ClientStatus.ACTIVE.value,
                    ClientAccount.company_size.isnot(None),
                )
            )
            .group_by(ClientAccount.company_size)
        )
        return list(result.all())

    # ── ClientUser queries ────────────────────────────────────────────────────

    async def count_users_total(self) -> int:
        result = await self.db.execute(
            select(func.count(ClientUser.id)).where(not ClientUser.is_deleted)
        )
        return result.scalar() or 0

    async def count_active_users_recent(self, cutoff: datetime) -> int:
        result = await self.db.execute(
            select(func.count(ClientUser.id)).where(
                and_(
                    not ClientUser.is_deleted,
                    ClientUser.status == ClientUserStatus.ACTIVE.value,
                    or_(
                        ClientUser.last_login_at >= cutoff,
                        ClientUser.last_login_at.is_(None),
                    ),
                )
            )
        )
        return result.scalar() or 0

    async def count_users_for_client(self, client_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(ClientUser.id)).where(
                and_(
                    ClientUser.company_id == client_id,
                    not ClientUser.is_deleted,
                )
            )
        )
        return result.scalar() or 0

    async def count_active_users_for_client(self, client_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(ClientUser.id)).where(
                and_(
                    ClientUser.company_id == client_id,
                    not ClientUser.is_deleted,
                    ClientUser.status == ClientUserStatus.ACTIVE.value,
                )
            )
        )
        return result.scalar() or 0

    # ── AiConsumption / AiCreditsBalance queries ──────────────────────────────

    async def get_ai_totals(self):
        """Return one row with (total_tokens, total_cost)."""
        result = await self.db.execute(
            select(
                func.sum(AiConsumption.total_tokens).label("total_tokens"),
                func.sum(AiConsumption.cost_cents).label("total_cost"),
            )
        )
        return result.one()

    async def get_ai_credits_balance(self, client_id: UUID) -> AiCreditsBalance | None:
        result = await self.db.execute(
            select(AiCreditsBalance).where(AiCreditsBalance.company_id == client_id)
        )
        return result.scalar_one_or_none()

    # ── ClientSaasMetrics queries ─────────────────────────────────────────────

    async def list_all_saas_metrics(self) -> list[ClientSaasMetrics]:
        result = await self.db.execute(select(ClientSaasMetrics))
        return list(result.scalars().all())

    async def get_saas_metrics_for_client(
        self, client_id: UUID
    ) -> ClientSaasMetrics | None:
        result = await self.db.execute(
            select(ClientSaasMetrics).where(ClientSaasMetrics.client_id == client_id)
        )
        return result.scalar_one_or_none()

    # ── ClientHealthMetrics queries ───────────────────────────────────────────

    async def list_all_health_metrics(self) -> list[ClientHealthMetrics]:
        result = await self.db.execute(select(ClientHealthMetrics))
        return list(result.scalars().all())

    async def get_health_metrics_for_client(
        self, client_id: UUID
    ) -> ClientHealthMetrics | None:
        result = await self.db.execute(
            select(ClientHealthMetrics).where(
                ClientHealthMetrics.client_id == client_id
            )
        )
        return result.scalar_one_or_none()

    # ── ClientUsageMetrics queries ────────────────────────────────────────────

    async def get_usage_metrics_for_client(
        self, client_id: UUID
    ) -> ClientUsageMetrics | None:
        result = await self.db.execute(
            select(ClientUsageMetrics).where(
                ClientUsageMetrics.client_id == client_id
            )
        )
        return result.scalar_one_or_none()

    # ── PaymentHistory queries ────────────────────────────────────────────────

    async def list_recent_payments(
        self, cutoff_date: datetime
    ) -> list[PaymentHistory]:
        result = await self.db.execute(
            select(PaymentHistory).where(PaymentHistory.date >= cutoff_date)
        )
        return list(result.scalars().all())

    async def list_payments_for_client(
        self,
        client_id: UUID,
        *,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaymentHistory]:
        conditions: list = [PaymentHistory.client_id == client_id]
        if status_filter:
            conditions.append(PaymentHistory.status == status_filter)
        result = await self.db.execute(
            select(PaymentHistory)
            .where(and_(*conditions))
            .order_by(PaymentHistory.date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_payments_for_client(
        self,
        client_id: UUID,
        *,
        status_filter: str | None = None,
    ) -> int:
        conditions: list = [PaymentHistory.client_id == client_id]
        if status_filter:
            conditions.append(PaymentHistory.status == status_filter)
        result = await self.db.execute(
            select(func.count(PaymentHistory.id)).where(and_(*conditions))
        )
        return result.scalar() or 0

    async def list_recent_payments_for_client(
        self, client_id: UUID, limit: int = 5
    ) -> list[PaymentHistory]:
        result = await self.db.execute(
            select(PaymentHistory)
            .where(PaymentHistory.client_id == client_id)
            .order_by(PaymentHistory.date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_payment(self, payment: PaymentHistory) -> PaymentHistory:
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def rollback(self) -> None:
        await self.db.rollback()
