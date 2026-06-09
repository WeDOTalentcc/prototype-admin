"""WorkOSRepository - manages WorkOS-specific models for the auth domain."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.workos_models import (
    CompanyWorkOSConfig,
    SSOAuditLog,
    WorkOSGroup,
    WorkOSGroupMembership,
    WorkOSGroupRoleMapping,
)
from app.models.client_account import ClientAccount

logger = logging.getLogger(__name__)


class WorkOSRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── CompanyWorkOSConfig ──────────────────────────────────────────────────

    async def get_config(self, company_id: str) -> CompanyWorkOSConfig | None:
        result = await self.db.execute(
            select(CompanyWorkOSConfig).where(CompanyWorkOSConfig.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_config_by_directory(self, directory_id: str) -> CompanyWorkOSConfig | None:
        result = await self.db.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.workos_directory_id == directory_id
            )
        )
        return result.scalar_one_or_none()

    async def get_config_by_sso_domain(self, domain: str) -> CompanyWorkOSConfig | None:
        """Find config by SSO domain (checks sso_domains array)."""
        result = await self.db.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.sso_enabled == True,  # noqa: E712
                CompanyWorkOSConfig.sso_domains.any(domain),
            )
        )
        return result.scalar_one_or_none()

    async def create_config(self, data: dict) -> CompanyWorkOSConfig:
        config = CompanyWorkOSConfig(**data)
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update_config(self, config_id: UUID, data: dict) -> CompanyWorkOSConfig | None:
        result = await self.db.execute(
            select(CompanyWorkOSConfig).where(CompanyWorkOSConfig.id == config_id)
        )
        config = result.scalar_one_or_none()
        if not config:
            return None
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    # ── SSOAuditLog ─────────────────────────────────────────────────────────

    async def log_sso_event(self, data: dict) -> SSOAuditLog:
        audit_log = SSOAuditLog(**data)
        self.db.add(audit_log)
        await self.db.commit()
        return audit_log

    async def list_audit_logs(
        self,
        company_id: str,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SSOAuditLog]:
        query = (
            select(SSOAuditLog)
            .where(SSOAuditLog.company_id == company_id)
            .order_by(SSOAuditLog.created_at.desc())
        )
        if event_type:
            query = query.where(SSOAuditLog.event_type == event_type)
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_recent_events(self, company_id: str, since: datetime) -> int:
        result = await self.db.execute(
            select(func.count(SSOAuditLog.id)).where(
                SSOAuditLog.company_id == company_id,
                SSOAuditLog.created_at >= since,
            )
        )
        return result.scalar_one() or 0

    # ── WorkOSGroup ──────────────────────────────────────────────────────────

    async def list_groups(self, directory_id: str) -> list[WorkOSGroup]:
        result = await self.db.execute(
            select(WorkOSGroup).where(
                WorkOSGroup.is_active == True,  # noqa: E712
                WorkOSGroup.directory_id == directory_id,
            )
        )
        return list(result.scalars().all())

    async def count_groups(self, directory_id: str) -> int:
        result = await self.db.execute(
            select(func.count(WorkOSGroup.id)).where(
                WorkOSGroup.is_active == True,  # noqa: E712
                WorkOSGroup.directory_id == directory_id,
            )
        )
        return result.scalar_one() or 0

    async def get_group_by_id(self, group_id: UUID) -> WorkOSGroup | None:
        result = await self.db.execute(
            select(WorkOSGroup).where(WorkOSGroup.id == group_id)
        )
        return result.scalar_one_or_none()

    async def get_group_by_workos_id(self, workos_id: str) -> WorkOSGroup | None:
        result = await self.db.execute(
            select(WorkOSGroup).where(WorkOSGroup.workos_id == workos_id)
        )
        return result.scalar_one_or_none()

    async def upsert_group(
        self,
        workos_id: str,
        directory_id: str,
        name: str,
        raw_attributes: dict | None = None,
        is_active: bool = True,
    ) -> WorkOSGroup:
        """Create or update a WorkOSGroup by workos_id."""
        existing = await self.get_group_by_workos_id(workos_id)
        if existing:
            existing.name = name or existing.name
            existing.directory_id = directory_id or existing.directory_id
            if raw_attributes is not None:
                existing.raw_attributes = raw_attributes
            existing.is_active = is_active
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        group = WorkOSGroup(
            workos_id=workos_id,
            directory_id=directory_id,
            name=name or "Unknown Group",
            raw_attributes=raw_attributes or {},
            is_active=is_active,
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def deactivate_group(self, workos_id: str) -> WorkOSGroup | None:
        group = await self.get_group_by_workos_id(workos_id)
        if not group:
            return None
        group.is_active = False
        group.updated_at = datetime.utcnow()
        await self.db.commit()
        return group

    async def update_group(self, workos_id: str, data: dict) -> WorkOSGroup | None:
        group = await self.get_group_by_workos_id(workos_id)
        if not group:
            return None
        for key, value in data.items():
            if hasattr(group, key):
                setattr(group, key, value)
        group.updated_at = datetime.utcnow()
        await self.db.commit()
        return group

    # ── WorkOSGroupMembership ────────────────────────────────────────────────

    async def get_membership(
        self, group_id: UUID, user_id: UUID
    ) -> WorkOSGroupMembership | None:
        result = await self.db.execute(
            select(WorkOSGroupMembership).where(
                WorkOSGroupMembership.group_id == group_id,
                WorkOSGroupMembership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_membership(self, group_id: UUID, user_id: UUID, added_by: str) -> WorkOSGroupMembership:
        # RLS-EXEMPT: workos_group_memberships has no company_id column (WorkOS IdP sync is per-user across SSO groups; tenant scope lives in the parent WorkOSGroup record)  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
        membership = WorkOSGroupMembership(
            group_id=group_id,
            user_id=user_id,
            added_by=added_by,
        )
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)
        return membership

    async def remove_membership(self, group_id: UUID, user_id: UUID) -> bool:
        membership = await self.get_membership(group_id, user_id)
        if not membership:
            return False
        await self.db.delete(membership)
        await self.db.commit()
        return True

    # ── WorkOSGroupRoleMapping ───────────────────────────────────────────────

    async def list_groups_for_user(self, user_id) -> list[WorkOSGroup]:
        """List all WorkOS groups a user belongs to (via membership).

        Sprint 4 RBAC (2026-05-25): canonical lookup for re-computing user.role
        when SCIM group membership changes (dsync.group.user_added/removed).
        """
        from app.auth.workos_models import WorkOSGroupMembership
        result = await self.db.execute(
            select(WorkOSGroup).join(
                WorkOSGroupMembership,
                WorkOSGroupMembership.group_id == WorkOSGroup.id,
            ).where(WorkOSGroupMembership.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_role_mappings(self, company_id: str) -> list[WorkOSGroupRoleMapping]:
        result = await self.db.execute(
            select(WorkOSGroupRoleMapping).where(
                WorkOSGroupRoleMapping.company_id == company_id
            )
        )
        return list(result.scalars().all())

    async def get_role_mapping(
        self, company_id: str, workos_group_id: UUID
    ) -> WorkOSGroupRoleMapping | None:
        result = await self.db.execute(
            select(WorkOSGroupRoleMapping).where(
                WorkOSGroupRoleMapping.company_id == company_id,
                WorkOSGroupRoleMapping.workos_group_id == workos_group_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_role_mapping(
        self,
        company_id: str,
        workos_group_id: UUID,
        role: str,
        permissions: list[str],
    ) -> WorkOSGroupRoleMapping:
        existing = await self.get_role_mapping(company_id, workos_group_id)
        if existing:
            existing.role = role
            existing.permissions = permissions
            await self.db.commit()
            return existing
        mapping = WorkOSGroupRoleMapping(
            company_id=company_id,
            workos_group_id=workos_group_id,
            role=role,
            permissions=permissions,
        )
        self.db.add(mapping)
        await self.db.commit()
        return mapping

    # ── ClientAccount lookup (for SSO domain check) ──────────────────────────

    async def get_client_by_id(self, client_id: UUID) -> ClientAccount | None:
        result = await self.db.execute(
            select(ClientAccount).where(ClientAccount.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_client_by_email_domain(self, domain: str) -> ClientAccount | None:
        from sqlalchemy import func as sqlfunc
        result = await self.db.execute(
            select(ClientAccount).where(
                sqlfunc.lower(ClientAccount.primary_email).like(f"%@{domain}")
            )
        )
        return result.scalar_one_or_none()

    async def get_config_for_client(
        self, company_id: str, sso_required: bool = True
    ) -> CompanyWorkOSConfig | None:
        query = select(CompanyWorkOSConfig).where(
            CompanyWorkOSConfig.company_id == company_id
        )
        if sso_required:
            query = query.where(CompanyWorkOSConfig.sso_enabled == True)  # noqa: E712
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
