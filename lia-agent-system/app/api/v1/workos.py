"""
WorkOS SSO and SCIM integration endpoints.

Security: These endpoints are called by the Next.js frontend after it has validated
the WorkOS webhook signature. They are protected by an internal shared secret
to prevent direct unauthorized access.

The /webhooks/scim endpoint is the exception - it receives direct calls from WorkOS
and validates the WorkOS-Signature header directly.
"""
import hashlib
import hmac
import logging
import os
import time
import uuid as uuid_module
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.auth.models import UserRole
from app.auth.workos_schemas import (
    SCIMActionResponse,
    SCIMGroupAction,
    SCIMUserCreated,
    SCIMUserDeleted,
    SCIMUserUpdated,
    WorkOSSyncUser,
    WorkOSSyncUserResponse,
)
from app.auth.workos_schemas import SCIMGroupMembership as SCIMGroupMembershipSchema
from app.domains.auth.dependencies import get_user_repo, get_workos_repo
from app.domains.auth.repositories.user_repository import UserRepository
from app.domains.auth.repositories.workos_repository import WorkOSRepository
from app.shared.resilience.circuit_breaker import WORKOS_CIRCUIT, circuit_breaker_decorator
from app.shared.compliance.audit_service import AuditService
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)


class RoleMappingRequest(WeDoBaseModel):
    role: str
    permissions: list[str] | None = []

INTERNAL_API_SECRET = os.getenv("INTERNAL_API_SECRET", os.getenv("WORKOS_WEBHOOK_SECRET", ""))
WORKOS_WEBHOOK_SECRET = os.getenv("WORKOS_WEBHOOK_SECRET", "")


