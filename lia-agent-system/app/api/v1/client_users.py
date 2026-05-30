"""
Client Users API.

Provides CRUD operations for managing users within a client company.
Multi-tenant user management with roles and permissions.

Onda 4.2f-P0.1 (2026-05-23): substituido X-User-Role/X-User-ID headers
em get_user_from_headers que eram FORJAVEIS = backdoor catastrofico
(privilege escalation cross-tenant via 1 header). Pattern canonical do
fix policies.py commit 1b487565: JWT-only via current_user.
"""
import logging
import os
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.core.database import get_db
from app.domains.client_users.dependencies import get_client_user_repo
from app.domains.client_users.repositories.client_user_repository import ClientUserRepository
from app.domains.communication.services.email_service import get_email_service
from app.domains.communication.services.email_service import EmailService
from app.models.client_user import (
    CLIENT_USER_ROLE_OPTIONS,
    CLIENT_USER_STATUS_OPTIONS,
    ClientUser,
    ClientUserRole,
    ClientUserStatus,
)
from app.schemas.client_user import (
    AcceptInvitationRequest,
    AcceptInvitationResponse,
    ClientUserCreate,
    ClientUserRoleUpdate,
    ClientUserUpdate,
)
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://app.wedotalent.com")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients/{client_id}/users", tags=["client-users"])

invitation_router = APIRouter(prefix="/invitations", tags=["invitations"])


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_user_from_headers(
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """Get user context from JWT (NO header).

    Onda 4.2f-P0.1 (2026-05-23): substituido X-User-Role/X-User-ID headers
    que eram FORJAVEIS = backdoor catastrofico (privilege escalation
    cross-tenant via 1 header `-H "X-User-Role: admin"`).

    Platform admin = role wedotalent_admin APENAS (staff WeDOTalent).
    Tenant admin (UserRole.admin) administra apenas a propria company.
    Nome `get_user_from_headers` mantido pra zero impacto callers.
    """
    return {
        "company_id": company_id,
        "user_id": str(current_user.id),
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        # Onda 4.2f-P0.1: is_admin = wedotalent_admin APENAS.
        "is_admin": current_user.role == UserRole.wedotalent_admin,
    }


def validate_client_access(client_id: str, current_user: dict[str, Any]) -> None:
    """Validate that the user has access to the specified client."""
    is_admin = current_user.get("is_admin", False)
    user_company_id = current_user.get("company_id")
    if not is_admin and client_id != user_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. company_id (from JWT) must match the client_id in the path.",
        )


async def verify_client_exists(client_id: str, repo: ClientUserRepository):
    """Verify that the client exists and is not deleted."""
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID format",
        )
    client = await repo.get_client_by_id(client_uuid)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client not found: {client_id}",
        )
    return client


# ---------------------------------------------------------------------------
# Invitation endpoints
# ---------------------------------------------------------------------------

@invitation_router.post("/accept", summary="Accept invitation")
async def accept_invitation(
    data: AcceptInvitationRequest,
    repo: ClientUserRepository = Depends(get_client_user_repo),
):
    """
    Accept an invitation using the token from the email link.
    This endpoint is unauthenticated - only requires a valid token.

    Onda 4.2f-B3 (2026-05-24): removido require_company_id que BLOQUEAVA
    fluxo. Invitee chega via email link SEM sessão — token É a autenticação.
    Antes flow estava completamente quebrado (401 em todo POST /accept).
    """
    try:
        user = await repo.get_by_invitation_token(data.token)

        if not user:
            logger.warning(f"Invalid invitation token attempt: {data.token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invitation token",
            )

        if user.status != ClientUserStatus.PENDING.value:
            logger.warning(f"Attempt to accept invitation for non-pending user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been accepted",
            )

        if not user.is_invitation_valid():
            logger.warning(f"Expired invitation token for user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired. Please request a new invitation.",
            )

        user.clear_invitation()
        user.updated_at = datetime.utcnow()

        await repo.log_audit(
            company_id=str(user.company_id),
            action="invitation_accepted",
            user_email=user.email,
            performed_by=str(user.id),
            details={"accepted_at": datetime.utcnow().isoformat()},
        )

        await repo.commit()
        await repo.refresh(user)

        redirect_url = f"{FRONTEND_URL}/login?invitation_accepted=true"
        logger.info(f"Invitation accepted: {user.id} (ID: {user.id})")

        return AcceptInvitationResponse(
            success=True,
            message="Invitation accepted successfully. You can now log in.",
            redirect_url=redirect_url,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "status": user.status,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error accepting invitation: {str(e)}", exc_info=True)
        # Onda 4.2f-B3: REGRA 5 — sem str(e) em response (OWASP A09 info disclosure)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation. Please contact support.",
        )


