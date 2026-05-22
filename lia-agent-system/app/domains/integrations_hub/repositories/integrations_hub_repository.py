"""
IntegrationsHubRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/integrations_hub.py.
"""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration_hub import (
    DEFAULT_INTEGRATION_PROVIDERS,
    IntegrationConnection,
    IntegrationProvider,
    IntegrationStatus,
    IntegrationSyncLog,
)
from app.shared.services.credentials_crypto import (
    CredentialsEncryptionError,
    decrypt_credentials,
    encrypt_credentials,
)

logger = logging.getLogger(__name__)


class IntegrationsHubRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Providers ───────────────────────────────────────────────────────────

    async def list_providers(
        self,
        active_only: bool = True,
        category: str | None = None,
    ) -> list[IntegrationProvider]:
        query = select(IntegrationProvider)

        filters = []
        if active_only:
            filters.append(IntegrationProvider.is_active)
        if category:
            filters.append(IntegrationProvider.category == category)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(IntegrationProvider.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_provider_by_id(self, provider_id: str) -> IntegrationProvider | None:
        result = await self.db.execute(
            select(IntegrationProvider).where(IntegrationProvider.id == provider_id)
        )
        return result.scalar_one_or_none()

    async def get_provider_by_slug(self, slug: str) -> IntegrationProvider | None:
        result = await self.db.execute(
            select(IntegrationProvider).where(IntegrationProvider.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_provider(self, provider_data: dict[str, Any]) -> IntegrationProvider:
        provider = IntegrationProvider(**provider_data)
        self.db.add(provider)
        await self.db.flush()
        return provider

    async def seed_default_providers(self) -> list[IntegrationProvider]:
        """Seed default providers if they don't exist, return all providers."""
        for provider_data in DEFAULT_INTEGRATION_PROVIDERS:
            existing = await self.get_provider_by_slug(provider_data["slug"])
            if existing:
                continue
            await self.create_provider(provider_data)

        await self.db.commit()

        result = await self.db.execute(
            select(IntegrationProvider).order_by(IntegrationProvider.name)
        )
        return list(result.scalars().all())

    # ── Connections ─────────────────────────────────────────────────────────

    async def list_connections(
        self,
        company_id: str,
        status: str | None = None,
        category: str | None = None,
    ) -> list[tuple[IntegrationConnection, IntegrationProvider]]:
        query = select(IntegrationConnection, IntegrationProvider).join(
            IntegrationProvider,
            IntegrationConnection.provider_id == IntegrationProvider.id,
        )

        filters = [IntegrationConnection.company_id == company_id]
        if status:
            filters.append(IntegrationConnection.status == status)
        if category:
            filters.append(IntegrationProvider.category == category)

        query = query.where(and_(*filters)).order_by(
            desc(IntegrationConnection.created_at)
        )
        result = await self.db.execute(query)
        return list(result.all())

    async def get_connection_by_id(
        self, connection_id: str
    ) -> IntegrationConnection | None:
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.id == connection_id
            )
        )
        return result.scalar_one_or_none()

    async def get_connection_with_provider(
        self, connection_id: str
    ) -> tuple[IntegrationConnection, IntegrationProvider] | None:
        result = await self.db.execute(
            select(IntegrationConnection, IntegrationProvider).join(
                IntegrationProvider,
                IntegrationConnection.provider_id == IntegrationProvider.id,
            ).where(IntegrationConnection.id == connection_id)
        )
        return result.first()

    async def create_connection(
        self,
        company_id: str,
        provider_id: str,
        auth_type: str,
        credentials: dict,
        sync_enabled: bool,
        sync_direction: str,
        sync_frequency: str,
        field_mappings: dict,
    ) -> IntegrationConnection:
        # P0.D LGPD Art. 46: encrypt credentials BEFORE INSERT.
        # Plaintext credentials NEVER touch credentials_legacy (the legacy
        # JSON column) on new writes — only credentials_encrypted is set.
        encrypted = encrypt_credentials(credentials)
        connection = IntegrationConnection(
            company_id=company_id,
            provider_id=provider_id,
            status=IntegrationStatus.CONNECTING.value,
            auth_type=auth_type,
            credentials_encrypted=encrypted,
            credentials_legacy=None,
            sync_enabled=sync_enabled,
            sync_direction=sync_direction,
            sync_frequency=sync_frequency,
            field_mappings=field_mappings,
        )
        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def update_connection(
        self,
        connection: IntegrationConnection,
        sync_enabled: bool | None = None,
        sync_direction: str | None = None,
        sync_frequency: str | None = None,
        field_mappings: dict | None = None,
        credentials: dict | None = None,
    ) -> IntegrationConnection:
        if sync_enabled is not None:
            connection.sync_enabled = sync_enabled
        if sync_direction is not None:
            connection.sync_direction = sync_direction
        if sync_frequency is not None:
            connection.sync_frequency = sync_frequency
        if field_mappings is not None:
            connection.field_mappings = field_mappings
        if credentials is not None:
            # P0.D LGPD Art. 46: re-encrypt full dict (Fernet ciphertext
            # is single-blob; partial update is not supported — caller
            # must pass the full credentials dict).
            connection.credentials_encrypted = encrypt_credentials(credentials)
            # Force-clear legacy column (defense in depth — should already
            # be NULL post-backfill of migration 168).
            connection.credentials_legacy = None

        connection.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def delete_connection(self, connection: IntegrationConnection) -> None:
        await self.db.delete(connection)
        await self.db.commit()

    async def mark_connection_tested(
        self, connection: IntegrationConnection
    ) -> None:
        connection.status = IntegrationStatus.CONNECTED.value
        connection.health_score = 100.0
        connection.error_count = 0
        connection.updated_at = datetime.utcnow()
        await self.db.commit()

    async def start_sync(
        self,
        connection: IntegrationConnection,
        sync_type: str,
    ) -> IntegrationSyncLog:
        sync_log = IntegrationSyncLog(
            connection_id=connection.id,
            sync_type=sync_type,
            direction="inbound",
            status="pending",
        )
        self.db.add(sync_log)

        connection.last_sync_at = datetime.utcnow()
        connection.last_sync_status = "pending"

        await self.db.commit()
        await self.db.refresh(sync_log)
        return sync_log

    async def rollback(self) -> None:
        await self.db.rollback()

    # ── Sync Logs ───────────────────────────────────────────────────────────

    async def get_sync_logs(
        self,
        connection_id: str,
        limit: int = 20,
    ) -> list[IntegrationSyncLog]:
        result = await self.db.execute(
            select(IntegrationSyncLog)
            .where(IntegrationSyncLog.connection_id == connection_id)
            .order_by(desc(IntegrationSyncLog.started_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Health ──────────────────────────────────────────────────────────────

    async def get_connections_with_providers_for_company(
        self, company_id: str
    ) -> list[tuple[IntegrationConnection, IntegrationProvider]]:
        result = await self.db.execute(
            select(IntegrationConnection, IntegrationProvider).join(
                IntegrationProvider,
                IntegrationConnection.provider_id == IntegrationProvider.id,
            ).where(IntegrationConnection.company_id == company_id)
        )
        return list(result.all())

    # ── Credentials decryption (P0.D LGPD Art. 46) ──────────────────────────

    async def get_decrypted_credentials(
        self, connection_id: str, company_id: str
    ) -> dict:
        """
        Return decrypted credentials for a connection (fail-loud).

        Multi-tenancy: requires company_id (JWT) and verifies ownership.
        Returns empty dict if connection has no credentials set.

        Raises
        ------
        ValueError
            If connection is not found, or belongs to a different company,
            or has a legacy unmigrated row (credentials_legacy populated
            with credentials_encrypted NULL — should never happen after
            migration 168 backfill).
        CredentialsEncryptionError
            If decryption fails (key rotation, ciphertext corruption).
        """
        conn = await self.get_connection_by_id(connection_id)
        if conn is None:
            raise ValueError(f"Connection not found: {connection_id}")
        if str(conn.company_id) != str(company_id):
            # Defense in depth — caller SHOULD already gate via JWT/RLS,
            # but never trust callers.
            raise ValueError("Connection does not belong to this company")

        if conn.credentials_encrypted:
            return decrypt_credentials(conn.credentials_encrypted)

        if conn.credentials_legacy:
            # This row was NOT migrated by 168. Refuse to silently expose
            # plaintext — REGRA 4 (no silent fallback in security path).
            raise ValueError(
                f"Connection {connection_id} has legacy unencrypted credentials; "
                "run migration 168 backfill before consuming via this path."
            )

        return {}

