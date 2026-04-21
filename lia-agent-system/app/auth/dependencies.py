"""
Authentication dependencies for FastAPI.
"""
import os
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError as JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.auth.security import decode_token, is_token_blacklisted, get_password_hash
from app.core.database import get_db
from app.core.tenant import DEMO_COMPANY_UUID, normalize_demo_company_id

DEMO_USER_EMAIL = "demo@wedotalent.com"
DEMO_USER_PASSWORD = os.getenv("DEV_AUTO_LOGIN_PASSWORD", "demo123")

_DEV_ENVS = {"development", "dev", "local"}


def _is_dev_environment() -> bool:
    """Single source of truth for dev-mode gating (canonical APP_ENV)."""
    from app.core.config import settings as app_settings
    env = (
        getattr(app_settings, "APP_ENV", None)
        or getattr(app_settings, "ENVIRONMENT", None)
        or os.getenv("APP_ENV", "development")
    )
    return str(env).lower() in _DEV_ENVS


async def ensure_demo_user(db: AsyncSession) -> User:
    """
    Ensure the dev demo user exists with a usable bcrypt password hash.

    Idempotent: creates the user if missing, repairs the password hash if it
    was previously seeded with a placeholder (e.g. "demo_not_for_login").
    Used both lazily by `get_current_user_or_demo` and eagerly at startup
    (in dev mode) so that the dev auto-login flow can reach `/auth/login`
    successfully on the very first request.

    Defense-in-depth: refuses to create or repair the demo account outside
    of dev environments, so a forgotten gate at the call site cannot expose
    a credentialed back-door account in production/staging.
    """
    if not _is_dev_environment():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo user is disabled outside development",
        )
    from app.shared.encryption.encrypted_field_mixin import _sha256_hash
    from sqlalchemy import or_
    from uuid import uuid4

    result = await db.execute(
        select(User).where(
            or_(
                User.email_hash == _sha256_hash(DEMO_USER_EMAIL),
                User._email_raw == DEMO_USER_EMAIL,
            )
        )
    )
    demo_user = result.scalar_one_or_none()

    expected_hash_prefix = ("$2a$", "$2b$", "$2y$")
    if demo_user is not None:
        changed = False
        if not demo_user.password_hash or not demo_user.password_hash.startswith(expected_hash_prefix):
            demo_user.password_hash = get_password_hash(DEMO_USER_PASSWORD)
            changed = True
        if demo_user.company_id and str(demo_user.company_id) == "demo_company":
            demo_user.company_id = DEMO_COMPANY_UUID
            changed = True
        if changed:
            await db.commit()
            await db.refresh(demo_user)
        return demo_user

    demo_user = User(
        id=uuid4(),
        email=DEMO_USER_EMAIL,
        name="Demo User",
        password_hash=get_password_hash(DEMO_USER_PASSWORD),
        role=UserRole.recruiter,
        company_id=DEMO_COMPANY_UUID,
        is_active=True,
    )
    db.add(demo_user)
    await db.commit()
    await db.refresh(demo_user)
    return demo_user

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    
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
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None:
            raise credentials_exception
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
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
    
    # Multi-tenancy: only allow demo user in development
    if not _is_dev_environment():
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    return await ensure_demo_user(db)


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

    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

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
    _normalized_cid = normalize_demo_company_id(
        str(user.company_id) if user.company_id is not None else None,
        context="auth.get_user_company_id",
    )
    if _normalized_cid and _normalized_cid != (str(user.company_id) if user.company_id else None):
        user.company_id = _normalized_cid
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