@invitation_router.get("/validate", summary="Validate invitation token")
async def validate_invitation(
    token: str = Query(..., description="Invitation token to validate"),
    repo: ClientUserRepository = Depends(get_client_user_repo),
):
    """
    Validate an invitation token without accepting it.
    Returns basic info about the invitation if valid.

    Onda 4.2f-B3 (2026-05-24): removido require_company_id (mesmo motivo
    de accept_invitation — invitee não tem sessão; token É a autenticação).
    """
    try:
        user = await repo.get_by_invitation_token(token)

        if not user:
            return {"valid": False, "reason": "Token not found"}

        if user.status != ClientUserStatus.PENDING.value:
            return {"valid": False, "reason": "Invitation already accepted"}

        if not user.is_invitation_valid():
            return {"valid": False, "reason": "Invitation expired"}

        client = await repo.get_client_by_id(user.company_id)

        return {
            "valid": True,
            "user_name": user.name,
            "user_email": user.email,
            "role": user.role,
            "company_name": client.name if client else "Empresa",
            "expires_at": user.invitation_expires_at.isoformat() if user.invitation_expires_at else None,
        }

    except Exception as e:
        logger.error(f"Error validating invitation: {str(e)}", exc_info=True)
        return {"valid": False, "reason": "Validation error"}


# ---------------------------------------------------------------------------
# Client-scoped user endpoints
# ---------------------------------------------------------------------------

@router.get("/options", summary="List available role and status options", response_model=None)
async def list_options(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all available role and status options for client users."""
    return {
        "success": True,
        "data": {
            "roles": CLIENT_USER_ROLE_OPTIONS,
            "statuses": CLIENT_USER_STATUS_OPTIONS,
        },
    }


@router.get("", summary="List users for a client", response_model=None)
async def list_client_users(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    status: str | None = Query(None, description="Filter by status"),
    role: str | None = Query(None, description="Filter by role"),
    search: str | None = Query(None, description="Search by name or email"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientUserRepository = Depends(get_client_user_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all users for a specific client."""
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, repo)

        client_uuid = UUID(client_id)

        users = await repo.list_users(
            client_uuid,
            status=status,
            role=role,
            search=search,
            limit=limit,
            offset=offset,
        )
        total = await repo.count_users(
            client_uuid,
            status=status,
            role=role,
            search=search,
        )

        logger.info(f"Listed {len(users)} users for client {client_id} (total: {total})")

        return {
            "success": True,
            "data": {
                "users": [u.to_dict() for u in users],
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing client users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}",
        )


