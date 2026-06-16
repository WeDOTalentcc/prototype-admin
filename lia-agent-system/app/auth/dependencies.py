"""
Authentication dependencies for FastAPI.
"""
import logging
import os
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status

logger = logging.getLogger(__name__)

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError as JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.auth.security import decode_token
from app.core.database import get_db

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.

    Aceita APENAS tokens FastAPI (payload com `sub`=UUID, `type`=access).
    Rails JWT não é mais aceito neste path (2026-06-13).
    Clientes com Rails JWT devem usar POST /api/v1/auth/exchange.

    Args:
        credentials: The HTTP bearer token credentials.
        db: The database session.

    Returns:
        The authenticated user.

    Raises:
        HTTPException: If authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    # 1. Tenta FastAPI JWT
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id and token_type == "access":
            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()
            if user is not None:
                return user
    except JWTError:
        pass  # FastAPI JWT inválido — rejeita (sem Rails fallback)
    except Exception:
        pass

    # Rails JWT fallback removido (2026-06-13): FastAPI JWT é fonte de verdade.
    # Clientes com Rails JWT devem trocar via POST /api/v1/auth/exchange.
    raise credentials_exception


async def _resolve_rails_jwt_user(token: str, db: AsyncSession) -> User | None:
    """
    Valida token Rails e resolve o User do FastAPI pelo email (via /v1/me).
    Auto-provisiona o usuário FastAPI se não existir.
    """
    from app.auth.rails_jwt import fetch_rails_user_info, validate_rails_token_from_env
    from app.shared.encryption.encrypted_field_mixin import _sha256_hash

    rails_payload = validate_rails_token_from_env(token)
    if rails_payload is None:
        return None

    info = await fetch_rails_user_info(token, rails_payload.user_id)
    if not info or not info.get("email"):
        return None

    email = info["email"]
    email_hash = _sha256_hash(email)

    result = await db.execute(
        select(User).where(User.email_hash == email_hash)
    )
    user = result.scalar_one_or_none()

    raw_company_id = str(info.get("account_id") or "")

    if user is not None:
        # Update company_id/role if they're missing (auto-heal provisioning gaps)
        updated = False
        if not user.company_id and raw_company_id:
            user.company_id = raw_company_id
            updated = True
        if info.get("is_admin") and user.role != UserRole.admin:
            user.role = UserRole.admin
            updated = True
        if updated:
            await db.commit()
            await db.refresh(user)
        return user

    # Auto-provisiona usuário FastAPI mirrorando o Rails
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email=email,
        name=info.get("name") or email.split("@")[0],
        password_hash="rails_sso_no_password",  # login real via Rails
        role=UserRole.admin if info.get("is_admin") else UserRole.recruiter,
        company_id=raw_company_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        The authenticated user if active.
        
    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """
    Dependency factory to require specific roles.
    
    Args:
        allowed_roles: List of roles that are allowed access.
        
    Returns:
        A dependency function that checks the user's role.
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


require_admin = require_role([UserRole.admin])
require_admin_or_recruiter = require_role([UserRole.admin, UserRole.recruiter])

# WeDOTalent staff-only gate. Canonical use: per-tenant overrides edited by
# Anderson + ops via admin2.wedotalent.cc. Customer-end admins (UserRole.admin)
# MUST receive 403 — they administer their own org, not the platform.
# See app/api/v1/admin_prompts.py tenant-override endpoints + the contract
# document docs/admin-wedotalent-integration.md for the canonical caller set.
require_wedotalent_admin = require_role([UserRole.wedotalent_admin])


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> User | None:
    """
    Dependency to get the current user if authenticated, or None if not.
    
    This is useful for endpoints that work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            return None
            
    except JWTError:
        return None
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    return result.scalar_one_or_none()


def _is_dev_environment() -> bool:
    """Check whether the app is running in development mode.

    Gating uses APP_ENV (the canonical Settings field). The legacy
    ``ENVIRONMENT`` attribute is NOT a Settings field (model_config uses
    extra="ignore"), so ``getattr(settings, "ENVIRONMENT", "development")``
    always returned ``"development"`` — which left the demo-user fallback
    active even in production. APP_ENV is set to ``"production"`` by the
    deployment run command, so this correctly disables demo auth in prod.
    """
    from app.core.config import settings as _app_settings
    return _app_settings.APP_ENV == "development"


