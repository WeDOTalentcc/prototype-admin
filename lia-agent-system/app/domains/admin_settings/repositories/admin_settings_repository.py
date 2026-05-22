"""
AdminSettingsRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/admin_settings.py.
"""
import logging
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin_settings import (
    DEFAULT_ROLES,
    AdminAuditLog,
    AdminRole,
    AdminUserRole,
    NotificationPolicy,
    SecuritySetting,
)

logger = logging.getLogger(__name__)


class AdminSettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Roles ────────────────────────────────────────────────────────────────

    async def list_roles(
        self,
        company_id: UUID,
        include_inactive: bool = False,
    ) -> list[AdminRole]:
        query = select(AdminRole).where(AdminRole.company_id == company_id)
        if not include_inactive:
            query = query.where(AdminRole.is_active)
        query = query.order_by(AdminRole.is_system_role.desc(), AdminRole.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_role_by_id(self, role_id: UUID) -> AdminRole | None:
        result = await self.db.execute(
            # TENANT-EXEMPT: AdminRole/AdminUserRole/NotificationPolicy are platform-staff scope (WeDOTalent admin), not customer-tenant; T-RATCHET tenant_filter
            select(AdminRole).where(AdminRole.id == role_id)
        )
        return result.scalar_one_or_none()

    async def create_role(
        self,
        company_id: UUID,
        name: str,
        description: str | None,
        permissions: dict[str, str],
        is_system_role: bool = False,
    ) -> AdminRole:
        role = AdminRole(
            company_id=company_id,
            name=name,
            description=description,
            permissions=permissions,
            is_system_role=is_system_role,
            is_active=True,
        )
        self.db.add(role)
        await self.db.flush()
        return role

    async def update_role(
        self,
        role: AdminRole,
        name: str | None = None,
        description: str | None = None,
        permissions: dict[str, str] | None = None,
        is_active: bool | None = None,
    ) -> AdminRole:
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if permissions is not None:
            role.permissions = permissions
        if is_active is not None:
            role.is_active = is_active
        role.updated_at = datetime.utcnow()
        return role

    async def soft_delete_role(self, role: AdminRole) -> AdminRole:
        role.is_active = False
        role.updated_at = datetime.utcnow()
        return role

    async def get_system_roles_for_company(self, company_id: UUID) -> list[AdminRole]:
        result = await self.db.execute(
            select(AdminRole).where(
                AdminRole.company_id == company_id,
                AdminRole.is_system_role,
            )
        )
        return list(result.scalars().all())

    async def initialize_default_roles(self, company_id: UUID) -> list[str]:
        existing_roles = await self.get_system_roles_for_company(company_id)
        existing_names = {r.name for r in existing_roles}

        created_names: list[str] = []
        for role_data in DEFAULT_ROLES:
            if role_data["name"] not in existing_names:
                await self.create_role(
                    company_id=company_id,
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_system_role=True,
                )
                created_names.append(role_data["name"])
        return created_names

    # ── User Roles ────────────────────────────────────────────────────────────

    async def list_user_roles(
        self,
        company_id: UUID,
        user_id: UUID | None = None,
    ) -> list[AdminUserRole]:
        query = (
            select(AdminUserRole)
            .options(selectinload(AdminUserRole.role))
            .where(AdminUserRole.company_id == company_id)
        )
        if user_id is not None:
            query = query.where(AdminUserRole.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_role_assignment(
        self,
        user_id: UUID,
        role_id: UUID,
        company_id: UUID,
    ) -> AdminUserRole | None:
        result = await self.db.execute(
            select(AdminUserRole).where(
                AdminUserRole.user_id == user_id,
                AdminUserRole.role_id == role_id,
                AdminUserRole.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        company_id: UUID,
        assigned_by: str | None = None,
    ) -> AdminUserRole:
        assignment = AdminUserRole(
            user_id=user_id,
            role_id=role_id,
            company_id=company_id,
            assigned_by=assigned_by,
        )
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment, ["role"])
        return assignment

    async def get_user_role_by_id(self, assignment_id: UUID) -> AdminUserRole | None:
        result = await self.db.execute(
            # TENANT-EXEMPT: AdminRole/AdminUserRole/NotificationPolicy are platform-staff scope (WeDOTalent admin), not customer-tenant; T-RATCHET tenant_filter
            select(AdminUserRole).where(AdminUserRole.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def remove_role_assignment(self, assignment: AdminUserRole) -> None:
        await self.db.delete(assignment)

    # ── Notification Policies ─────────────────────────────────────────────────

    async def list_notification_policies(
        self,
        company_id: UUID,
        event_type: str | None = None,
    ) -> list[NotificationPolicy]:
        query = select(NotificationPolicy).where(
            NotificationPolicy.company_id == company_id
        )
        if event_type is not None:
            query = query.where(NotificationPolicy.event_type == event_type)
        query = query.order_by(NotificationPolicy.event_type, NotificationPolicy.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_notification_policy_by_id(self, policy_id: UUID) -> NotificationPolicy | None:
        result = await self.db.execute(
            # TENANT-EXEMPT: AdminRole/AdminUserRole/NotificationPolicy are platform-staff scope (WeDOTalent admin), not customer-tenant; T-RATCHET tenant_filter
            select(NotificationPolicy).where(NotificationPolicy.id == policy_id)
        )
        return result.scalar_one_or_none()

    async def create_notification_policy(
        self,
        company_id: UUID,
        name: str,
        event_type: str,
        channels: list[str],
        recipient_type: str | None,
        recipients: list[str],
        subject_template: str | None,
        body_template: str | None,
        is_enabled: bool,
    ) -> NotificationPolicy:
        policy = NotificationPolicy(
            company_id=company_id,
            name=name,
            event_type=event_type,
            channels=channels,
            recipient_type=recipient_type,
            recipients=recipients,
            subject_template=subject_template,
            body_template=body_template,
            is_enabled=is_enabled,
        )
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def update_notification_policy(
        self,
        policy: NotificationPolicy,
        name: str | None = None,
        event_type: str | None = None,
        channels: list[str] | None = None,
        recipient_type: str | None = None,
        recipients: list[str] | None = None,
        subject_template: str | None = None,
        body_template: str | None = None,
        is_enabled: bool | None = None,
    ) -> NotificationPolicy:
        if name is not None:
            policy.name = name
        if event_type is not None:
            policy.event_type = event_type
        if channels is not None:
            policy.channels = channels
        if recipient_type is not None:
            policy.recipient_type = recipient_type
        if recipients is not None:
            policy.recipients = recipients
        if subject_template is not None:
            policy.subject_template = subject_template
        if body_template is not None:
            policy.body_template = body_template
        if is_enabled is not None:
            policy.is_enabled = is_enabled
        policy.updated_at = datetime.utcnow()
        return policy

    async def delete_notification_policy(self, policy: NotificationPolicy) -> None:
        await self.db.delete(policy)

    # ── Security Settings ─────────────────────────────────────────────────────

    async def get_security_settings(self, company_id: UUID) -> SecuritySetting | None:
        result = await self.db.execute(
            select(SecuritySetting).where(
                SecuritySetting.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_security_settings(self, company_id: UUID) -> SecuritySetting:
        settings = await self.get_security_settings(company_id)
        if not settings:
            settings = SecuritySetting(company_id=company_id)
            self.db.add(settings)
            await self.db.flush()
        return settings

    async def update_security_settings(
        self,
        settings: SecuritySetting,
        require_2fa: bool | None = None,
        session_timeout_minutes: int | None = None,
        max_login_attempts: int | None = None,
        password_min_length: int | None = None,
        password_require_uppercase: bool | None = None,
        password_require_numbers: bool | None = None,
        password_require_special: bool | None = None,
        password_expiry_days: int | None = None,
        ip_whitelist: list[str] | None = None,
        ip_blacklist: list[str] | None = None,
        audit_logging_enabled: bool | None = None,
        audit_retention_days: int | None = None,
        data_export_allowed: bool | None = None,
        data_retention_days: int | None = None,
    ) -> SecuritySetting:
        if require_2fa is not None:
            settings.require_2fa = require_2fa
        if session_timeout_minutes is not None:
            settings.session_timeout_minutes = session_timeout_minutes
        if max_login_attempts is not None:
            settings.max_login_attempts = max_login_attempts
        if password_min_length is not None:
            settings.password_min_length = password_min_length
        if password_require_uppercase is not None:
            settings.password_require_uppercase = password_require_uppercase
        if password_require_numbers is not None:
            settings.password_require_numbers = password_require_numbers
        if password_require_special is not None:
            settings.password_require_special = password_require_special
        if password_expiry_days is not None:
            settings.password_expiry_days = password_expiry_days
        if ip_whitelist is not None:
            settings.ip_whitelist = ip_whitelist
        if ip_blacklist is not None:
            settings.ip_blacklist = ip_blacklist
        if audit_logging_enabled is not None:
            settings.audit_logging_enabled = audit_logging_enabled
        if audit_retention_days is not None:
            settings.audit_retention_days = audit_retention_days
        if data_export_allowed is not None:
            settings.data_export_allowed = data_export_allowed
        if data_retention_days is not None:
            settings.data_retention_days = data_retention_days
        settings.updated_at = datetime.utcnow()
        await self.db.flush()
        return settings

    # ── Audit Logs ────────────────────────────────────────────────────────────

    async def get_audit_logs(
        self,
        company_id: UUID,
        action: str | None = None,
        resource_type: str | None = None,
        user_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AdminAuditLog], int]:
        query = select(AdminAuditLog).where(
            AdminAuditLog.company_id == company_id
        )

        if action is not None:
            query = query.where(AdminAuditLog.action == action)
        if resource_type is not None:
            query = query.where(AdminAuditLog.resource_type == resource_type)
        if user_id is not None:
            query = query.where(AdminAuditLog.user_id == user_id)
        if start_date is not None:
            query = query.where(AdminAuditLog.created_at >= start_date)
        if end_date is not None:
            query = query.where(AdminAuditLog.created_at <= end_date)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(AdminAuditLog.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total