@router.get("/{user_id}", summary="Get user by ID", response_model=None)
async def get_client_user(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientUserRepository = Depends(get_client_user_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific user by ID for a client."""
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, repo)

        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format",
            )

        user = await repo.get_by_id(user_uuid, client_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        return {"success": True, "data": user.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create/invite user", response_model=None)
async def create_client_user(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ClientUserCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientUserRepository = Depends(get_client_user_repo),
    email_svc: EmailService = Depends(get_email_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create or invite a new user to a client."""
    try:
        validate_client_access(client_id, current_user)
        client = await verify_client_exists(client_id, repo)

        client_uuid = UUID(client_id)

        user_limit = client.user_limit or 10
        current_user_count = await repo.count_active_users(client_uuid)

        if current_user_count >= user_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite de licencas atingido ({current_user_count}/{user_limit}). Entre em contato com o suporte WEDOTALENT para aumentar seu plano.",
            )

        valid_roles = [r.value for r in ClientUserRole]
        if data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
            )

        existing_user = await repo.get_by_email(data.email, client_uuid)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {data.email} already exists for this client",
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
        repo.add(user)
        await repo.flush()

        accept_url = f"{FRONTEND_URL}/aceitar-convite?token={token}"
        inviter_name = current_user.get("user_id", "Sistema")

        email_sent = False
        try:
            email_sent = await email_svc.send_invite_email(
                client_user=user,
                accept_url=accept_url,
                inviter_name=inviter_name,
                db=repo.db,
            )
        except Exception as e:
            logger.warning(f"Failed to send invitation email: {str(e)}")

        await repo.log_audit(
            company_id=client_id,
            action="user_created",
            user_email=data.email,
            performed_by=current_user.get("user_id", "system"),
            details={
                "role": data.role,
                "name": data.name,
                "invitation_token_generated": True,
                "invitation_expires_at": user.invitation_expires_at.isoformat() if user.invitation_expires_at else None,
                "email_sent": email_sent,
            },
        )

        await repo.commit()
        await repo.refresh(user)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created/invited user: {user.id} for client {client.name} (ID: {user.id}, email_sent: {email_sent})")

        return {
            "success": True,
            "message": "User invited successfully" + (" and email sent" if email_sent else " (email pending)"),
            "data": user.to_dict(),
            "invitation_url": accept_url,
            "email_sent": email_sent,
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.put("/{user_id}", summary="Update user", response_model=None)
async def update_client_user(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ClientUserUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientUserRepository = Depends(get_client_user_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a user for a client."""
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, repo)

        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format",
            )

        user = await repo.get_by_id(user_uuid, client_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        if data.status:
            valid_statuses = [s.value for s in ClientUserStatus]
            if data.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                )

        update_data = data.model_dump(exclude_unset=True)

        # Sprint 5.5 + Sprint 8 RBAC: PII grants require tenant admin role.
        # LGPD Art. 6 III minimização + Art. 5 II categorias sensíveis.
        # Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
        can_view_salary_change = None
        can_view_sensitive_pii_change = None
        actor_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
        actor_role_str = actor_role.value if hasattr(actor_role, "value") else str(actor_role) if actor_role else ""

        for grant_field in ("can_view_salary", "can_view_sensitive_pii"):
            if grant_field in update_data:
                if actor_role_str not in ("admin", "wedotalent_admin"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Only tenant admin can grant {grant_field}",
                    )

        if "can_view_salary" in update_data:
            can_view_salary_change = update_data.pop("can_view_salary")
        if "can_view_sensitive_pii" in update_data:
            can_view_sensitive_pii_change = update_data.pop("can_view_sensitive_pii")

        for field, value in update_data.items():
            setattr(user, field, value)
        user.updated_at = datetime.utcnow()

        # Sprint 5.5 + Sprint 8 RBAC: SYNC PII grants → users.* (auth SoT).
        # client_users doesn't store these fields; users.can_view_* is the canonical SoT.
        from sqlalchemy import text as _sa_text
        for grant_field, grant_value, audit_action, pii_class in [
            ("can_view_salary", can_view_salary_change, "pii_grant_change", "financial_salary"),
            ("can_view_sensitive_pii", can_view_sensitive_pii_change, "pii_grant_change", "sensitive_identity"),
        ]:
            if grant_value is None or not user.user_id:
                continue
            try:
                await repo.db.execute(
                    _sa_text(f"UPDATE users SET {grant_field} = :v WHERE id = :uid"),
                    {"v": bool(grant_value), "uid": str(user.user_id)},
                )
                # Audit log SOXAuditLog 7-year retention (LGPD Art. 37 V).
                from app.shared.compliance.audit_service import AuditService
                audit_svc = AuditService()
                actor_id = current_user.get("user_id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
                actor_email = current_user.get("email") if isinstance(current_user, dict) else getattr(current_user, "email", None)
                await audit_svc.log_user_provisioning(
                    company_id=client_id,
                    actor=str(actor_email or actor_id or "system"),
                    action=audit_action,
                    target_user_id=str(user.user_id),
                    target_user_email=user.email,
                    details={
                        "grant_field": grant_field,
                        "grant_new": bool(grant_value),
                        "pii_class": pii_class,
                    },
                )
            except HTTPException:
                raise
            except Exception as sync_exc:
                logger.warning(
                    "[client_users] can_view_salary sync to users failed (non-blocking): %s", sync_exc
                )

        # Sprint 2 RBAC (2026-05-25): SYNC client_users.department_id → users.department_id (auth table).
        # Filter logic em app/api/v1/job_vacancies/crud.py:list_job_vacancies usa users.department_id.
        # Sem sync, popular dept via UI cliente fica isolado e filter nunca ativa.
        # Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
        if "department_id" in update_data and user.user_id:
            from sqlalchemy import text
            try:
                await repo.db.execute(
                    text("UPDATE users SET department_id = :dept_id WHERE id = :uid"),
                    {"dept_id": update_data["department_id"], "uid": str(user.user_id)},
                )
            except Exception as sync_exc:
                # Non-blocking: sync failure não bloqueia client_user update.
                logger.warning(
                    "[client_users] dept sync to users failed (non-blocking): %s", sync_exc
                )

        await repo.log_audit(
            company_id=client_id,
            action="user_updated",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={"updated_fields": list(update_data.keys())},
        )

        await repo.commit()
        await repo.refresh(user)

        logger.info(f"Updated user: {user.id} (ID: {user.id})")

        return {
            "success": True,
            "message": "User updated successfully",
            "data": user.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error updating client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.delete("/{user_id}", summary="Delete user (soft delete)", response_model=None)
async def delete_client_user(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientUserRepository = Depends(get_client_user_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Soft delete a user from a client."""
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, repo)

        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format",
            )

        user = await repo.get_by_id(user_uuid, client_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.deleted_by = current_user.get("user_id", "system")
        user.updated_at = datetime.utcnow()

        await repo.log_audit(
            company_id=client_id,
            action="user_deleted",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={"user_id": str(user.id)},
        )

        await repo.commit()

        logger.info(f"Deleted user: {user.id} (ID: {user.id})")

        return {"success": True, "message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error deleting client user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )


@router.post("/{user_id}/resend-invite", summary="Resend invitation", response_model=None)
async def resend_invite(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientUserRepository = Depends(get_client_user_repo),
    email_svc: EmailService = Depends(get_email_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Resend invitation email to a pending user."""
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, repo)

        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format",
            )

        user = await repo.get_by_id(user_uuid, client_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        if user.status != ClientUserStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resend invitation to pending users",
            )

        token = user.generate_invitation_token()
        user.updated_at = datetime.utcnow()

        accept_url = f"{FRONTEND_URL}/aceitar-convite?token={token}"
        inviter_name = current_user.get("user_id", "Sistema")

        email_sent = False
        try:
            email_sent = await email_svc.send_invite_email(
                client_user=user,
                accept_url=accept_url,
                inviter_name=inviter_name,
                db=repo.db,
            )
        except Exception as e:
            logger.warning(f"Failed to send invitation email: {str(e)}")

        await repo.log_audit(
            company_id=client_id,
            action="invitation_resent",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={
                "new_token_generated": True,
                "invitation_expires_at": user.invitation_expires_at.isoformat() if user.invitation_expires_at else None,
                "email_sent": email_sent,
            },
        )

        await repo.commit()
        await repo.refresh(user)

        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Resent invitation to user: {user.id} (ID: {user.id}, email_sent: {email_sent})")

        return {
            "success": True,
            "message": "Invitation resent successfully" + (" and email sent" if email_sent else " (email pending)"),
            "data": user.to_dict(),
            "invitation_url": accept_url,
            "email_sent": email_sent,
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error resending invite: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend invitation: {str(e)}",
        )


@router.put("/{user_id}/role", summary="Update user role", response_model=None)
async def update_user_role(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ClientUserRoleUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientUserRepository = Depends(get_client_user_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update the role of a user."""
    try:
        validate_client_access(client_id, current_user)
        await verify_client_exists(client_id, repo)

        try:
            client_uuid = UUID(client_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format",
            )

        valid_roles = [r.value for r in ClientUserRole]
        if data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
            )

        user = await repo.get_by_id(user_uuid, client_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        old_role = user.role
        user.role = data.role
        user.updated_at = datetime.utcnow()

        await repo.log_audit(
            company_id=client_id,
            action="user_role_changed",
            user_email=user.email,
            performed_by=current_user.get("user_id", "system"),
            details={"old_role": old_role, "new_role": data.role},
        )

        await repo.commit()
        await repo.refresh(user)

        logger.info(f"Updated user role: {user.id} from {old_role} to {data.role}")

        return {
            "success": True,
            "message": f"User role updated from {old_role} to {data.role}",
            "data": user.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error updating user role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        )

reorder_collection_before_item(router)
