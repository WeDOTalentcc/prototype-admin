"""
Admin Settings API endpoints for RBAC, notifications, and security.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy import select, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime
import uuid

from app.models.admin_settings import (
    AdminRole,
    AdminUserRole,
    NotificationPolicy,
    SecuritySetting,
    AdminAuditLog,
    DEFAULT_ROLES,
    AVAILABLE_PERMISSIONS,
    NOTIFICATION_EVENT_TYPES,
    PermissionLevel
)
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-settings"])


def verify_ownership(resource, company_id: uuid.UUID, resource_name: str = "Resource"):
    """Verify that a resource belongs to the specified company."""
    if resource is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    if resource.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, str] = {}


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class UserRoleAssign(BaseModel):
    user_id: str
    role_id: str
    assigned_by: Optional[str] = None


class NotificationPolicyCreate(BaseModel):
    name: str
    event_type: str
    channels: List[str] = []
    recipient_type: Optional[str] = None
    recipients: List[str] = []
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    is_enabled: bool = True


class NotificationPolicyUpdate(BaseModel):
    name: Optional[str] = None
    event_type: Optional[str] = None
    channels: Optional[List[str]] = None
    recipient_type: Optional[str] = None
    recipients: Optional[List[str]] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    is_enabled: Optional[bool] = None


class SecuritySettingUpdate(BaseModel):
    require_2fa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    max_login_attempts: Optional[int] = None
    password_min_length: Optional[int] = None
    password_require_uppercase: Optional[bool] = None
    password_require_numbers: Optional[bool] = None
    password_require_special: Optional[bool] = None
    password_expiry_days: Optional[int] = None
    ip_whitelist: Optional[List[str]] = None
    ip_blacklist: Optional[List[str]] = None
    audit_logging_enabled: Optional[bool] = None
    audit_retention_days: Optional[int] = None
    data_export_allowed: Optional[bool] = None
    data_retention_days: Optional[int] = None


@router.get("/roles")
async def list_roles(
    company_id: str = Query(..., description="Company ID"),
    include_inactive: bool = Query(False, description="Include inactive roles"),
    db: AsyncSession = Depends(get_db)
):
    """List all roles for a company."""
    try:
        query = select(AdminRole).where(AdminRole.company_id == uuid.UUID(company_id))
        if not include_inactive:
            query = query.where(AdminRole.is_active == True)
        query = query.order_by(AdminRole.is_system_role.desc(), AdminRole.name)
        
        result = await db.execute(query)
        roles = result.scalars().all()
        
        return {
            "success": True,
            "data": [role.to_dict() for role in roles]
        }
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles")
async def create_role(
    data: RoleCreate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role."""
    try:
        role = AdminRole(
            company_id=uuid.UUID(company_id),
            name=data.name,
            description=data.description,
            permissions=data.permissions,
            is_system_role=False,
            is_active=True
        )
        db.add(role)
        await db.flush()
        
        return {
            "success": True,
            "data": role.to_dict()
        }
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    data: RoleUpdate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update a role."""
    try:
        result = await db.execute(
            select(AdminRole).where(AdminRole.id == uuid.UUID(role_id))
        )
        role = result.scalar_one_or_none()
        
        verify_ownership(role, uuid.UUID(company_id), "Role")
        
        if role.is_system_role and data.name is not None:
            raise HTTPException(status_code=400, detail="Cannot rename system roles")
        
        if data.name is not None:
            role.name = data.name
        if data.description is not None:
            role.description = data.description
        if data.permissions is not None:
            role.permissions = data.permissions
        if data.is_active is not None:
            role.is_active = data.is_active
        
        role.updated_at = datetime.utcnow()
        
        return {
            "success": True,
            "data": role.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a role (soft delete by setting is_active=False)."""
    try:
        result = await db.execute(
            select(AdminRole).where(AdminRole.id == uuid.UUID(role_id))
        )
        role = result.scalar_one_or_none()
        
        verify_ownership(role, uuid.UUID(company_id), "Role")
        
        if role.is_system_role:
            raise HTTPException(status_code=400, detail="Cannot delete system roles")
        
        role.is_active = False
        role.updated_at = datetime.utcnow()
        
        return {
            "success": True,
            "message": "Role deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles/initialize")
