"""
AuditLog Repository — data access layer for SOX audit logs and retention policies.
Extracted from app/api/v1/audit_logs.py as part of Phase 2 refactor.
"""
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_logs import (
    DEFAULT_RETENTION_POLICIES,
    AuditRetentionPolicy,
    SOXAuditLog,
)

logger = logging.getLogger(__name__)


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── SOXAuditLog ──────────────────────────────

    async def list_logs(
        self,
        *,
        conditions: list,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SOXAuditLog], int]:
        # TENANT-EXEMPT: SOX audit logs are cross-tenant (system-wide compliance trail); LGPD Art. 7º IX legítimo interesse (immutable compliance trail, NOT aggregate); T-RATCHET tenant_filter
        query = select(SOXAuditLog).order_by(desc(SOXAuditLog.timestamp))
        if conditions:
            query = query.where(and_(*conditions))
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        count_q = select(func.count(SOXAuditLog.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total = (await self.db.execute(count_q)).scalar() or 0
        return logs, total

    async def get_log_by_id(self, log_id: UUID, company_id: str | None) -> SOXAuditLog | None:
        # TENANT-EXEMPT: SOX audit logs are cross-tenant (system-wide compliance trail); LGPD Art. 7º IX legítimo interesse (immutable compliance trail, NOT aggregate); T-RATCHET tenant_filter
        query = select(SOXAuditLog).where(SOXAuditLog.id == log_id)
        # P1-W4-07: branch "platform" removida — toda consulta verifica tenant
        if company_id:
            query = query.where(SOXAuditLog.client_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_log(self, data: dict) -> SOXAuditLog:
        log = SOXAuditLog(**data)
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def export_logs(self, conditions: list, limit: int = 10000) -> list[SOXAuditLog]:
        # TENANT-EXEMPT: SOX audit logs are cross-tenant (system-wide compliance trail); LGPD Art. 7º IX legítimo interesse (immutable compliance trail, NOT aggregate); T-RATCHET tenant_filter
        query = select(SOXAuditLog).order_by(desc(SOXAuditLog.timestamp)).limit(limit)
        if conditions:
            query = query.where(and_(*conditions))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stats(self, conditions: list) -> dict:
        """Return aggregated stats dict for audit logs."""
        total_q = select(func.count(SOXAuditLog.id))
        if conditions:
            total_q = total_q.where(and_(*conditions))
        total = (await self.db.execute(total_q)).scalar() or 0

        cat_q = select(SOXAuditLog.action_category, func.count(SOXAuditLog.id)).group_by(
            SOXAuditLog.action_category
        )
        if conditions:
            cat_q = cat_q.where(and_(*conditions))
        logs_by_category = {r[0]: r[1] for r in (await self.db.execute(cat_q)).fetchall()}

        st_q = select(SOXAuditLog.status, func.count(SOXAuditLog.id)).group_by(SOXAuditLog.status)
        if conditions:
            st_q = st_q.where(and_(*conditions))
        logs_by_status = {r[0]: r[1] for r in (await self.db.execute(st_q)).fetchall()}

        users_q = select(func.count(func.distinct(SOXAuditLog.user_id)))
        if conditions:
            users_q = users_q.where(and_(*conditions))
        unique_users = (await self.db.execute(users_q)).scalar() or 0

        clients_q = select(func.count(func.distinct(SOXAuditLog.client_id)))
        if conditions:
            clients_q = clients_q.where(and_(*conditions))
        unique_clients = (await self.db.execute(clients_q)).scalar() or 0

        top_q = (
            select(SOXAuditLog.action, func.count(SOXAuditLog.id).label("count"))
            .group_by(SOXAuditLog.action)
            .order_by(desc("count"))
            .limit(10)
        )
        if conditions:
            top_q = top_q.where(and_(*conditions))
        top_actions = [
            {"action": r[0], "count": r[1]} for r in (await self.db.execute(top_q)).fetchall()
        ]

        # WT-2022 P5.1: compute recent_24h real (era ghost — FE esperava mas BE não populava)
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        recent_q = select(func.count(SOXAuditLog.id)).where(
            SOXAuditLog.timestamp >= cutoff_24h
        )
        if conditions:
            recent_q = recent_q.where(and_(*conditions))
        recent_24h = (await self.db.execute(recent_q)).scalar() or 0

        # WT-2022 P5.1: by_severity — model SOXAuditLog NÃO tem severity column.
        # Retorna dict vazio pra alinhar schema FE/BE (era fake na UI). Feature
        # de severity exige migration que adicione coluna (separate card).
        by_severity: dict = {}

        return {
            "total_logs": total,
            "logs_by_category": logs_by_category,
            "logs_by_status": logs_by_status,
            "unique_users": unique_users,
            "unique_clients": unique_clients,
            "top_actions": top_actions,
            "recent_24h": recent_24h,
            "by_severity": by_severity,
        }

    # ── AuditRetentionPolicy ─────────────────────

    async def list_retention_policies(self) -> list[AuditRetentionPolicy]:
        result = await self.db.execute(
            select(AuditRetentionPolicy).order_by(AuditRetentionPolicy.category)
        )
        return list(result.scalars().all())

    async def get_retention_policy_by_category(self, category: str) -> AuditRetentionPolicy | None:
        result = await self.db.execute(
            select(AuditRetentionPolicy).where(AuditRetentionPolicy.category == category)
        )
        return result.scalar_one_or_none()

    async def create_retention_policy(self, data: dict) -> AuditRetentionPolicy:
        policy = AuditRetentionPolicy(**data)
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def seed_retention_policies(self) -> tuple[int, int]:
        """Returns (created_count, skipped_count)."""
        created = skipped = 0
        for pdata in DEFAULT_RETENTION_POLICIES:
            if await self.get_retention_policy_by_category(pdata["category"]):
                skipped += 1
                continue
            self.db.add(AuditRetentionPolicy(**pdata))
            created += 1
        return created, skipped