async def _heal_legacy_demo_company_id(user, db) -> None:
    """Tenant healing for the demo account — fixes B1 (LIA pergunta company_id).

    Scope: this helper covers ONLY the **tenant identity** of the demo user.
    It is NOT the wizard session-continuity layer (B2/B3/B4) — those are
    handled by the canonical ``app.shared.sessions.derive_thread_id`` +
    LangGraph checkpointer + handler-level pin (Task #1080). The two layers
    were briefly conflated under "Task #1051" in the codebase; this helper
    is the only artifact of that work that survives, because the demo
    tenant id problem is genuinely orthogonal to session continuity.

    Behavior: heals ANY non-canonical demo ``company_id`` — not only the
    literal ``"demo_company"`` string. Demo users that ever ended up with
    a malformed/legacy/empty value (any state that ``CompanyId.parse``
    cannot consume) are reconciled in-place to ``CANONICAL_DEMO_UUID``.
    Broader-than-named scope is INTENTIONAL: a demo user is platform
    hygiene, not real tenant data — any invalid state should converge
    silently rather than block the chat.

    Legacy demo users persisted with ``company_id="demo_company"`` (or other
    string values) trigger the recurring T-E bug ("LIA pergunta company_id no
    chat") because ``CompanyId.parse`` rejects the value and the wizard mixin
    fails-closed. New users are seeded with ``CANONICAL_DEMO_UUID``
    (``00000000-0000-4000-a000-000000000001``), but this helper reconciles
    any pre-existing legacy row in-place.

    Idempotent + fail-open: any DB error is logged but never raises — the
    fallback is degradation back to the bug, not a hard 500 on login.

    LGPD: log carries only ``user_id`` (UUID) + the literal legacy value;
    NEVER the demo email or any other PII.
    """
    from scripts.seeds.demo_company import CANONICAL_DEMO_UUID

    current = str(getattr(user, "company_id", "") or "")
    if current == CANONICAL_DEMO_UUID:
        return
    try:
        legacy_value = current
        user.company_id = CANONICAL_DEMO_UUID
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.warning(
            "demo_user_company_id_healed",
            extra={
                "event": "demo_user_company_id_healed",
                "user_id": str(getattr(user, "id", "")),
                "legacy_company_id": legacy_value or "<empty>",
                "canonical_company_id": CANONICAL_DEMO_UUID,
                "task": "#1081",
            },
        )
    except Exception as exc:  # pragma: no cover — fail-open
        logger.error(
            "demo_user_company_id_heal_failed",
            extra={
                "event": "demo_user_company_id_heal_failed",
                "user_id": str(getattr(user, "id", "")),
                "error": type(exc).__name__,
            },
        )


async def ensure_demo_user(db):
    """Ensure a demo user exists; repairs placeholder password hashes.

    Raises HTTP 403 outside development so callers cannot accidentally
    expose this path in staging/production.
    """
    if not _is_dev_environment():
        raise HTTPException(
            status_code=403,
            detail="ensure_demo_user is only available in development",
        )

    from app.shared.encryption.encrypted_field_mixin import _sha256_hash
    from sqlalchemy import or_ as _or_

    _demo_email = "demo@wedotalent.com"
    result = await db.execute(
        select(User).where(
            _or_(
                User.email_hash == _sha256_hash(_demo_email),
                User._email_raw == _demo_email,
            )
        )
    )
    demo_user = result.scalar_one_or_none()

    if demo_user:
        # Repair placeholder / non-bcrypt hashes
        if not demo_user.password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            from app.auth.security import get_password_hash
            demo_user.password_hash = get_password_hash("demo123")
            await db.commit()
        # B1 (tenant identity) — auto-heal legacy company_id of the demo user.
        # Orthogonal to wizard session continuity (B2/B3/B4 → Task #1080).
        await _heal_legacy_demo_company_id(demo_user, db)
        return demo_user

    # Create demo user with a proper bcrypt hash
    from uuid import uuid4
    from app.auth.security import get_password_hash as _gph
    from scripts.seeds.demo_company import CANONICAL_DEMO_UUID
    demo_user = User(
        id=uuid4(),
        email=_demo_email,
        name="Demo User",
        password_hash=_gph("demo123"),
        role=UserRole.recruiter,
        company_id=CANONICAL_DEMO_UUID,
        is_active=True,
    )
    db.add(demo_user)
    await db.commit()
    await db.refresh(demo_user)
    return demo_user