def verify_workos_webhook_signature(
    payload: bytes,
    sig_header: str,
    secret: str,
    tolerance: int = 180
) -> bool:
    """
    Verify WorkOS webhook signature using HMAC SHA256.

    Args:
        payload: Raw request body (bytes)
        sig_header: Value of WorkOS-Signature header (format: "t=timestamp,v1=signature")
        secret: Your webhook secret from WorkOS Dashboard
        tolerance: Maximum age of webhook in seconds (default 180 = 3 minutes)

    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not sig_header or not secret:
        return False

    parts = sig_header.split(',')
    timestamp = None
    signature = None

    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            if key == 't':
                timestamp = value
            elif key == 'v1':
                signature = value

    if not timestamp or not signature:
        logger.warning("WorkOS webhook signature header malformed")
        return False

    current_time = int(time.time())
    try:
        webhook_time = int(timestamp)
    except ValueError:
        logger.warning("WorkOS webhook timestamp invalid")
        return False

    if abs(current_time - webhook_time) > tolerance:
        logger.warning(f"WorkOS webhook timestamp out of tolerance: {abs(current_time - webhook_time)}s")
        return False

    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def verify_internal_auth(x_internal_auth: str = Header(None, alias="X-Internal-Auth")):
    """
    Verify internal authentication for WorkOS endpoints.
    These endpoints are called by the Next.js frontend after it validates WorkOS signatures.
    """
    if not INTERNAL_API_SECRET:
        env = os.getenv("ENVIRONMENT", "development")
        if env in ("production", "staging"):
            logger.error(
                "LIA-SEC-03 INTERNAL_API_SECRET not configured in %s — rejecting WorkOS endpoint call", env,
            )
            raise HTTPException(status_code=503, detail="Internal auth not configured")
        logger.warning("INTERNAL_API_SECRET not configured - WorkOS endpoints unprotected in development")
        return True

    if not x_internal_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing internal authentication header"
        )

    if not hmac.compare_digest(x_internal_auth, INTERNAL_API_SECRET):
        logger.warning("Invalid internal auth attempt on WorkOS endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal authentication"
        )

    return True


async def verify_scim_webhook(request: Request):
    """
    Verify WorkOS SCIM webhook signature using HMAC SHA256.

    This dependency:
    - Reads the WorkOS-Signature header from the request
    - Reads the raw request body for signature validation
    - Calls verify_workos_webhook_signature() to validate
    - Returns 401 if signature is invalid
    - In development (if secret not configured), logs warning but allows the request

    The raw body is cached by FastAPI/Starlette, so Pydantic can still parse it afterward.
    """
    if not WORKOS_WEBHOOK_SECRET:
        env = os.getenv("ENVIRONMENT", "development")
        if env in ("production", "staging"):
            logger.error(
                "LIA-SEC-03 WORKOS_WEBHOOK_SECRET not configured in %s — rejecting SCIM webhook", env,
            )
            raise HTTPException(status_code=503, detail="Webhook secret not configured")
        logger.warning("WORKOS_WEBHOOK_SECRET not configured - SCIM webhook signature validation disabled (development mode)")
        return True

    sig_header = request.headers.get("WorkOS-Signature")

    if not sig_header:
        logger.warning("SCIM webhook request missing WorkOS-Signature header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing WorkOS-Signature header"
        )

    raw_body = await request.body()

    if not verify_workos_webhook_signature(
        payload=raw_body,
        sig_header=sig_header,
        secret=WORKOS_WEBHOOK_SECRET
    ):
        logger.warning("SCIM webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    logger.debug("SCIM webhook signature verified successfully")
    return True


router = APIRouter(prefix="/workos", tags=["workos"], dependencies=[Depends(verify_internal_auth)])
scim_router = APIRouter(prefix="/workos", tags=["workos-scim"], dependencies=[Depends(verify_scim_webhook)])
auth_router = APIRouter(prefix="/auth/workos", tags=["workos-auth"], dependencies=[Depends(verify_internal_auth)])
webhook_router = APIRouter(prefix="/workos/webhooks", tags=["workos-webhooks"])
public_auth_router = APIRouter(prefix="/auth", tags=["auth-public"])


class CheckSSODomainResponse(BaseModel):
    sso_available: bool
    organization_id: str | None = None
    company_name: str | None = None


@public_auth_router.get("/check-sso-domain", response_model=CheckSSODomainResponse)
async def check_sso_domain(
    email: str = Query(..., description="Email address to check for SSO availability"),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
company_id: str = Depends(require_company_id)):
    """
    Check if an email domain has SSO configured.
    This is a public endpoint called from the login page before authentication.

    Logic:
    1. Extract domain from email (part after @)
    2. Check CompanyWorkOSConfig.sso_domains array for matching domain
    3. If not found, fall back to checking client_accounts by primary_email domain
    4. Return SSO availability and organization_id if enabled
    """
    if not email or '@' not in email:
        return CheckSSODomainResponse(sso_available=False)

    domain = email.split('@')[1].lower()

    config = await workos_repo.get_config_by_sso_domain(domain)

    if config:
        client = None
        try:
            company_uuid = uuid_module.UUID(config.company_id)
            client = await workos_repo.get_client_by_id(company_uuid)
        except (ValueError, TypeError):
            logger.warning(f"Invalid company_id format in CompanyWorkOSConfig: {config.company_id}")

        return CheckSSODomainResponse(
            sso_available=True,
            organization_id=config.workos_organization_id,
            company_name=client.name if client else None
        )

    client = await workos_repo.get_client_by_email_domain(domain)

    if client:
        config = await workos_repo.get_config_for_client(str(client.id), sso_required=True)

        if config:
            return CheckSSODomainResponse(
                sso_available=True,
                organization_id=config.workos_organization_id,
                company_name=client.name
            )

    return CheckSSODomainResponse(sso_available=False)


@auth_router.post("/sync-user", response_model=WorkOSSyncUserResponse)
@circuit_breaker_decorator(WORKOS_CIRCUIT)
async def sync_workos_user(
    user_data: WorkOSSyncUser,
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
company_id: str = Depends(require_company_id)):
    """
    Sync a user from WorkOS SSO.
    Called after successful SSO authentication to ensure user exists in our database.
    Creates new user if not exists, updates if exists.
    """
    user = await user_repo.get_by_workos_id(user_data.workos_id)

    is_new_user = False
    name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip() or user_data.email.split('@')[0]

    if not user:
        user = await user_repo.get_by_email(user_data.email)

        if user:
            user = await user_repo.update_by_instance(user, {
                "workos_id": user_data.workos_id,
                "workos_organization_id": user_data.organization_id,
                "sso_provider": user_data.connection_type,
                "last_sso_login_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.info(f"Linked existing user (email={user_data.email}) to WorkOS ID {user_data.workos_id}")
        else:
            user = await user_repo.create({
                "email": user_data.email,
                "name": name,
                "workos_id": user_data.workos_id,
                "workos_organization_id": user_data.organization_id,
                "sso_provider": user_data.connection_type,
                "role": UserRole.viewer,
                "is_active": True,
                "email_verified": True,
                "last_sso_login_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            is_new_user = True
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.info(f"Created new SSO user: workos_id={user_data.workos_id}, email={user_data.email}")
    else:
        update_data = {
            "last_sso_login_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        if user_data.organization_id:
            update_data["workos_organization_id"] = user_data.organization_id
        user = await user_repo.update_by_instance(user, update_data)
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"SSO login for existing user: workos_id={user_data.workos_id}, email={user_data.email}")

    await workos_repo.log_sso_event({
        "company_id": user_data.organization_id or None,
        "event_type": "sso.login",
        "actor_id": str(user.id),
        "actor_email": user.email,
        "target_id": user_data.workos_id,
        "target_email": user.email,
        "payload": {
            "is_new_user": is_new_user,
            "connection_type": user_data.connection_type,
            "workos_id": user_data.workos_id
        }
    })

    return WorkOSSyncUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        workos_id=user.workos_id,
        is_new_user=is_new_user,
        sso_provider=user.sso_provider
    )


@scim_router.post("/users/created", response_model=SCIMActionResponse)
@circuit_breaker_decorator(WORKOS_CIRCUIT)
async def scim_user_created(
    user_data: SCIMUserCreated,
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
company_id: str = Depends(require_company_id)):
    """
    Handle SCIM dsync.user.created event.
    Auto-provisions a new user from the corporate directory.

    Flow:
    1. Validate email is provided
    2. Check if user already exists by workos_id
    3. Check if user already exists by email (link existing user)
    4. Look up CompanyWorkOSConfig by directory_id to get company_id
    5. Create new user with company association
    6. Log audit event
    """
    if not user_data.email:
        logger.warning(f"SCIM user.created without email: {user_data.workos_id}")
        return SCIMActionResponse(
            success=False,
            action="created",
            workos_id=user_data.workos_id,
            message="Email required for user provisioning"
        )

    existing = await user_repo.get_by_workos_id(user_data.workos_id)

    if existing:
        logger.info(f"SCIM user already exists: {user_data.workos_id}")
        return SCIMActionResponse(
            success=True,
            action="created",
            workos_id=user_data.workos_id,
            message="User already exists"
        )

    company_config = None
    company_id = None
    if user_data.directory_id:
        company_config = await workos_repo.get_config_by_directory(user_data.directory_id)
        if company_config:
            company_id = company_config.company_id
            logger.info(f"SCIM user.created: Found company config for directory {user_data.directory_id} -> company_id={company_id}")
        else:
            logger.warning(f"SCIM user.created: No CompanyWorkOSConfig found for directory_id={user_data.directory_id}")

    existing_by_email = await user_repo.get_by_email(user_data.email)

    if existing_by_email:
        # ── Wave 4 audit 2026-05-22: cross-tenant SCIM email collision ────
        # Pre-fix, this branch silently overwrote workos_directory_id +
        # is_scim_managed for a user that already belonged to tenant A
        # when tenant B's SCIM provisioned the same email. Net effect:
        # tenant B's IdP could hijack tenant A's user record (and any
        # subsequent SSO login would route the original tenant-A user to
        # tenant B's directory).
        #
        # Policy = REJECT (conservative default). Cross-tenant merges go
        # through ops manually (admin@wedotalent.cc) after both tenants
        # consent in writing — never automatic from SCIM.
        if (
            existing_by_email.company_id
            and company_id
            and existing_by_email.company_id != company_id
        ):
            # NEVER log the email in plaintext (LGPD). The audit log entry
            # records the event with hashed email; the response message
            # generic.
            try:
                import hashlib as _hashlib
                _email_hash = _hashlib.sha256(
                    user_data.email.lower().strip().encode("utf-8")
                ).hexdigest()[:16]
            except Exception:
                _email_hash = "hash-failed"

            logger.warning(
                "SCIM email collision rejected (cross-tenant): "
                "email_hash=%s existing_tenant=%s scim_tenant=%s",
                _email_hash,
                existing_by_email.company_id,
                company_id,
            )

            await workos_repo.log_sso_event({
                "company_id": company_id,
                "event_type": "scim.user.collision_rejected",
                "actor_id": user_data.workos_id,
                "actor_email": user_data.email,
                "target_id": str(existing_by_email.id),
                "target_email": user_data.email,
                "payload": {
                    "workos_id": user_data.workos_id,
                    "directory_id": user_data.directory_id,
                    "scim_tenant": company_id,
                    "existing_tenant": existing_by_email.company_id,
                    "action": "rejected_cross_tenant_collision",
                    "email_hash_prefix": _email_hash,
                },
            })

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Email already provisioned in another tenant. "
                    "Contact admin@wedotalent.cc for cross-tenant user merge."
                ),
            )

        # Same-tenant OR existing user has no tenant yet (legacy unassigned):
        # safe to link.
        update_data = {
            "workos_id": user_data.workos_id,
            "workos_directory_id": user_data.directory_id,
            "is_scim_managed": True,
            "updated_at": datetime.utcnow(),
        }
        if company_id and not existing_by_email.company_id:
            update_data["company_id"] = company_id
        await user_repo.update_by_instance(existing_by_email, update_data)

        await workos_repo.log_sso_event({
            "company_id": company_id or user_data.directory_id or None,
            "event_type": "scim.user.linked",
            "actor_id": user_data.workos_id,
            "actor_email": user_data.email,
            "target_id": str(existing_by_email.id),
            "target_email": user_data.email,
            "payload": {
                "workos_id": user_data.workos_id,
                "directory_id": user_data.directory_id,
                "company_id": company_id,
                "action": "linked_existing_user"
            }
        })

        logger.info(f"SCIM linked existing user (workos_id={user_data.workos_id}) to directory (company_id={company_id})")
        return SCIMActionResponse(
            success=True,
            action="created",
            workos_id=user_data.workos_id,
            message="Linked existing user to SCIM"
        )

    name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip() or user_data.email.split('@')[0]

    user = await user_repo.create({
        "email": user_data.email,
        "name": name,
        "workos_id": user_data.workos_id,
        "workos_directory_id": user_data.directory_id,
        "company_id": company_id,
        "is_scim_managed": True,
        "role": UserRole.viewer,
        "is_active": True,
        "email_verified": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    await workos_repo.log_sso_event({
        "company_id": company_id or user_data.directory_id or None,
        "event_type": "scim.user.created",
        "actor_id": user_data.workos_id,
        "actor_email": user_data.email,
        "target_id": str(user.id),
        "target_email": user_data.email,
        "payload": {
            "workos_id": user_data.workos_id,
            "directory_id": user_data.directory_id,
            "company_id": company_id,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "state": user_data.state
        }
    })

    logger.info(f"SCIM provisioned new user: workos_id={user_data.workos_id} (company_id={company_id})")
    return SCIMActionResponse(
        success=True,
        action="created",
        workos_id=user_data.workos_id,
        message="User provisioned successfully"
    )


@scim_router.post("/users/updated", response_model=SCIMActionResponse)
async def scim_user_updated(
    user_data: SCIMUserUpdated,
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
company_id: str = Depends(require_company_id)):
    """
    Handle SCIM dsync.user.updated event.
    Updates user information from corporate directory.
    """
    user = await user_repo.get_by_workos_id(user_data.workos_id)

    if not user:
        logger.warning(f"SCIM user.updated for unknown user: {user_data.workos_id}")
        return SCIMActionResponse(
            success=False,
            action="updated",
            workos_id=user_data.workos_id,
            message="User not found"
        )

    update_data: dict = {"updated_at": datetime.utcnow()}

    if user_data.first_name or user_data.last_name:
        name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip()
        if name:
            update_data["name"] = name

    if user_data.email and user_data.email != user.email:
        update_data["email"] = user_data.email

    if user_data.state:
        update_data["is_active"] = user_data.state != "suspended"

    await user_repo.update_by_instance(user, update_data)

    await workos_repo.log_sso_event({
        "company_id": user.workos_directory_id or user.workos_organization_id or None,
        "event_type": "scim.user.updated",
        "actor_id": user_data.workos_id,
        "actor_email": user.email,
        "target_id": str(user.id),
        "target_email": user.email,
        "payload": {
            "workos_id": user_data.workos_id,
            "state": user_data.state,
            "email_updated": user_data.email != user.email if user_data.email else False
        }
    })

    logger.info(f"SCIM updated user: {user_data.workos_id}")
    return SCIMActionResponse(
        success=True,
        action="updated",
        workos_id=user_data.workos_id,
        message="User updated successfully"
    )


@scim_router.post("/users/deleted", response_model=SCIMActionResponse)
async def scim_user_deleted(
    user_data: SCIMUserDeleted,
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
company_id: str = Depends(require_company_id)):
    """
    Handle SCIM dsync.user.deleted event.
    Deactivates user (soft delete) - does not remove data for compliance.
    """
    user = await user_repo.get_by_workos_id(user_data.workos_id)

    if not user:
        logger.warning(f"SCIM user.deleted for unknown user: {user_data.workos_id}")
        return SCIMActionResponse(
            success=False,
            action="deleted",
            workos_id=user_data.workos_id,
            message="User not found"
        )

    await user_repo.update_by_instance(user, {
        "is_active": False,
        "updated_at": datetime.utcnow(),
    })

    await workos_repo.log_sso_event({
        "company_id": user.workos_directory_id or user.workos_organization_id or None,
        "event_type": "scim.user.deleted",
        "actor_id": user_data.workos_id,
        "actor_email": user.email,
        "target_id": str(user.id),
        "target_email": user.email,
        "payload": {
            "workos_id": user_data.workos_id,
            "user_id": str(user.id)
        }
    })

    logger.info(f"SCIM deactivated user: {user_data.workos_id}")
    return SCIMActionResponse(
        success=True,
        action="deleted",
        workos_id=user_data.workos_id,
        message="User deactivated successfully"
    )


@scim_router.post("/groups/{action}", response_model=SCIMActionResponse)
async def scim_group_action(
    action: str,
    group_data: SCIMGroupAction,
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
company_id: str = Depends(require_company_id)):
    """
    Handle SCIM group events (created, updated, deleted).
    Persists groups to the database and logs audit events.
    """
    if action not in ["created", "updated", "deleted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be created, updated, or deleted."
        )

    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"SCIM group.{action}: {group_data.workos_id} ({group_data.name})")

    if action == "created":
        await workos_repo.upsert_group(
            workos_id=group_data.workos_id,
            directory_id=group_data.directory_id or "",
            name=group_data.name or "Unknown Group",
            is_active=True,
        )
        message = "Group created/updated successfully"

    elif action == "updated":
        group = await workos_repo.get_group_by_workos_id(group_data.workos_id)
        if not group:
            logger.warning(f"SCIM group.updated for unknown group: {group_data.workos_id}")
            return SCIMActionResponse(
                success=False,
                action=action,
                workos_id=group_data.workos_id,
                message="Group not found"
            )
        update_data = {}
        if group_data.name:
            update_data["name"] = group_data.name
        if group_data.directory_id:
            update_data["directory_id"] = group_data.directory_id
        await workos_repo.update_group(group_data.workos_id, update_data)
        message = "Group updated successfully"

    elif action == "deleted":
        group = await workos_repo.deactivate_group(group_data.workos_id)
        if not group:
            logger.warning(f"SCIM group.deleted for unknown group: {group_data.workos_id}")
            return SCIMActionResponse(
                success=False,
                action=action,
                workos_id=group_data.workos_id,
                message="Group not found"
            )
        message = "Group deactivated successfully"

    await workos_repo.log_sso_event({
        "company_id": group_data.directory_id or None,
        "event_type": f"scim.group.{action}",
        "actor_id": group_data.workos_id,
        "target_id": group_data.workos_id,
        "payload": {
            "workos_id": group_data.workos_id,
            "name": group_data.name,
            "directory_id": group_data.directory_id
        }
    })

    return SCIMActionResponse(
        success=True,
        action=action,
        workos_id=group_data.workos_id,
        message=message
    )


@scim_router.post("/group-membership", response_model=SCIMActionResponse)
async def scim_group_membership(
    membership_data: SCIMGroupMembershipSchema,
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
company_id: str = Depends(require_company_id)):
    """
    Handle SCIM group membership events.
    Persists memberships to the database and logs audit events.
    """
    logger.info(f"SCIM membership.{membership_data.action}: user={membership_data.user_id} group={membership_data.group_id}")

    user = await user_repo.get_by_workos_id(membership_data.user_id)

    if not user:
        logger.warning(f"User {membership_data.user_id} not found for membership event")
        return SCIMActionResponse(
            success=False,
            action=f"membership_{membership_data.action}",
            workos_id=membership_data.user_id,
            message="User not found"
        )

    group = await workos_repo.get_group_by_workos_id(membership_data.group_id)

    if not group:
        logger.warning(f"Group {membership_data.group_id} not found for membership event")
        return SCIMActionResponse(
            success=False,
            action=f"membership_{membership_data.action}",
            workos_id=membership_data.group_id,
            message="Group not found"
        )

    if membership_data.action == "added":
        existing = await workos_repo.get_membership(group.id, user.id)
        if existing:
            message = "Membership already exists"
        else:
            await workos_repo.add_membership(group.id, user.id, added_by="scim")
            message = "User added to group"

    elif membership_data.action == "removed":
        removed = await workos_repo.remove_membership(group.id, user.id)
        message = "User removed from group" if removed else "Membership not found"

    else:
        message = f"Unknown membership action: {membership_data.action}"

    await workos_repo.log_sso_event({
        "company_id": group.directory_id or user.workos_directory_id or None,
        "event_type": f"scim.group.user_{membership_data.action}",
        "actor_id": membership_data.user_id,
        "actor_email": user.email,
        "target_id": membership_data.group_id,
        "payload": {
            "user_workos_id": membership_data.user_id,
            "group_workos_id": membership_data.group_id,
            "user_id": str(user.id),
            "group_id": str(group.id),
            "group_name": group.name
        }
    })

    return SCIMActionResponse(
        success=True,
        action=f"membership_{membership_data.action}",
        workos_id=membership_data.user_id,
        message=message
    )


@router.get("/admin/status", response_model=None)
async def get_sso_status(
    company_id: str = Query(...),
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get SSO/SCIM configuration status for a company.

    Tenant Isolation: Only counts groups from the company's configured directory.
    """
    config = await workos_repo.get_config(company_id)

    scim_users_count = await user_repo.count_for_company(company_id, scim_only=True)
    sso_users_count = await user_repo.count_for_company(company_id, workos_only=True)

    groups_count = 0
    if config and config.workos_directory_id:
        groups_count = await workos_repo.count_groups(config.workos_directory_id)

    recent_events_count = await workos_repo.count_recent_events(
        company_id,
        since=datetime.utcnow() - timedelta(days=7)
    )

    return {
        "company_id": company_id,
        "sso_enabled": sso_users_count > 0,
        "scim_enabled": scim_users_count > 0,
        "sso_users_count": sso_users_count,
        "scim_users_count": scim_users_count,
        "groups_count": groups_count,
        "recent_events_count": recent_events_count
    }


