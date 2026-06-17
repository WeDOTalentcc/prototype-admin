from datetime import datetime, timezone

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ats_integration import (
    ATSCandidate,
    ATSConnection,
    ATSJobMapping,
    ATSProvider,
    ATSSyncJob,
    ATSWebhookLog,
    SyncStatus,
)


class ATSRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ #
    # ATSConnection
    # ------------------------------------------------------------------ #

    async def get_active_connections_by_company(self, company_id: str) -> list[ATSConnection]:
        result = await self.db.execute(
            select(ATSConnection).where(
                and_(
                    ATSConnection.is_active,
                    ATSConnection.company_id == company_id,
                )
            )
        )
        return list(result.scalars().all())

    async def get_connection_by_id_and_company(
        self, connection_id: str, company_id: str
    ) -> ATSConnection | None:
        result = await self.db.execute(
            select(ATSConnection).where(
                and_(
                    ATSConnection.id == connection_id,
                    ATSConnection.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_connections_by_provider(
        self, provider_enum: ATSProvider
    ) -> list[ATSConnection]:
        """List active connections by provider — CROSS-TENANT.

        CROSS-TENANT-EXEMPT: usado por sync schedulers / background jobs que precisam
        listar todas as ATSConnections de um provider em todos os tenants (e.g., daily
        sync orchestrator). Caller é trusted (Celery/Sidekiq), não exposto a API.
        Audit 2026-05-22.
        """
        # CROSS-TENANT-EXEMPT: background sync orchestration — see docstring
        result = await self.db.execute(
            select(ATSConnection).where(
                ATSConnection.provider == provider_enum,
                ATSConnection.is_active == True,
            ).order_by(desc(ATSConnection.created_at))
        )
        return list(result.scalars().all())

    async def add_connection(self, connection: ATSConnection) -> ATSConnection:
        self.db.add(connection)
        await self.db.flush()
        await self.db.refresh(connection)
        return connection

    # ------------------------------------------------------------------ #
    # ATSSyncJob
    # ------------------------------------------------------------------ #

    async def list_sync_jobs(
        self,
        company_id: str,
        connection_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[ATSSyncJob]:
        """List ATS sync jobs scoped to company.

        Onda 4.2g-P0-2 (2026-05-23): company_id obrigatorio — antes vazava
        sync logs (timings, error_message) de TODOS tenants quando
        connection_id omitido. LGPD Art. 6 violado.
        """
        # JOIN com ATSConnection pra filtrar tenant.
        query = (
            select(ATSSyncJob)
            .join(ATSConnection, ATSConnection.id == ATSSyncJob.connection_id)
            .where(ATSConnection.company_id == company_id)
        )
        filters = []
        if connection_id:
            filters.append(ATSSyncJob.connection_id == connection_id)
        if status:
            filters.append(ATSSyncJob.status == SyncStatus[status.upper()])
        if filters:
            query = query.where(and_(*filters))
        query = query.order_by(desc(ATSSyncJob.created_at)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_sync_job(self, sync_job: ATSSyncJob) -> ATSSyncJob:
        self.db.add(sync_job)
        await self.db.flush()
        await self.db.refresh(sync_job)
        return sync_job

    # ------------------------------------------------------------------ #
    # ATSCandidate
    # ------------------------------------------------------------------ #

    async def list_candidates(
        self,
        company_id: str,
        provider: str | None = None,
        connection_id: str | None = None,
        limit: int = 50,
    ) -> list[ATSCandidate]:
        """List ATS candidates scoped to company.

        Onda 4.2g-P0-1 (2026-05-23): company_id obrigatorio — antes vazava
        PII (name+email+phone) de candidatos de TODOS tenants quando
        connection_id omitido. LGPD Art. 33 incident risk.
        """
        # JOIN com ATSConnection pra filtrar tenant.
        query = (
            select(ATSCandidate)
            .join(ATSConnection, ATSConnection.id == ATSCandidate.connection_id)
            .where(ATSConnection.company_id == company_id)
            .where(ATSCandidate.is_active)
        )
        if provider:
            query = query.where(ATSCandidate.provider == ATSProvider[provider.upper()])
        if connection_id:
            query = query.where(ATSCandidate.connection_id == connection_id)
        query = query.order_by(desc(ATSCandidate.last_synced_at)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_candidate_by_ats_id(
        self,
        ats_candidate_id: str,
        provider: ATSProvider,
        connection_id: object,
    ) -> ATSCandidate | None:
        result = await self.db.execute(
            select(ATSCandidate).where(
                ATSCandidate.ats_candidate_id == ats_candidate_id,
                ATSCandidate.provider == provider,
                ATSCandidate.connection_id == connection_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_candidate(self, candidate: ATSCandidate) -> None:
        self.db.add(candidate)

    # ------------------------------------------------------------------ #
    # ATSJobMapping
    # ------------------------------------------------------------------ #

    async def get_job_by_ats_id(
        self,
        ats_job_id: str,
        provider: ATSProvider,
        connection_id: object,
    ) -> ATSJobMapping | None:
        result = await self.db.execute(
            select(ATSJobMapping).where(
                ATSJobMapping.ats_job_id == ats_job_id,
                ATSJobMapping.provider == provider,
                ATSJobMapping.connection_id == connection_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_job(self, job: ATSJobMapping) -> None:
        self.db.add(job)

    # ------------------------------------------------------------------ #
    # ATSWebhookLog
    # ------------------------------------------------------------------ #

    async def list_webhook_logs(
        self,
        company_id: str,
        provider: str | None = None,
        processed: bool | None = None,
        limit: int = 50,
    ) -> list[ATSWebhookLog]:
        """List ATS webhook logs scoped to company.

        Onda 4.2g-P0-3 (2026-05-23): company_id obrigatorio — antes vazava
        payloads completos (event_type, IDs externos, PII conforme provider)
        de TODOS tenants quando provider omitido. LGPD Art. 33 incident risk.
        """
        # JOIN com ATSConnection pra filtrar tenant.
        query = (
            select(ATSWebhookLog)
            .join(ATSConnection, ATSConnection.id == ATSWebhookLog.connection_id)
            .where(ATSConnection.company_id == company_id)
        )
        if provider:
            query = query.where(ATSWebhookLog.provider == ATSProvider[provider.upper()])
        if processed is not None:
            query = query.where(ATSWebhookLog.processed == processed)
        query = query.order_by(desc(ATSWebhookLog.received_at)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_webhook_log(self, log: ATSWebhookLog) -> ATSWebhookLog:
        self.db.add(log)
        await self.db.flush()
        return log
