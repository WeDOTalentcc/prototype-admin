"""ClientAccountRepository - session-in-constructor pattern."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.auth.workos_models import CompanyWorkOSConfig
from app.models.client_account import ClientAccount, ClientStatus

logger = logging.getLogger(__name__)


class ClientAccountRepository:
    """Repository for ClientAccount CRUD and query operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Basic lookups ─────────────────────────────────────────────────────────

    async def get_by_id(self, client_id: UUID) -> ClientAccount | None:
        result = await self.db.execute(
            select(ClientAccount).where(
                and_(
                    ClientAccount.id == client_id,
                    not ClientAccount.is_deleted,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_cnpj(self, cnpj: str) -> ClientAccount | None:
        result = await self.db.execute(
            select(ClientAccount).where(
                and_(
                    ClientAccount.cnpj == cnpj,
                    not ClientAccount.is_deleted,
                )
            )
        )
        return result.scalar_one_or_none()

    # ── List / count ──────────────────────────────────────────────────────────

    async def list_all(
        self,
        *,
        status: str | None = None,
        plan_id: str | None = None,
        search: str | None = None,
        industry: str | None = None,
        company_size: str | None = None,
        company_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClientAccount]:
        conditions = self._build_conditions(
            status=status,
            plan_id=plan_id,
            search=search,
            industry=industry,
            company_size=company_size,
            company_id=company_id,
        )
        query = (
            select(ClientAccount)
            .where(and_(*conditions))
            .order_by(ClientAccount.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_all(
        self,
        *,
        status: str | None = None,
        plan_id: str | None = None,
        search: str | None = None,
        industry: str | None = None,
        company_size: str | None = None,
        company_id: str | None = None,
    ) -> int:
        conditions = self._build_conditions(
            status=status,
            plan_id=plan_id,
            search=search,
            industry=industry,
            company_size=company_size,
            company_id=company_id,
        )
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(and_(*conditions))
        )
        return result.scalar() or 0

    def _build_conditions(
        self,
        *,
        status: str | None,
        plan_id: str | None,
        search: str | None,
        industry: str | None,
        company_size: str | None,
        company_id: str | None,
    ) -> list:
        conditions: list = [not ClientAccount.is_deleted]
        if status:
            conditions.append(ClientAccount.status == status)
        if plan_id:
            conditions.append(ClientAccount.plan_id == plan_id)
        if industry:
            conditions.append(ClientAccount.industry == industry)
        if company_size:
            conditions.append(ClientAccount.company_size == company_size)
        if search:
            term = f"%{search}%"
            conditions.append(
                or_(
                    ClientAccount.name.ilike(term),
                    ClientAccount.trade_name.ilike(term),
                    ClientAccount.cnpj.ilike(term),
                )
            )
        if company_id:
            conditions.append(ClientAccount.id == company_id)
        return conditions

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, data: dict) -> ClientAccount:
        """
        Create a new ClientAccount.

        Also inserts a default company_workos_config row and verifies it was
        created. Rolls back and raises RuntimeError if the config row is
        missing after insert.
        """
        client = ClientAccount(**data)
        self.db.add(client)
        await self.db.flush()

        # Provision WorkOS config row atomically with the client
        await self.db.execute(
            text(
                """
                INSERT INTO company_workos_config (company_id, sso_enabled, scim_enabled)
                VALUES (:company_id, false, false)
                ON CONFLICT (company_id) DO NOTHING
                """
            ),
            {"company_id": str(client.id)},
        )

        config_check = await self.db.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.company_id == str(client.id)
            )
        )
        if not config_check.scalar_one_or_none():
            await self.db.rollback()
            raise RuntimeError("Failed to provision WorkOS config for client")

        await self.db.commit()
        await self.db.refresh(client)
        return client

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, client_id: UUID, data: dict) -> ClientAccount | None:
        client = await self.get_by_id(client_id)
        if not client:
            return None
        for field, value in data.items():
            setattr(client, field, value)
        client.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def update_status(
        self, client_id: UUID, new_status: str
    ) -> ClientAccount | None:
        client = await self.get_by_id(client_id)
        if not client:
            return None
        old_status = client.status
        client.status = new_status
        client.updated_at = datetime.utcnow()
        # Auto-complete onboarding when first transitioning to ACTIVE
        if (
            new_status == ClientStatus.ACTIVE.value
            and old_status == ClientStatus.PENDING_SETUP.value
            and not client.onboarding_completed_at
        ):
            client.onboarding_completed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(client)
        return client, old_status

    # ── Delete (soft) ─────────────────────────────────────────────────────────

    async def soft_delete(
        self, client_id: UUID, deleted_by: str
    ) -> ClientAccount | None:
        client = await self.get_by_id(client_id)
        if not client:
            return None
        client.is_deleted = True
        client.deleted_at = datetime.utcnow()
        client.deleted_by = deleted_by
        client.status = ClientStatus.CHURNED.value
        await self.db.commit()
        return client

    # ── Save (flush + commit settings changes) ────────────────────────────────

    async def save(self, client: ClientAccount) -> ClientAccount:
        """Commit pending changes on an already-tracked instance.

        Automatically marks the settings JSON column as dirty so SQLAlchemy
        detects in-place mutations to the JSON object.
        """
        flag_modified(client, "settings")
        client.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(client)
        return client

    # ── Dashboard / stats queries ─────────────────────────────────────────────

    async def count_by_status(self, status_value: str) -> int:
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(
                and_(
                    ClientAccount.status == status_value,
                    not ClientAccount.is_deleted,
                )
            )
        )
        return result.scalar() or 0

    async def count_total(self) -> int:
        result = await self.db.execute(
            select(func.count(ClientAccount.id)).where(
                not ClientAccount.is_deleted
            )
        )
        return result.scalar() or 0

    async def list_by_status(self, status_value: str) -> list[ClientAccount]:
        result = await self.db.execute(
            select(ClientAccount)
            .where(
                and_(
                    ClientAccount.status == status_value,
                    not ClientAccount.is_deleted,
                )
            )
            .order_by(ClientAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_created_between(
        self, start: datetime, end: datetime
    ) -> list[ClientAccount]:
        result = await self.db.execute(
            select(ClientAccount)
            .where(
                and_(
                    ClientAccount.created_at >= start,
                    ClientAccount.created_at <= end,
                    not ClientAccount.is_deleted,
                )
            )
            .order_by(ClientAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_churned_between(
        self, start: datetime, end: datetime
    ) -> list[ClientAccount]:
        result = await self.db.execute(
            select(ClientAccount)
            .where(
                and_(
                    ClientAccount.status == ClientStatus.CHURNED.value,
                    ClientAccount.updated_at >= start,
                    ClientAccount.updated_at <= end,
                    not ClientAccount.is_deleted,
                )
            )
            .order_by(ClientAccount.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_plan_distribution(self) -> dict[str, int]:
        result = await self.db.execute(
            select(ClientAccount.plan_id, func.count(ClientAccount.id).label("count"))
            .where(
                and_(
                    not ClientAccount.is_deleted,
                    ClientAccount.plan_id.isnot(None),
                )
            )
            .group_by(ClientAccount.plan_id)
        )
        return {row.plan_id: row.count for row in result}

    async def get_company_size_distribution(self) -> dict[str, int]:
        result = await self.db.execute(
            select(
                ClientAccount.company_size,
                func.count(ClientAccount.id).label("count"),
            )
            .where(
                and_(
                    not ClientAccount.is_deleted,
                    ClientAccount.company_size.isnot(None),
                )
            )
            .group_by(ClientAccount.company_size)
        )
        return {row.company_size: row.count for row in result}

    async def get_status_distribution(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for status_opt in ClientStatus:
            stats[status_opt.value] = await self.count_by_status(status_opt.value)
        return stats