async def get_current_user_or_demo(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that returns the authenticated user or a demo user.
    
    For development and demo purposes, returns a demo user when:
    - No authentication token is provided
    - The token is invalid
    
    This allows the frontend to work without requiring login during development.
    """
    if credentials:
        try:
            payload = decode_token(credentials.credentials)
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id and token_type == "access":
                result = await db.execute(
                    select(User).where(User.id == UUID(user_id))
                )
                user = result.scalar_one_or_none()
                if user and user.is_active:
                    return user
        except (JWTError, Exception):
            pass

        # Rails JWT fallback removido (2026-06-13): FastAPI JWT é fonte de verdade.
        # Clientes com Rails JWT devem trocar via POST /api/v1/auth/exchange.

    # Multi-tenancy: only allow demo user in development
    if not _is_dev_environment():
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    from app.shared.encryption.encrypted_field_mixin import _sha256_hash
    from sqlalchemy import or_
    _demo_email = "demo@wedotalent.com"
    result = await db.execute(
        select(User).where(
            or_(
                User.email_hash == _sha256_hash(_demo_email),
                User._email_raw == _demo_email,
            )
        )
    )
    demo_user = result.scalar_one_or_none()
    
    if demo_user:
        # B1 (tenant identity) — auto-heal legacy company_id of the demo user.
        # Orthogonal to wizard session continuity (B2/B3/B4 → Task #1080).
        await _heal_legacy_demo_company_id(demo_user, db)
        return demo_user
    
    from uuid import uuid4
    from scripts.seeds.demo_company import CANONICAL_DEMO_UUID
    # F-BG.1 (audit 2026-05-20): RLS deny-by-default em users (migration 068)
    # exige `app.company_id` setado na sessão Postgres antes do INSERT.
    # Sem isso, 100% das requests anônimas em dev caem em HTTP 500 + traceback ~70 linhas.
    from app.core.database import set_tenant_context
    await set_tenant_context(db, str(CANONICAL_DEMO_UUID))

    demo_user = User(
        id=uuid4(),
        email="demo@wedotalent.com",
        name="Demo User",
        password_hash="demo_not_for_login",
        role=UserRole.recruiter,
        company_id=CANONICAL_DEMO_UUID,
        is_active=True
    )
    db.add(demo_user)
    await db.commit()
    await db.refresh(demo_user)
    
    return demo_user


async def get_current_user_strict(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Strict auth dependency — no demo fallback.

    Use on sensitive endpoints (admin, compliance, billing, LGPD, audit)
    where a demo fallback would be a security risk.

    Raises HTTP 401 if token is missing or invalid.
    Raises HTTP 403 if the user account is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user: User | None = None

    # 1. Tenta FastAPI JWT
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id and token_type == "access":
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
    except JWTError:
        pass

    # Rails JWT fallback removido (2026-06-13): FastAPI JWT é fonte de verdade.
    # Clientes com Rails JWT devem trocar via POST /api/v1/auth/exchange.
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


def validate_company_access(user: User, company_id: str) -> None:
    """
    Validate that the user has access to the specified company.
    
    Args:
        user: The authenticated user
        company_id: The company ID being accessed
        
    Raises:
        HTTPException: If the user doesn't have access to the company
    """
    if not user.can_access_company(company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access this company's data"
        )


def get_user_company_id(user: User) -> str:
    """
    Get the company ID for the user. Returns the user's company_id.
    Simple helper that always returns the user's own company.
    
    Args:
        user: The authenticated user
        
    Returns:
        The company ID for the user
    """
    if not user.company_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="User has no company_id assigned. A valid company_id is required for multi-tenant operations."
        )
    return user.company_id


def assert_resource_ownership(resource, user: User, resource_type: str = "resource") -> None:
    """
    Assert that a resource belongs to the user's company.
    For admins accessing cross-tenant resources, logs the access for audit.
    
    Args:
        resource: The database resource with company_id attribute
        user: The authenticated user
        resource_type: Name of resource for error message
        
    Raises:
        HTTPException: If resource doesn't belong to user's company (non-admin)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not hasattr(resource, 'company_id'):
        return
    
    resource_company = getattr(resource, 'company_id', None)
    user_company = user.company_id
    
    if user.role == UserRole.admin:
        if resource_company != user_company:
            resource_id = getattr(resource, 'id', 'unknown')
            logger.warning(
                f"[AUDIT] Admin cross-tenant access: user={user.id} ({user.email}) "
                f"accessing {resource_type}={resource_id} from company={resource_company} "
                f"(user's company={user_company})"
            )
        return
    
    if not user.can_access_company(resource_company):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: This {resource_type} belongs to another company"
        )


