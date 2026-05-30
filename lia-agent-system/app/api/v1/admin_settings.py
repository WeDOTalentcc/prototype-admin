"""
Admin Settings API endpoints for RBAC, notifications, and security.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.models.admin_settings import (
    AVAILABLE_PERMISSIONS,
    NOTIFICATION_EVENT_TYPES,
    PermissionLevel,
)
from app.domains.admin_settings.dependencies import get_admin_settings_repo
from app.domains.admin_settings.repositories.admin_settings_repository import (
    AdminSettingsRepository,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-settings"])


def verify_ownership(resource, company_id: uuid.UUID, resource_name: str = "Resource"):
    """Verify that a resource belongs to the specified company."""
    if resource is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    if resource.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")


def _check_admin_tenant_access(admin: User, company_id: str) -> None:
    """Validate company_id format and audit cross-tenant admin access.

    Admins may legitimately manage any tenant, but every cross-tenant
    operation is logged so that lateral movement is detectable in audit trails.
    Non-admin access is blocked upstream by require_admin.
    """
    try:
        uuid.UUID(company_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid company_id format")

    if admin.company_id and str(admin.company_id) != str(company_id):
        logger.warning(
            "[AUDIT:CROSS-TENANT] Admin accessing foreign tenant — "
            "admin_id=%s admin_company=%s target_company=%s",
            admin.id, admin.company_id, company_id,
        )


class RoleCreate(WeDoBaseModel):
    name: str
    description: str | None = None
    permissions: dict[str, str] = {}


class RoleUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    permissions: dict[str, str] | None = None
    is_active: bool | None = None


class UserRoleAssign(BaseModel):
    user_id: str
    role_id: str
    assigned_by: str | None = None


class NotificationPolicyCreate(WeDoBaseModel):
    name: str
    event_type: str
    channels: list[str] = []
    recipient_type: str | None = None
    recipients: list[str] = []
    subject_template: str | None = None
    body_template: str | None = None
    is_enabled: bool = True


class NotificationPolicyUpdate(WeDoBaseModel):
    name: str | None = None
    event_type: str | None = None
    channels: list[str] | None = None
    recipient_type: str | None = None
    recipients: list[str] | None = None
    subject_template: str | None = None
    body_template: str | None = None
    is_enabled: bool | None = None


class SecuritySettingUpdate(WeDoBaseModel):
    require_2fa: bool | None = None
    session_timeout_minutes: int | None = None
    max_login_attempts: int | None = None
    password_min_length: int | None = None
    password_require_uppercase: bool | None = None
    password_require_numbers: bool | None = None
    password_require_special: bool | None = None
    password_expiry_days: int | None = None
    ip_whitelist: list[str] | None = None
    ip_blacklist: list[str] | None = None
    audit_logging_enabled: bool | None = None
    audit_retention_days: int | None = None
    data_export_allowed: bool | None = None
    data_retention_days: int | None = None


@router.get("/roles", response_model=None)
async def list_roles(
    company_id: str = Query(..., description="Company ID"),
    include_inactive: bool = Query(False, description="Include inactive roles"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """List all roles for a company."""
    _check_admin_tenant_access(admin, company_id)
    try:
        roles = await repo.list_roles(
            company_id=uuid.UUID(company_id),
            include_inactive=include_inactive,
        )
        return {
            "success": True,
            "data": [role.to_dict() for role in roles],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles", response_model=None)
async def create_role(
    data: RoleCreate,
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Create a new role."""
    _check_admin_tenant_access(admin, company_id)
    try:
        role = await repo.create_role(
            company_id=uuid.UUID(company_id),
            name=data.name,
            description=data.description,
            permissions=data.permissions,
            is_system_role=False,
        )
        return {
            "success": True,
            "data": role.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/roles/{role_id}", response_model=None)
async def update_role(
    role_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: RoleUpdate,
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Update a role."""
    _check_admin_tenant_access(admin, company_id)
    try:
        role = await repo.get_role_by_id(uuid.UUID(role_id))

        verify_ownership(role, uuid.UUID(company_id), "Role")

        if role.is_system_role and data.name is not None:
            raise HTTPException(status_code=400, detail="Cannot rename system roles")

        role = await repo.update_role(
            role=role,
            name=data.name,
            description=data.description,
            permissions=data.permissions,
            is_active=data.is_active,
        )
        return {
            "success": True,
            "data": role.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/roles/{role_id}", response_model=None)
async def delete_role(
    role_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Delete a role (soft delete by setting is_active=False)."""
    _check_admin_tenant_access(admin, company_id)
    try:
        role = await repo.get_role_by_id(uuid.UUID(role_id))

        verify_ownership(role, uuid.UUID(company_id), "Role")

        if role.is_system_role:
            raise HTTPException(status_code=400, detail="Cannot delete system roles")

        await repo.soft_delete_role(role)
        return {
            "success": True,
            "message": "Role deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles/initialize", response_model=None)
async def initialize_default_roles(
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Initialize default roles for a company."""
    _check_admin_tenant_access(admin, company_id)
    try:
        created_roles = await repo.initialize_default_roles(uuid.UUID(company_id))
        return {
            "success": True,
            "message": f"Initialized {len(created_roles)} default roles",
            "created_roles": created_roles,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing default roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-roles", response_model=None)
async def list_user_roles(
    company_id: str = Query(..., description="Company ID"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """List user role assignments."""
    _check_admin_tenant_access(admin, company_id)
    try:
        uid = uuid.UUID(user_id) if user_id else None
        assignments = await repo.list_user_roles(
            company_id=uuid.UUID(company_id),
            user_id=uid,
        )
        return {
            "success": True,
            "data": [a.to_dict() for a in assignments],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing user roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-roles", response_model=None)
async def assign_role_to_user(
    data: UserRoleAssign,
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Assign a role to a user."""
    _check_admin_tenant_access(admin, company_id)
    try:
        company_uuid = uuid.UUID(company_id)
        user_uuid = uuid.UUID(data.user_id)
        role_uuid = uuid.UUID(data.role_id)

        role = await repo.get_role_by_id(role_uuid)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        existing = await repo.get_user_role_assignment(
            user_id=user_uuid,
            role_id=role_uuid,
            company_id=company_uuid,
        )
        if existing:
            raise HTTPException(status_code=400, detail="User already has this role")

        assignment = await repo.assign_role(
            user_id=user_uuid,
            role_id=role_uuid,
            company_id=company_uuid,
            assigned_by=data.assigned_by,
        )
        return {
            "success": True,
            "data": assignment.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user-roles/{assignment_id}", response_model=None)
async def remove_role_assignment(
    assignment_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Remove a role assignment."""
    _check_admin_tenant_access(admin, company_id)
    try:
        assignment = await repo.get_user_role_by_id(uuid.UUID(assignment_id))

        verify_ownership(assignment, uuid.UUID(company_id), "Assignment")

        await repo.remove_role_assignment(assignment)
        return {
            "success": True,
            "message": "Role assignment removed successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing role assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notification-policies", response_model=None)
async def list_notification_policies(
    company_id: str = Query(..., description="Company ID"),
    event_type: str | None = Query(None, description="Filter by event type"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """List notification policies."""
    _check_admin_tenant_access(admin, company_id)
    try:
        policies = await repo.list_notification_policies(
            company_id=uuid.UUID(company_id),
            event_type=event_type,
        )
        return {
            "success": True,
            "data": [p.to_dict() for p in policies],
            "event_types": NOTIFICATION_EVENT_TYPES,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing notification policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notification-policies", response_model=None)
async def create_notification_policy(
    data: NotificationPolicyCreate,
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Create a notification policy."""
    _check_admin_tenant_access(admin, company_id)
    try:
        policy = await repo.create_notification_policy(
            company_id=uuid.UUID(company_id),
            name=data.name,
            event_type=data.event_type,
            channels=data.channels,
            recipient_type=data.recipient_type,
            recipients=data.recipients,
            subject_template=data.subject_template,
            body_template=data.body_template,
            is_enabled=data.is_enabled,
        )
        return {
            "success": True,
            "data": policy.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notification-policies/{policy_id}", response_model=None)
async def update_notification_policy(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: NotificationPolicyUpdate,
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Update a notification policy."""
    _check_admin_tenant_access(admin, company_id)
    try:
        policy = await repo.get_notification_policy_by_id(uuid.UUID(policy_id))

        verify_ownership(policy, uuid.UUID(company_id), "Policy")

        policy = await repo.update_notification_policy(
            policy=policy,
            name=data.name,
            event_type=data.event_type,
            channels=data.channels,
            recipient_type=data.recipient_type,
            recipients=data.recipients,
            subject_template=data.subject_template,
            body_template=data.body_template,
            is_enabled=data.is_enabled,
        )
        return {
            "success": True,
            "data": policy.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notification-policies/{policy_id}", response_model=None)
async def delete_notification_policy(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Delete a notification policy."""
    _check_admin_tenant_access(admin, company_id)
    try:
        policy = await repo.get_notification_policy_by_id(uuid.UUID(policy_id))

        verify_ownership(policy, uuid.UUID(company_id), "Policy")

        await repo.delete_notification_policy(policy)
        return {
            "success": True,
            "message": "Policy deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security", response_model=None)
async def get_security_settings(
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Get security settings for a company."""
    _check_admin_tenant_access(admin, company_id)
    try:
        settings = await repo.get_or_create_security_settings(uuid.UUID(company_id))
        return {
            "success": True,
            "data": settings.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/security", response_model=None)
async def update_security_settings(
    data: SecuritySettingUpdate,
    company_id: str = Query(..., description="Company ID"),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Update security settings."""
    _check_admin_tenant_access(admin, company_id)
    try:
        settings = await repo.get_or_create_security_settings(uuid.UUID(company_id))
        settings = await repo.update_security_settings(
            settings=settings,
            require_2fa=data.require_2fa,
            session_timeout_minutes=data.session_timeout_minutes,
            max_login_attempts=data.max_login_attempts,
            password_min_length=data.password_min_length,
            password_require_uppercase=data.password_require_uppercase,
            password_require_numbers=data.password_require_numbers,
            password_require_special=data.password_require_special,
            password_expiry_days=data.password_expiry_days,
            ip_whitelist=data.ip_whitelist,
            ip_blacklist=data.ip_blacklist,
            audit_logging_enabled=data.audit_logging_enabled,
            audit_retention_days=data.audit_retention_days,
            data_export_allowed=data.data_export_allowed,
            data_retention_days=data.data_retention_days,
        )
        return {
            "success": True,
            "data": settings.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating security settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs", response_model=None)
async def get_audit_logs(
    company_id: str = Query(..., description="Company ID"),
    action: str | None = Query(None, description="Filter by action"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    repo: AdminSettingsRepository = Depends(get_admin_settings_repo),
    admin: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Get audit logs with filtering and pagination."""
    _check_admin_tenant_access(admin, company_id)
    try:
        from datetime import datetime

        uid = uuid.UUID(user_id) if user_id else None
        sd = datetime.fromisoformat(start_date) if start_date else None
        ed = datetime.fromisoformat(end_date) if end_date else None

        logs, total = await repo.get_audit_logs(
            company_id=uuid.UUID(company_id),
            action=action,
            resource_type=resource_type,
            user_id=uid,
            start_date=sd,
            end_date=ed,
            page=page,
            page_size=page_size,
        )
        return {
            "success": True,
            "data": [log.to_dict() for log in logs],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permissions-matrix", response_model=None)
async def get_permissions_matrix(_admin: User = Depends(require_admin), company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Get the available permissions matrix."""
    return {
        "success": True,
        "data": {
            "permissions": AVAILABLE_PERMISSIONS,
            "levels": [level.value for level in PermissionLevel],
        },
    }


@router.get("/notification-event-types", response_model=None)
async def get_notification_event_types(_admin: User = Depends(require_admin), company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Get available notification event types."""
    return {
        "success": True,
        "data": NOTIFICATION_EVENT_TYPES,
    }

reorder_collection_before_item(router)
