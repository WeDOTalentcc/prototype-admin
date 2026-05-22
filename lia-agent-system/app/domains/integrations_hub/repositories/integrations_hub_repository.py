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
from app.domains.integrations_hub.repositories.credentials_access_log_repository import (
    CredentialsAccessLogRepository,
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
        # TENANT-EXEMPT: dynamic builder — filters[0] is IntegrationConnection.company_id == company_id (below); .where(and_(*filters)) aplica filter; sensor AST não traça
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
        self,
        connection_id: str,
        company_id: str | None = None,
    ) -> IntegrationConnection | None:
        """Lookup IntegrationConnection por id.

        Sprint B.1 tail (2026-05-22): company_id RECOMENDADO (defense-in-depth).
        Quando passado, filtra por tenant. Caller eh tenant-gated.
        """
        # TENANT-EXEMPT: defense-in-depth — caller api/v1/integrations_hub.py eh tenant-gated via require_company_id; company_id opcional desde Sprint B.1 tail
        if company_id is not None:
            result = await self.db.execute(
                select(IntegrationConnection).where(
                    IntegrationConnection.id == connection_id,
                    IntegrationConnection.company_id == company_id,
                )
            )
        else:
            # TENANT-EXEMPT: backwards-compat — caller validates connection.company_id post-fetch
            result = await self.db.execute(
                select(IntegrationConnection).where(
                    IntegrationConnection.id == connection_id
                )
            )
        return result.scalar_one_or_none()

    async def get_connection_with_provider(
        self,
        connection_id: str,
        company_id: str | None = None,
    ) -> tuple[IntegrationConnection, IntegrationProvider] | None:
        """Lookup IntegrationConnection + Provider.

        Sprint B.1 tail (2026-05-22): company_id RECOMENDADO (defense-in-depth).
        """
        # TENANT-EXEMPT: defense-in-depth — caller eh tenant-gated; company_id opcional desde Sprint B.1 tail
        if company_id is not None:
            result = await self.db.execute(
                select(IntegrationConnection, IntegrationProvider).join(
                    IntegrationProvider,
                    IntegrationConnection.provider_id == IntegrationProvider.id,
                ).where(
                    IntegrationConnection.id == connection_id,
                    IntegrationConnection.company_id == company_id,
                )
            )
        else:
            # TENANT-EXEMPT: backwards-compat — caller validates connection.company_id post-fetch
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

    # ── Credentials decryption (P0.D LGPD Art. 46 + Camada 3 Art. 37) ──────

    async def get_decrypted_credentials(
        self,
        connection_id: str,
        company_id: str,
        *,
        access_purpose: str,
        accessor_user_id: str | None = None,
        accessor_type: str = "system",
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> dict:
        """
        Return decrypted credentials for a connection (fail-loud).

        Multi-tenancy: requires company_id (JWT) and verifies ownership.
        Returns empty dict if connection has no credentials set.

        LGPD Art. 37 (Wave 3 Camada 3 — 2026-05-22): EVERY decryption
        attempt writes an audit-trail entry to ``credentials_access_logs``
        BEFORE the decrypt happens. ``access_purpose`` is REQUIRED so the
        caller documents *why* the secret material was read (forensic
        responsibility).

        Parameters
        ----------
        connection_id : str
            UUID of the IntegrationConnection.
        company_id : str
            JWT-derived tenant id. Used for ownership check + audit row.
        access_purpose : str (keyword-only, REQUIRED)
            Short reason, e.g. ``'webhook_dispatch'``, ``'sync_check'``,
            ``'manual_test'``, ``'health_check'``. Empty / whitespace
            raises ValueError.
        accessor_user_id : str | None
            Human user id when caller is a request handler. None for
            system / Celery / agent code paths.
        accessor_type : str
            Canonical: ``'human_user'`` | ``'system'`` | ``'agent'`` |
            ``'celery_task'``. Defaults to ``'system'``.
        client_ip : str | None
            Best-effort. ``request.client.host`` when inside a FastAPI
            handler.
        request_id : str | None
            X-Request-ID when inside HTTP scope.

        Raises
        ------
        ValueError
            If connection is not found, belongs to a different company,
            has a legacy unmigrated row (credentials_legacy populated
            with credentials_encrypted NULL — should never happen after
            migration 168 backfill), OR if ``access_purpose`` is empty /
            ``accessor_type`` invalid.
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

        # LGPD Art. 37 audit trail — write BEFORE decrypt so attempts
        # (even failed ones) leave a record.
        await CredentialsAccessLogRepository(self.db).log_access(
            company_id=company_id,
            integration_connection_id=connection_id,
            accessor_user_id=accessor_user_id,
            accessor_type=accessor_type,
            access_purpose=access_purpose,
            client_ip=client_ip,
            request_id=request_id,
        )

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