@circuit_breaker_decorator(WORKOS_CIRCUIT)
async def _fetch_workos_metrics(workos_api_key: str, organization_id: str, local_data: dict[str, Any]) -> dict[str, Any]:
    """Fetch real-time metrics from WorkOS API, protected by circuit breaker."""
    import httpx
    async with httpx.AsyncClient(timeout=5.0) as client:
        headers = {"Authorization": f"Bearer {workos_api_key}"}

        dirs_response = await client.get(
            "https://api.workos.com/directory_sync/directories",
            headers=headers,
            params={"organization_id": organization_id}
        )
        directories = dirs_response.json().get("data", []) if dirs_response.status_code == 200 else []

        conns_response = await client.get(
            "https://api.workos.com/sso/connections",
            headers=headers,
            params={"organization_id": organization_id}
        )
        connections = conns_response.json().get("data", []) if conns_response.status_code == 200 else []

        return {
            "source": "workos_api",
            "organization_id": organization_id,
            "sso_users_count": local_data["sso_users_count"],
            "scim_users_count": local_data["scim_users_count"],
            "groups_count": local_data["groups_count"],
            "directories_count": len(directories),
            "connections_count": len(connections),
        }


@router.get("/admin/realtime-metrics", response_model=None)
async def get_realtime_metrics(
    company_id: str = Query(...),
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Fetch real-time metrics directly from WorkOS API.
    Falls back to local database if WorkOS API is unavailable.
    """
    workos_api_key = os.getenv("WORKOS_API_KEY")

    local_data: dict[str, Any] = {
        "source": "local",
        "sso_users_count": 0,
        "scim_users_count": 0,
        "groups_count": 0,
        "directories_count": 0,
        "connections_count": 0,
    }
    config = None

    try:
        local_data["sso_users_count"] = await user_repo.count_for_company(company_id, workos_only=True)
        local_data["scim_users_count"] = await user_repo.count_for_company(company_id, scim_only=True)

        config = await workos_repo.get_config(company_id)

        if config and config.workos_directory_id:
            local_data["groups_count"] = await workos_repo.count_groups(config.workos_directory_id)
    except Exception as e:
        logger.warning(f"Error getting local metrics: {e}")

    if not workos_api_key:
        return local_data

    organization_id = config.workos_organization_id if config else None

    if not organization_id:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"No WorkOS organization_id configured for company {company_id}")
        return local_data

    try:
        return await _fetch_workos_metrics(workos_api_key, organization_id, local_data)
    except Exception as e:
        logger.warning(f"Error fetching WorkOS API metrics: {e}")
        return local_data


@router.get("/admin/groups", response_model=None)
async def get_groups(
    company_id: str = Query(...),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get WorkOS groups for a company with role mappings.

    Tenant Isolation: Validates that the company has access to the directory
    before returning any groups.
    """
    config = await workos_repo.get_config(company_id)

    if not config or not config.workos_directory_id:
        return []

    groups = await workos_repo.list_groups(config.workos_directory_id)
    mappings = await workos_repo.list_role_mappings(company_id)
    mappings_dict = {str(m.workos_group_id): m for m in mappings}

    groups_response = []
    for group in groups:
        mapped_role = None
        mapped_permissions = []
        mapping = mappings_dict.get(str(group.id))
        if mapping:
            mapped_role = mapping.role
            mapped_permissions = mapping.permissions or []

        groups_response.append({
            "id": str(group.id),
            "workos_id": group.workos_id,
            "name": group.name,
            "directory_id": group.directory_id,
            "mapped_role": mapped_role,
            "mapped_permissions": mapped_permissions
        })

    return groups_response


@router.post("/admin/groups/{group_id}/role-mapping", response_model=None)
async def set_group_role_mapping(
    group_id: str,
    mapping: RoleMappingRequest,
    company_id: str = Query(...),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Set role mapping for a WorkOS group.

    Tenant Isolation: Validates that the group belongs to the company's directory.
    """
    config = await workos_repo.get_config(company_id)

    if not config or not config.workos_directory_id:
        raise HTTPException(
            status_code=403,
            detail="Company has no configured WorkOS directory"
        )

    group = await workos_repo.get_group_by_id(uuid_module.UUID(group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.directory_id != config.workos_directory_id:
        raise HTTPException(
            status_code=403,
            detail="Group does not belong to your directory"
        )

    await workos_repo.upsert_role_mapping(
        company_id=company_id,
        workos_group_id=uuid_module.UUID(group_id),
        role=mapping.role,
        permissions=mapping.permissions or [],
    )

    return {"success": True, "group_id": group_id, "role": mapping.role}


@router.get("/admin/audit-logs", response_model=None)
async def get_audit_logs(
    company_id: str = Query(...),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    event_type: str | None = Query(default=None),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get SSO/SCIM audit logs for a company.

    Note: For full audit log access with advanced filtering and export,
    use WorkOS Dashboard at https://dashboard.workos.com/events.
    This endpoint provides local backup logs for compliance requirements.
    """
    logs = await workos_repo.list_audit_logs(
        company_id=company_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )

    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "actor_id": log.actor_id,
            "actor_email": log.actor_email,
            "target_id": log.target_id,
            "target_email": log.target_email,
            "source_ip": log.source_ip,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]


@router.get("/admin/users", response_model=None)
async def get_sso_users(
    company_id: str = Query(...),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    scim_only: bool = Query(default=False),
    user_repo: UserRepository = Depends(get_user_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get SSO/SCIM managed users for a company.

    Note: For full user management and provisioning,
    use WorkOS Dashboard at https://dashboard.workos.com/users.
    This endpoint provides read-only access to synced user data.
    """
    users = await user_repo.list_for_company(
        company_id=company_id,
        workos_only=True,
        scim_only=scim_only,
        limit=limit,
        offset=offset,
    )

    return [
        {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value if user.role else None,
            "workos_id": user.workos_id,
            "sso_provider": user.sso_provider,
            "is_scim_managed": user.is_scim_managed,
            "is_active": user.is_active,
            "last_sso_login_at": user.last_sso_login_at.isoformat() if user.last_sso_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in users
    ]


async def _get_company_id_from_directory(directory_id: str, workos_repo: WorkOSRepository) -> str | None:
    """
    Lookup company_id from directory_id via company_workos_config table.
    Returns None if not found.
    """
    if not directory_id:
        return None
    config = await workos_repo.get_config_by_directory(directory_id)
    return config.company_id if config else None



# ---------------------------------------------------------------------------
# Sprint 4 RBAC canonical — role mapping & audit helpers
# ---------------------------------------------------------------------------
_ROLE_HIERARCHY = {
    "admin": 4,
    "manager": 3,
    "recruiter": 2,
    "viewer": 1,
}


async def _recompute_user_role_from_groups(
    user,
    company_id: str,
    user_repo: UserRepository,
    workos_repo: WorkOSRepository,
) -> tuple[str, str | None]:
    """Re-compute user.role based on highest privileged WorkOS group mapping.

    Sprint 4 RBAC (2026-05-25, plan canonical: jolly-roaming-moler.md). Called
    after dsync.group.user_added/removed events.

    Logic:
      - List user's WorkOS groups
      - For each group, lookup WorkOSGroupRoleMapping (admin WeDOTalent configures)
      - Pick HIGHEST role per _ROLE_HIERARCHY (admin > manager > recruiter > viewer)
      - If no group has mapping → default viewer
      - Update users.role + commit

    Returns (new_role, old_role) — old_role can be None if no change applied.
    """
    groups = await workos_repo.list_groups_for_user(user.id)
    candidate_role = "viewer"
    best_rank = 0
    for g in groups:
        mapping = await workos_repo.get_role_mapping(company_id, g.id)
        if not mapping:
            continue
        rank = _ROLE_HIERARCHY.get(mapping.role, 0)
        if rank > best_rank:
            best_rank = rank
            candidate_role = mapping.role

    old_role = getattr(user, "role", None)
    old_role_str = old_role.value if hasattr(old_role, "value") else str(old_role) if old_role else None
    if old_role_str == candidate_role:
        return candidate_role, None  # no change

    # Need UserRole enum to assign
    from app.auth.models import UserRole
    try:
        new_role_enum = UserRole(candidate_role)
    except ValueError:
        # Defensive: invalid mapping role → fallback viewer
        new_role_enum = UserRole.viewer
        candidate_role = "viewer"

    await user_repo.update_by_instance(user, {"role": new_role_enum})
    return candidate_role, old_role_str


_audit_service = AuditService()


async def _handle_dsync_user_created(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    user_repo: UserRepository,
) -> dict[str, Any]:
    """Handle dsync.user.created event."""
    workos_id = data.get("id")
    email = data.get("emails", [{}])[0].get("value") if data.get("emails") else None
    first_name = data.get("first_name") or data.get("name", {}).get("given_name")
    last_name = data.get("last_name") or data.get("name", {}).get("family_name")
    state = data.get("state", "active")

    if not email:
        logger.warning(f"dsync.user.created without email: {workos_id}")
        return {"success": False, "message": "Email required for user provisioning"}

    existing = await user_repo.get_by_workos_id(workos_id)
    if existing:
        logger.info(f"SCIM user already exists: {workos_id}")
        return {"success": True, "message": "User already exists"}

    existing_by_email = await user_repo.get_by_email(email)
    if existing_by_email:
        await user_repo.update_by_instance(existing_by_email, {
            "workos_id": workos_id,
            "workos_directory_id": directory_id,
            "is_scim_managed": True,
            "company_id": company_id,
            "updated_at": datetime.utcnow(),
        })
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"SCIM linked existing user {email} to directory")
        return {"success": True, "message": "Linked existing user to SCIM", "user_id": str(existing_by_email.id)}

    name = f"{first_name or ''} {last_name or ''}".strip() or email.split('@')[0]

    user = await user_repo.create({
        "email": email,
        "name": name,
        "workos_id": workos_id,
        "workos_directory_id": directory_id,
        "company_id": company_id,
        "is_scim_managed": True,
        "role": UserRole.viewer,
        "is_active": state != "suspended",
        "email_verified": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
    logger.info(f"SCIM provisioned new user: {email}")
    # Sprint 4 RBAC audit: user provisioning event, 7-year SOX/LGPD retention
    await _audit_service.log_user_provisioning(
        company_id=company_id,
        actor="scim_webhook",
        action="provision_user",
        target_user_id=str(user.id),
        target_user_email=email,
        details={
            "workos_id": workos_id,
            "directory_id": directory_id,
            "event_id": event_id,
            "initial_role": "viewer",
            "is_scim_managed": True,
        },
    )
    return {"success": True, "message": "User provisioned successfully", "user_id": str(user.id)}


async def _handle_dsync_user_updated(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    user_repo: UserRepository,
) -> dict[str, Any]:
    """Handle dsync.user.updated event."""
    workos_id = data.get("id")
    email = data.get("emails", [{}])[0].get("value") if data.get("emails") else None
    first_name = data.get("first_name") or data.get("name", {}).get("given_name")
    last_name = data.get("last_name") or data.get("name", {}).get("family_name")
    state = data.get("state")

    user = await user_repo.get_by_workos_id(workos_id)

    if not user:
        logger.warning(f"dsync.user.updated for unknown user: {workos_id}")
        return {"success": False, "message": "User not found"}

    update_data: dict = {"updated_at": datetime.utcnow()}

    if first_name or last_name:
        name = f"{first_name or ''} {last_name or ''}".strip()
        if name:
            update_data["name"] = name

    if email and email != user.email:
        update_data["email"] = email

    if state:
        update_data["is_active"] = state != "suspended"

    await user_repo.update_by_instance(user, update_data)

    logger.info(f"SCIM updated user: {workos_id}")
    await _audit_service.log_user_provisioning(
        company_id=company_id,
        actor="scim_webhook",
        action="update_user",
        target_user_id=str(user.id),
        target_user_email=getattr(user, "email", None),
        details={
            "workos_id": workos_id,
            "directory_id": directory_id,
            "event_id": event_id,
            "fields_updated": list(update_data.keys()),
        },
    )
    return {"success": True, "message": "User updated successfully", "user_id": str(user.id)}


async def _handle_dsync_user_deleted(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    user_repo: UserRepository,
) -> dict[str, Any]:
    """Handle dsync.user.deleted event - soft delete (deactivate)."""
    workos_id = data.get("id")

    user = await user_repo.get_by_workos_id(workos_id)

    if not user:
        logger.warning(f"dsync.user.deleted for unknown user: {workos_id}")
        return {"success": False, "message": "User not found"}

    await user_repo.update_by_instance(user, {
        "is_active": False,
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"SCIM deactivated user: {workos_id}")
    await _audit_service.log_user_provisioning(
        company_id=company_id,
        actor="scim_webhook",
        action="deactivate_user",
        target_user_id=str(user.id),
        target_user_email=getattr(user, "email", None),
        details={
            "workos_id": workos_id,
            "directory_id": directory_id,
            "event_id": event_id,
        },
    )
    return {"success": True, "message": "User deactivated successfully", "user_id": str(user.id)}


async def _handle_dsync_group_created(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    workos_repo: WorkOSRepository,
) -> dict[str, Any]:
    """Handle dsync.group.created event."""
    workos_id = data.get("id")
    name = data.get("name") or "Unknown Group"
    raw_attributes = data.get("raw_attributes", {})

    group = await workos_repo.upsert_group(
        workos_id=workos_id,
        directory_id=directory_id,
        name=name,
        raw_attributes=raw_attributes,
        is_active=True,
    )
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"SCIM created/updated group: {workos_id} ({name})")
    return {"success": True, "message": "Group created/updated", "group_id": str(group.id)}


async def _handle_dsync_group_updated(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    workos_repo: WorkOSRepository,
) -> dict[str, Any]:
    """Handle dsync.group.updated event."""
    workos_id = data.get("id")
    name = data.get("name")
    raw_attributes = data.get("raw_attributes", {})

    group = await workos_repo.get_group_by_workos_id(workos_id)

    if not group:
        logger.warning(f"dsync.group.updated for unknown group: {workos_id}")
        return {"success": False, "message": "Group not found"}

    update_data = {}
    if name:
        update_data["name"] = name
    if directory_id:
        update_data["directory_id"] = directory_id
    if raw_attributes:
        update_data["raw_attributes"] = raw_attributes

    await workos_repo.update_group(workos_id, update_data)

    logger.info(f"SCIM updated group: {workos_id}")
    return {"success": True, "message": "Group updated successfully", "group_id": str(group.id)}


async def _handle_dsync_group_deleted(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    workos_repo: WorkOSRepository,
) -> dict[str, Any]:
    """Handle dsync.group.deleted event - mark as inactive."""
    workos_id = data.get("id")

    group = await workos_repo.deactivate_group(workos_id)

    if not group:
        logger.warning(f"dsync.group.deleted for unknown group: {workos_id}")
        return {"success": False, "message": "Group not found"}

    logger.info(f"SCIM deactivated group: {workos_id}")
    return {"success": True, "message": "Group deactivated successfully", "group_id": str(group.id)}


async def _handle_dsync_group_user_added(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    user_repo: UserRepository,
    workos_repo: WorkOSRepository,
) -> dict[str, Any]:
    """Handle dsync.group.user_added event - add membership."""
    group_data = data.get("group", {})
    user_data_inner = data.get("user", {})
    group_workos_id = group_data.get("id")
    user_workos_id = user_data_inner.get("id")

    user = await user_repo.get_by_workos_id(user_workos_id)
    if not user:
        logger.warning(f"dsync.group.user_added for unknown user: {user_workos_id}")
        return {"success": False, "message": "User not found"}

    group = await workos_repo.get_group_by_workos_id(group_workos_id)
    if not group:
        logger.warning(f"dsync.group.user_added for unknown group: {group_workos_id}")
        return {"success": False, "message": "Group not found"}

    existing = await workos_repo.get_membership(group.id, user.id)
    if existing:
        logger.info(f"SCIM membership already exists: user={user_workos_id} group={group_workos_id}")
        return {"success": True, "message": "Membership already exists"}

    membership = await workos_repo.add_membership(group.id, user.id, added_by="scim_webhook")
    logger.info(f"SCIM added user {user_workos_id} to group {group_workos_id}")

    # Sprint 4 RBAC: recompute user.role from group mappings (admin WeDOTalent configures)
    new_role, old_role = await _recompute_user_role_from_groups(
        user, company_id, user_repo, workos_repo,
    )
    role_changed = old_role is not None and old_role != new_role

    # Sprint 4 audit: USER_MANAGEMENT event, 7-year retention (LGPD Art. 37 V + SOX 802)
    await _audit_service.log_user_provisioning(
        company_id=company_id,
        actor="scim_webhook",
        action="group_add" if not role_changed else "role_change",
        target_user_id=str(user.id),
        target_user_email=getattr(user, "email", None),
        details={
            "workos_id": user_workos_id,
            "group_workos_id": group_workos_id,
            "group_name": getattr(group, "name", None),
            "role_old": old_role,
            "role_new": new_role,
            "directory_id": directory_id,
            "event_id": event_id,
        },
    )
    return {"success": True, "message": "User added to group", "membership_id": str(membership.id)}


async def _handle_dsync_group_user_removed(
    data: dict[str, Any],
    directory_id: str,
    company_id: str,
    event_id: str,
    user_repo: UserRepository,
    workos_repo: WorkOSRepository,
) -> dict[str, Any]:
    """Handle dsync.group.user_removed event - remove membership."""
    group_data = data.get("group", {})
    user_data_inner = data.get("user", {})
    group_workos_id = group_data.get("id")
    user_workos_id = user_data_inner.get("id")

    user = await user_repo.get_by_workos_id(user_workos_id)
    if not user:
        logger.warning(f"dsync.group.user_removed for unknown user: {user_workos_id}")
        return {"success": False, "message": "User not found"}

    group = await workos_repo.get_group_by_workos_id(group_workos_id)
    if not group:
        logger.warning(f"dsync.group.user_removed for unknown group: {group_workos_id}")
        return {"success": False, "message": "Group not found"}

    removed = await workos_repo.remove_membership(group.id, user.id)
    if removed:
        logger.info(f"SCIM removed user {user_workos_id} from group {group_workos_id}")
        # Sprint 4 RBAC: recompute user.role (might downgrade if highest-priv group was removed)
        new_role, old_role = await _recompute_user_role_from_groups(
            user, company_id, user_repo, workos_repo,
        )
        role_changed = old_role is not None and old_role != new_role
        await _audit_service.log_user_provisioning(
            company_id=company_id,
            actor="scim_webhook",
            action="group_remove" if not role_changed else "role_change",
            target_user_id=str(user.id),
            target_user_email=getattr(user, "email", None),
            details={
                "workos_id": user_workos_id,
                "group_workos_id": group_workos_id,
                "group_name": getattr(group, "name", None),
                "role_old": old_role,
                "role_new": new_role,
                "directory_id": directory_id,
                "event_id": event_id,
            },
        )
        return {"success": True, "message": "User removed from group"}
    else:
        logger.info(f"SCIM membership not found: user={user_workos_id} group={group_workos_id}")
        return {"success": True, "message": "Membership not found"}


@webhook_router.post("/scim")
async def scim_webhook(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repo),
    workos_repo: WorkOSRepository = Depends(get_workos_repo),
):
    """
    Main webhook endpoint to receive SCIM events from WorkOS.

    This endpoint:
    1. Validates the WorkOS-Signature header
    2. Parses the event type and routes to appropriate handler
    3. Extracts company_id from directory_id via company_workos_config
    4. Logs all events to sso_audit_logs
    5. Returns 200 OK quickly to acknowledge receipt

    Supported events:
    - dsync.user.created
    - dsync.user.updated
    - dsync.user.deleted
    - dsync.group.created
    - dsync.group.updated
    - dsync.group.deleted
    - dsync.group.user_added
    - dsync.group.user_removed
    """
    payload = await request.body()
    sig_header = request.headers.get("WorkOS-Signature") or request.headers.get("workos-signature")

    if not WORKOS_WEBHOOK_SECRET:
        env = os.getenv("ENVIRONMENT", "development")
        if env in ("production", "staging"):
            logger.error(
                "LIA-SEC-03 WORKOS_WEBHOOK_SECRET not configured in %s — rejecting webhook", env,
            )
            raise HTTPException(status_code=503, detail="Webhook secret not configured")
        logger.warning("WORKOS_WEBHOOK_SECRET not configured - webhook signature validation skipped in development")
    elif not verify_workos_webhook_signature(payload, sig_header, WORKOS_WEBHOOK_SECRET):
        logger.warning("Invalid WorkOS webhook signature")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid signature"}
        )

    try:
        event = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON payload"}
        )

    event_type = event.get("event")
    event_id = event.get("id")
    data = event.get("data", {})

    directory_id = data.get("directory_id")
    if not directory_id:
        if "group" in data:
            directory_id = data.get("group", {}).get("directory_id")
        elif "user" in data:
            directory_id = data.get("user", {}).get("directory_id")

    company_id = await _get_company_id_from_directory(directory_id, workos_repo) or None

    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Received WorkOS webhook: {event_type} (event_id={event_id}, directory={directory_id}, company={company_id})")

    handler_result = {"success": True, "message": f"Event {event_type} acknowledged"}

    user_event_types = {"dsync.user.created", "dsync.user.updated", "dsync.user.deleted"}
    group_event_types = {"dsync.group.created", "dsync.group.updated", "dsync.group.deleted"}
    membership_event_types = {"dsync.group.user_added", "dsync.group.user_removed"}

    try:
        if event_type == "dsync.user.created":
            handler_result = await _handle_dsync_user_created(data, directory_id, company_id, event_id, user_repo)
        elif event_type == "dsync.user.updated":
            handler_result = await _handle_dsync_user_updated(data, directory_id, company_id, event_id, user_repo)
        elif event_type == "dsync.user.deleted":
            handler_result = await _handle_dsync_user_deleted(data, directory_id, company_id, event_id, user_repo)
        elif event_type == "dsync.group.created":
            handler_result = await _handle_dsync_group_created(data, directory_id, company_id, event_id, workos_repo)
        elif event_type == "dsync.group.updated":
            handler_result = await _handle_dsync_group_updated(data, directory_id, company_id, event_id, workos_repo)
        elif event_type == "dsync.group.deleted":
            handler_result = await _handle_dsync_group_deleted(data, directory_id, company_id, event_id, workos_repo)
        elif event_type == "dsync.group.user_added":
            handler_result = await _handle_dsync_group_user_added(data, directory_id, company_id, event_id, user_repo, workos_repo)
        elif event_type == "dsync.group.user_removed":
            handler_result = await _handle_dsync_group_user_removed(data, directory_id, company_id, event_id, user_repo, workos_repo)
        else:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"No handler for event type: {event_type}")
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error handling {event_type}: {e}", exc_info=True)
        handler_result = {"success": False, "message": f"Handler error: {str(e)}"}

    actor_id = None
    actor_email = None
    target_id = None
    target_email = None

    if event_type and event_type.startswith("dsync.user."):
        actor_id = data.get("id")
        actor_email = data.get("emails", [{}])[0].get("value") if data.get("emails") else None
        target_id = data.get("id")
        target_email = actor_email
    elif event_type and event_type.startswith("dsync.group.user_"):
        user_data_webhook = data.get("user", {})
        group_data_webhook = data.get("group", {})
        actor_id = user_data_webhook.get("id")
        actor_email = user_data_webhook.get("emails", [{}])[0].get("value") if user_data_webhook.get("emails") else None
        target_id = group_data_webhook.get("id")
    elif event_type and event_type.startswith("dsync.group."):
        actor_id = data.get("id")
        target_id = data.get("id")

    # SMOKE-#1 RLS fix (audit 2026-05-20): webhooks externos (sem JWT) precisam
    # injetar company_id na session Postgres para satisfazer RLS policy de sso_audit_logs.
    # Padrão canonical de app/shared/security/webhook_ownership.py:212-225.
    if company_id:
        try:
            from app.core.database import set_tenant_context
            await set_tenant_context(workos_repo.db, str(company_id))
        except Exception as _rls_err:
            # pii-logs ok: nome de tabela/erro técnico, sem PII
            logger.error(
                f"[SCIM] Falha ao setar tenant context para RLS: {_rls_err}",
                exc_info=True,
            )
            # company_id é NOT NULL em sso_audit_logs — sem RLS context o INSERT falha
            return {"success": False, "message": "RLS context setup failed", "event_id": event_id}
    else:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V)
        logger.warning(
            f"[SCIM] Sem company_id resolvido para event_id={event_id} directory={directory_id} — skipping audit log"
        )
        return {"success": True, "message": f"Event {event_type} acknowledged (no company_id, audit skipped)", "event_id": event_id}

    await workos_repo.log_sso_event({
        "company_id": company_id,
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "target_id": target_id,
        "target_email": target_email,
        "source_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "workos_event_id": event_id,
        "payload": {
            "event_type": event_type,
            "directory_id": directory_id,
            "data": data,
            "handler_result": handler_result
        }
    })

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "event_id": event_id, "event_type": event_type}
    )