async def initialize_default_roles(
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Initialize default roles for a company."""
    try:
        company_uuid = uuid.UUID(company_id)
        
        existing = await db.execute(
            select(AdminRole).where(
                AdminRole.company_id == company_uuid,
                AdminRole.is_system_role == True
            )
        )
        existing_roles = existing.scalars().all()
        existing_names = {r.name for r in existing_roles}
        
        created_roles = []
        for role_data in DEFAULT_ROLES:
            if role_data["name"] not in existing_names:
                role = AdminRole(
                    company_id=company_uuid,
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_system_role=True,
                    is_active=True
                )
                db.add(role)
                created_roles.append(role_data["name"])
        
        await db.flush()
        
        return {
            "success": True,
            "message": f"Initialized {len(created_roles)} default roles",
            "created_roles": created_roles
        }
    except Exception as e:
        logger.error(f"Error initializing default roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-roles")
async def list_user_roles(
    company_id: str = Query(..., description="Company ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db)
):
    """List user role assignments."""
    try:
        query = select(AdminUserRole).options(
            selectinload(AdminUserRole.role)
        ).where(AdminUserRole.company_id == uuid.UUID(company_id))
        
        if user_id:
            query = query.where(AdminUserRole.user_id == uuid.UUID(user_id))
        
        result = await db.execute(query)
        assignments = result.scalars().all()
        
        return {
            "success": True,
            "data": [a.to_dict() for a in assignments]
        }
    except Exception as e:
        logger.error(f"Error listing user roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-roles")
async def assign_role_to_user(
    data: UserRoleAssign,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Assign a role to a user."""
    try:
        company_uuid = uuid.UUID(company_id)
        user_uuid = uuid.UUID(data.user_id)
        role_uuid = uuid.UUID(data.role_id)
        
        role_result = await db.execute(
            select(AdminRole).where(AdminRole.id == role_uuid)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        existing = await db.execute(
            select(AdminUserRole).where(
                AdminUserRole.user_id == user_uuid,
                AdminUserRole.role_id == role_uuid,
                AdminUserRole.company_id == company_uuid
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already has this role")
        
        assignment = AdminUserRole(
            user_id=user_uuid,
            role_id=role_uuid,
            company_id=company_uuid,
            assigned_by=data.assigned_by
        )
        db.add(assignment)
        await db.flush()
        
        await db.refresh(assignment, ['role'])
        
        return {
            "success": True,
            "data": assignment.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user-roles/{assignment_id}")
async def remove_role_assignment(
    assignment_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Remove a role assignment."""
    try:
        result = await db.execute(
            select(AdminUserRole).where(AdminUserRole.id == uuid.UUID(assignment_id))
        )
        assignment = result.scalar_one_or_none()
        
        verify_ownership(assignment, uuid.UUID(company_id), "Assignment")
        
        await db.delete(assignment)
        
        return {
            "success": True,
            "message": "Role assignment removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing role assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notification-policies")
async def list_notification_policies(
    company_id: str = Query(..., description="Company ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    db: AsyncSession = Depends(get_db)
):
    """List notification policies."""
    try:
        query = select(NotificationPolicy).where(
            NotificationPolicy.company_id == uuid.UUID(company_id)
        )
        
        if event_type:
            query = query.where(NotificationPolicy.event_type == event_type)
        
        query = query.order_by(NotificationPolicy.event_type, NotificationPolicy.name)
        
        result = await db.execute(query)
        policies = result.scalars().all()
        
        return {
            "success": True,
            "data": [p.to_dict() for p in policies],
            "event_types": NOTIFICATION_EVENT_TYPES
        }
    except Exception as e:
        logger.error(f"Error listing notification policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notification-policies")
async def create_notification_policy(
    data: NotificationPolicyCreate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a notification policy."""
    try:
        policy = NotificationPolicy(
            company_id=uuid.UUID(company_id),
            name=data.name,
            event_type=data.event_type,
            channels=data.channels,
            recipient_type=data.recipient_type,
            recipients=data.recipients,
            subject_template=data.subject_template,
            body_template=data.body_template,
            is_enabled=data.is_enabled
        )
        db.add(policy)
        await db.flush()
        
        return {
            "success": True,
            "data": policy.to_dict()
        }
    except Exception as e:
        logger.error(f"Error creating notification policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notification-policies/{policy_id}")
async def update_notification_policy(
    policy_id: str,
    data: NotificationPolicyUpdate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update a notification policy."""
    try:
        result = await db.execute(
            select(NotificationPolicy).where(NotificationPolicy.id == uuid.UUID(policy_id))
        )
        policy = result.scalar_one_or_none()
        
        verify_ownership(policy, uuid.UUID(company_id), "Policy")
        
        if data.name is not None:
            policy.name = data.name
        if data.event_type is not None:
            policy.event_type = data.event_type
        if data.channels is not None:
            policy.channels = data.channels
        if data.recipient_type is not None:
            policy.recipient_type = data.recipient_type
        if data.recipients is not None:
            policy.recipients = data.recipients
        if data.subject_template is not None:
            policy.subject_template = data.subject_template
        if data.body_template is not None:
            policy.body_template = data.body_template
        if data.is_enabled is not None:
            policy.is_enabled = data.is_enabled
        
        policy.updated_at = datetime.utcnow()
        
        return {
            "success": True,
            "data": policy.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notification-policies/{policy_id}")
async def delete_notification_policy(
    policy_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification policy."""
    try:
        result = await db.execute(
            select(NotificationPolicy).where(NotificationPolicy.id == uuid.UUID(policy_id))
        )
        policy = result.scalar_one_or_none()
        
        verify_ownership(policy, uuid.UUID(company_id), "Policy")
        
        await db.delete(policy)
        
        return {
            "success": True,
            "message": "Policy deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security")
async def get_security_settings(
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get security settings for a company."""
    try:
        result = await db.execute(
            select(SecuritySetting).where(
                SecuritySetting.company_id == uuid.UUID(company_id)
            )
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = SecuritySetting(company_id=uuid.UUID(company_id))
            db.add(settings)
            await db.flush()
        
        return {
            "success": True,
            "data": settings.to_dict()
        }
    except Exception as e:
        logger.error(f"Error getting security settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/security")
async def update_security_settings(
    data: SecuritySettingUpdate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update security settings."""
    try:
        result = await db.execute(
            select(SecuritySetting).where(
                SecuritySetting.company_id == uuid.UUID(company_id)
            )
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = SecuritySetting(company_id=uuid.UUID(company_id))
            db.add(settings)
        
        if data.require_2fa is not None:
            settings.require_2fa = data.require_2fa
        if data.session_timeout_minutes is not None:
            settings.session_timeout_minutes = data.session_timeout_minutes
        if data.max_login_attempts is not None:
            settings.max_login_attempts = data.max_login_attempts
        if data.password_min_length is not None:
            settings.password_min_length = data.password_min_length
        if data.password_require_uppercase is not None:
            settings.password_require_uppercase = data.password_require_uppercase
        if data.password_require_numbers is not None:
            settings.password_require_numbers = data.password_require_numbers
        if data.password_require_special is not None:
            settings.password_require_special = data.password_require_special
        if data.password_expiry_days is not None:
            settings.password_expiry_days = data.password_expiry_days
        if data.ip_whitelist is not None:
            settings.ip_whitelist = data.ip_whitelist
        if data.ip_blacklist is not None:
            settings.ip_blacklist = data.ip_blacklist
        if data.audit_logging_enabled is not None:
            settings.audit_logging_enabled = data.audit_logging_enabled
        if data.audit_retention_days is not None:
            settings.audit_retention_days = data.audit_retention_days
        if data.data_export_allowed is not None:
            settings.data_export_allowed = data.data_export_allowed
        if data.data_retention_days is not None:
            settings.data_retention_days = data.data_retention_days
        
        settings.updated_at = datetime.utcnow()
        await db.flush()
        
        return {
            "success": True,
            "data": settings.to_dict()
        }
    except Exception as e:
        logger.error(f"Error updating security settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs")
async def get_audit_logs(
    company_id: str = Query(..., description="Company ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filtering and pagination."""
    try:
        query = select(AdminAuditLog).where(
            AdminAuditLog.company_id == uuid.UUID(company_id)
        )
        
        if action:
            query = query.where(AdminAuditLog.action == action)
        if resource_type:
            query = query.where(AdminAuditLog.resource_type == resource_type)
        if user_id:
            query = query.where(AdminAuditLog.user_id == uuid.UUID(user_id))
        if start_date:
            query = query.where(AdminAuditLog.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.where(AdminAuditLog.created_at <= datetime.fromisoformat(end_date))
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.order_by(desc(AdminAuditLog.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return {
            "success": True,
            "data": [log.to_dict() for log in logs],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permissions-matrix")
async def get_permissions_matrix():
    """Get the available permissions matrix."""
    return {
        "success": True,
        "data": {
            "permissions": AVAILABLE_PERMISSIONS,
            "levels": [level.value for level in PermissionLevel]
        }
    }


@router.get("/notification-event-types")
async def get_notification_event_types():
    """Get available notification event types."""
    return {
        "success": True,
        "data": NOTIFICATION_EVENT_TYPES
    }