def assert_admin_cross_tenant_access(
    resource, 
    user: User, 
    action: str,
    resource_type: str = "resource"
) -> None:
    """
    Explicit validation for admin cross-tenant access with detailed audit logging.
    Use this for sensitive operations that modify data across tenants.
    
    Args:
        resource: The database resource with company_id attribute
        user: The authenticated user (must be admin for cross-tenant)
        action: The action being performed (e.g., "update", "delete")
        resource_type: Name of resource for logging
        
    Raises:
        HTTPException: If non-admin attempts cross-tenant access
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not hasattr(resource, 'company_id'):
        return
    
    resource_company = getattr(resource, 'company_id', None)
    user_company = user.company_id
    
    is_cross_tenant = resource_company != user_company
    
    if is_cross_tenant:
        if user.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: This {resource_type} belongs to another company"
            )
        
        resource_id = getattr(resource, 'id', 'unknown')
        logger.warning(
            f"[AUDIT:CROSS-TENANT] Admin {action}: user={user.id} ({user.email}) "
            f"performing '{action}' on {resource_type}={resource_id} "
            f"from company={resource_company} (user's company={user_company})"
        )


async def derive_company_from_context(
    context: dict[str, Any] | None,
    db: AsyncSession,
    fallback: str = "default"
) -> str:
    """
    Safely derive company_id from context.
    
    Priority:
    1. user_id in context -> fetch user and get company_id
    2. company_id in context (only if no user_id to validate against)
    3. fallback value
    
    This ensures company_id is derived from authenticated session when possible,
    not just trusted from caller-provided context.
    
    Args:
        context: Context dictionary (may contain user_id, company_id)
        db: Database session
        fallback: Fallback company_id if none can be derived
        
    Returns:
        Validated company_id string
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not context:
        return fallback
    
    user_id = context.get("user_id")
    if user_id:
        try:
            result = await db.execute(
                select(User).where(User.id == UUID(str(user_id)))
            )
            user = result.scalar_one_or_none()
            if user and user.company_id:
                logger.debug(f"Derived company_id={user.company_id} from user_id={user_id}")
                return user.company_id
        except Exception as e:
            logger.warning(f"Failed to derive company from user_id={user_id}: {e}")
    
    context_company = context.get("company_id")
    if context_company:
        if user_id:
            logger.warning(
                f"Using context company_id={context_company} but user_id={user_id} "
                "has no company - potential security gap"
            )
        return context_company
    
    return fallback


async def get_service_or_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current user or validate service token.
    Checks for SERVICE_API_TOKEN in Authorization header for server-to-server calls.
    """
    service_token = os.getenv("SERVICE_API_TOKEN")
    
    if credentials and service_token:
        if credentials.credentials == service_token:
            from app.shared.encryption.encrypted_field_mixin import _sha256_hash
            from sqlalchemy import or_
            _svc_email = "service@wedotalent.com"
            result = await db.execute(
                select(User).where(
                    or_(
                        User.email_hash == _sha256_hash(_svc_email),
                        User._email_raw == _svc_email,
                    )
                )
            )
            service_user = result.scalar_one_or_none()
            
            if not service_user:
                service_user = User(
                    email="service@wedotalent.com",
                    name="Service Account",
                    password_hash="",
                    role=UserRole.admin,
                    is_active=True
                )
                db.add(service_user)
                await db.commit()
                await db.refresh(service_user)
            
            return service_user
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
