"""
Client Users API Endpoints.

Provides CRUD operations for managing users within a client company.
Multi-tenant user management with roles and permissions.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import os
from uuid import UUID

from app.core.database import get_db
from app.models.client_user import (
    ClientUser, ClientUserRole, ClientUserStatus,
    CLIENT_USER_ROLE_OPTIONS, CLIENT_USER_STATUS_OPTIONS
)
from app.models.client_account import ClientAccount
from app.models.audit_log import AuditLog
from app.schemas.client_user import (
    ClientUserCreate, ClientUserUpdate, ClientUserRoleUpdate, ClientUserResponse,
    AcceptInvitationRequest, AcceptInvitationResponse
)
from app.services.email_service import email_service

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://app.wedotalent.com")

logger = logging.getLogger(__name__)


async def log_user_audit(
    db: AsyncSession,
    company_id: str,
    action: str,
    user_email: str,
    performed_by: str,
    details: Dict[str, Any] = None
) -> None:
    """
    Log an audit entry for user management actions.
    
    Args:
        db: Database session
        company_id: Company ID
        action: Action performed (create, update, delete, role_change, etc.)
        user_email: Email of the user being managed
        performed_by: ID of the user performing the action
        details: Additional details about the action
    """
    try:
        audit_log = AuditLog(
            company_id=company_id,
            agent_name="user_management",
            decision_type="user_management",
            action=action,
            decision=action,
            reasoning=[{
                "action": action,
                "target_user": user_email,
                "performed_by": performed_by,
                "details": details or {}
            }],
            criteria_used=["user_management_policy"],
            criteria_ignored=[]
        )
        db.add(audit_log)
        await db.flush()
        logger.info(f"📝 Audit log: {action} for user {user_email} by {performed_by}")
    except Exception as e:
        logger.warning(f"Failed to create audit log: {str(e)}")

router = APIRouter(prefix="/clients/{client_id}/users", tags=["client-users"])

invitation_router = APIRouter(prefix="/invitations", tags=["invitations"])


@invitation_router.post("/accept", summary="Accept invitation")
async def accept_invitation(
    data: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept an invitation using the token from the email link.
    This endpoint is unauthenticated - only requires a valid token.
    """
    try:
        query = select(ClientUser).where(
            and_(
                ClientUser.invitation_token == data.token,
                ClientUser.is_deleted == False
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"❌ Invalid invitation token attempt: {data.token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invitation token"
            )
        
        if user.status != ClientUserStatus.PENDING.value:
            logger.warning(f"❌ Attempt to accept invitation for non-pending user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been accepted"
            )
        
        if not user.is_invitation_valid():
            logger.warning(f"❌ Expired invitation token for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired. Please request a new invitation."
            )
        
        user.clear_invitation()
        user.updated_at = datetime.utcnow()
        
        await log_user_audit(
            db=db,
            company_id=str(user.company_id),
            action="invitation_accepted",
            user_email=user.email,
            performed_by=str(user.id),
            details={"accepted_at": datetime.utcnow().isoformat()}
        )
        
        await db.commit()
        await db.refresh(user)
        
        redirect_url = f"{FRONTEND_URL}/login?invitation_accepted=true"
        
        logger.info(f"✅ Invitation accepted: {user.email} (ID: {user.id})")
        
        return AcceptInvitationResponse(
            success=True,
            message="Invitation accepted successfully. You can now log in.",
            redirect_url=redirect_url,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "status": user.status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error accepting invitation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invitation: {str(e)}"
        )


@invitation_router.get("/validate", summary="Validate invitation token")
async def validate_invitation(
    token: str = Query(..., description="Invitation token to validate"),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate an invitation token without accepting it.
    Returns basic info about the invitation if valid.
    """
    try:
        query = select(ClientUser).where(
            and_(
                ClientUser.invitation_token == token,
                ClientUser.is_deleted == False
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return {
                "valid": False,
                "reason": "Token not found"
            }
        
        if user.status != ClientUserStatus.PENDING.value:
            return {
                "valid": False,
                "reason": "Invitation already accepted"
            }
        
        if not user.is_invitation_valid():
            return {
                "valid": False,
                "reason": "Invitation expired"
            }
        
        client_query = select(ClientAccount).where(ClientAccount.id == user.company_id)
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        return {
            "valid": True,
            "user_name": user.name,
            "user_email": user.email,
            "role": user.role,
            "company_name": client.name if client else "Empresa",
            "expires_at": user.invitation_expires_at.isoformat() if user.invitation_expires_at else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error validating invitation: {str(e)}", exc_info=True)
        return {
            "valid": False,
            "reason": "Validation error"
        }


def get_user_from_headers(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> Dict[str, Any]:
    """
    Get user context from request headers.
    """
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company ID required. Please provide X-Company-ID header."
        )
    
    return {
        "company_id": x_company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }


def validate_client_access(client_id: str, current_user: Dict[str, Any]) -> None:
    """
    Validate that the user has access to the specified client.
    Admin users can access any client, others only their own company.
    """
    is_admin = current_user.get("is_admin", False)
    user_company_id = current_user.get("company_id")
    
    if not is_admin and client_id != user_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. X-Company-ID must match the client_id in the path."
        )


async def verify_client_exists(client_id: str, db: AsyncSession) -> ClientAccount:
    """
    Verify that the client exists and is not deleted.
    """
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID format"
        )
    
    query = select(ClientAccount).where(
        and_(
            ClientAccount.id == client_uuid,
            ClientAccount.is_deleted == False
        )
    )
    result = await db.execute(query)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client not found: {client_id}"
        )
    
    return client


@router.get("/options", summary="List available role and status options")
async def list_options():
    """List all available role and status options for client users."""
    return {
        "success": True,
        "data": {
            "roles": CLIENT_USER_ROLE_OPTIONS,
            "statuses": CLIENT_USER_STATUS_OPTIONS
        }
    }


@router.get("", summary="List users for a client")
async def list_client_users(
    client_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users for a specific client.
    """
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, db)
        
        client_uuid = UUID(client_id)
        
        conditions = [
            ClientUser.company_id == client_uuid,
            ClientUser.is_deleted == False
        ]
        
        if status:
            conditions.append(ClientUser.status == status)
        
        if role:
            conditions.append(ClientUser.role == role)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    ClientUser.name.ilike(search_term),
                    ClientUser.email.ilike(search_term)
                )
            )
        
        query = select(ClientUser).where(and_(*conditions))
        query = query.order_by(ClientUser.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        count_query = select(func.count(ClientUser.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        logger.info(f"📋 Listed {len(users)} users for client {client_id} (total: {total})")
        
        return {
            "success": True,
            "data": {
                "users": [u.to_dict() for u in users],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing client users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/{user_id}", summary="Get user by ID")
async def get_client_user(
    client_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific user by ID for a client.
    """
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, db)
        
        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        
        query = select(ClientUser).where(
            and_(
                ClientUser.id == user_uuid,
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        return {
            "success": True,
            "data": user.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create/invite user")
async def create_client_user(
    client_id: str,
    data: ClientUserCreate,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or invite a new user to a client.
    """
    try:
        validate_client_access(client_id, current_user)
        client = await verify_client_exists(client_id, db)
        
        client_uuid = UUID(client_id)
        
        user_limit = client.user_limit or 10
        active_users_query = select(func.count(ClientUser.id)).where(
            and_(
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False
            )
        )
        active_users_result = await db.execute(active_users_query)
        current_user_count = active_users_result.scalar() or 0
        
        if current_user_count >= user_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite de licenças atingido ({current_user_count}/{user_limit}). Entre em contato com o suporte WEDOTALENT para aumentar seu plano."
            )
        
        valid_roles = [r.value for r in ClientUserRole]
        if data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        existing_query = select(ClientUser).where(
            and_(
                ClientUser.company_id == client_uuid,
                ClientUser.email == data.email,
                ClientUser.is_deleted == False
            )
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {data.email} already exists for this client"
            )
        
        user = ClientUser(
            company_id=client_uuid,
            email=data.email,
            name=data.name,
            role=data.role,
            permissions=data.permissions or [],
            status=ClientUserStatus.PENDING.value,
        )
        
        token = user.generate_invitation_token()
        
        db.add(user)
        await db.flush()
        
        accept_url = f"{FRONTEND_URL}/aceitar-convite?token={token}"
        inviter_name = current_user.get("user_id", "Sistema")
        
        email_sent = False
        try:
            email_sent = await email_service.send_invite_email(
                client_user=user,
                accept_url=accept_url,
                inviter_name=inviter_name,
                db=db
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send invitation email: {str(e)}")
        
        await log_user_audit(
            db=db,
            company_id=client_id,
            action="user_created",
            user_email=data.email,
            performed_by=current_user.get("user_id", "system"),
            details={
                "role": data.role, 
                "name": data.name,
                "invitation_token_generated": True,
                "invitation_expires_at": user.invitation_expires_at.isoformat() if user.invitation_expires_at else None,
                "email_sent": email_sent
            }
        )
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✅ Created/invited user: {user.email} for client {client.name} (ID: {user.id}, email_sent: {email_sent})")
        
        return {
            "success": True,
            "message": "User invited successfully" + (" and email sent" if email_sent else " (email pending)"),
            "data": user.to_dict(),
            "invitation_url": accept_url,
            "email_sent": email_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.put("/{user_id}", summary="Update user")
async def update_client_user(
    client_id: str,
    user_id: str,
    data: ClientUserUpdate,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user for a client.
    """
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, db)
        
        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        
        query = select(ClientUser).where(
            and_(
                ClientUser.id == user_uuid,
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        if data.status:
            valid_statuses = [s.value for s in ClientUserStatus]
            if data.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await log_user_audit(
            db=db,
            company_id=client_id,
            action="user_updated",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={"updated_fields": list(update_data.keys())}
        )
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✅ Updated user: {user.email} (ID: {user.id})")
        
        return {
            "success": True,
            "message": "User updated successfully",
            "data": user.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", summary="Delete user (soft delete)")
async def delete_client_user(
    client_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a user from a client.
    """
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, db)
        
        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        
        query = select(ClientUser).where(
            and_(
                ClientUser.id == user_uuid,
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.deleted_by = current_user.get("user_id", "system")
        user.updated_at = datetime.utcnow()
        
        await log_user_audit(
            db=db,
            company_id=client_id,
            action="user_deleted",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={"user_id": str(user.id)}
        )
        
        await db.commit()
        
        logger.info(f"🗑️ Deleted user: {user.email} (ID: {user.id})")
        
        return {
            "success": True,
            "message": "User deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{user_id}/resend-invite", summary="Resend invitation")
async def resend_invite(
    client_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Resend invitation email to a pending user.
    """
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, db)
        
        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        
        query = select(ClientUser).where(
            and_(
                ClientUser.id == user_uuid,
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        if user.status != ClientUserStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resend invitation to pending users"
            )
        
        token = user.generate_invitation_token()
        user.updated_at = datetime.utcnow()
        
        accept_url = f"{FRONTEND_URL}/aceitar-convite?token={token}"
        inviter_name = current_user.get("user_id", "Sistema")
        
        email_sent = False
        try:
            email_sent = await email_service.send_invite_email(
                client_user=user,
                accept_url=accept_url,
                inviter_name=inviter_name,
                db=db
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send invitation email: {str(e)}")
        
        await log_user_audit(
            db=db,
            company_id=client_id,
            action="invitation_resent",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={
                "new_token_generated": True,
                "invitation_expires_at": user.invitation_expires_at.isoformat() if user.invitation_expires_at else None,
                "email_sent": email_sent
            }
        )
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"📧 Resent invitation to user: {user.email} (ID: {user.id}, email_sent: {email_sent})")
        
        return {
            "success": True,
            "message": "Invitation resent successfully" + (" and email sent" if email_sent else " (email pending)"),
            "data": user.to_dict(),
            "invitation_url": accept_url,
            "email_sent": email_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error resending invite: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend invitation: {str(e)}"
        )


@router.put("/{user_id}/role", summary="Update user role")
async def update_user_role(
    client_id: str,
    user_id: str,
    data: ClientUserRoleUpdate,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the role of a user.
    """
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, db)
        
        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        
        valid_roles = [r.value for r in ClientUserRole]
        if data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        query = select(ClientUser).where(
            and_(
                ClientUser.id == user_uuid,
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        old_role = user.role
        user.role = data.role
        user.updated_at = datetime.utcnow()
        
        await log_user_audit(
            db=db,
            company_id=client_id,
            action="user_role_changed",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={"old_role": old_role, "new_role": data.role}
        )
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✅ Updated user role: {user.email} from {old_role} to {data.role}")
        
        return {
            "success": True,
            "message": f"User role updated from {old_role} to {data.role}",
            "data": user.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating user role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}"
        )
