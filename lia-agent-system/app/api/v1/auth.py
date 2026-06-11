"""
Authentication API endpoints.

Onda 4.2f-B4 (2026-05-24): rate limit canonical em forgot-password
para mitigar email flood + enumeration timing attack.
Pattern: data_subject_requests.py via rate_limiter._redis_sliding_window.
"""
import os
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_active_user, get_current_user_or_demo
from app.auth.models import User, UserRole
from app.auth.schemas import (
    EmailVerificationRequest,
    InvitationAccept,
    InvitationInfo,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPublicRegister,
    UserResponse,
)
from app.auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    EMAIL_VERIFICATION_EXPIRE_DAYS,
    INVITATION_EXPIRE_HOURS,
    PASSWORD_RESET_EXPIRE_HOURS,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    get_password_hash,
    verify_password,
)
from app.repositories.dependencies import get_user_repo
from app.repositories.auth_user_repository import UserRepository
from app.domains.communication.services.email_service import EmailService, get_email_service
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.pii_masking import get_masked_logger
from app.shared.security.require_company_id import require_company_id

logger = get_masked_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

FRONTEND_URL = (
    os.getenv("FRONTEND_URL")
    or os.getenv("WEDOTALENT_PLATFORM_URL")
    or "https://plataforma-lia.replit.app"
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    repo: UserRepository = Depends(get_user_repo), 
):
    """
    Register a new user.

    For testing purposes - creates a new user account.
    """
    existing_user = await repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = await repo.create_flush({
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "name": user_data.name,
        "role": UserRole.viewer,
        "is_active": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"User registered: {user.id}")

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    repo: UserRepository = Depends(get_user_repo),
    audit_svc: AuditService = Depends(get_audit_service),
):
    """
    Login with email and password.

    Returns JWT access token and refresh token.
    """
    user = await repo.get_by_email(login_data.email)

    _client_ip = getattr(request, "client", None)
    _masked_ip = "*.*.*.{}".format(_client_ip.host.split(".")[-1]) if _client_ip and _client_ip.host else "unknown"

    if not user or not verify_password(login_data.password, user.password_hash):
        try:
            await audit_svc.log_decision(
                company_id=None,
                agent_name="auth_module",
                decision_type="auth_event",
                action="auth_failed",
                decision="rejected",
                reasoning=["Authentication failed: invalid credentials", "Method: password", f"Source IP: {_masked_ip}"],
                criteria_used=["email_match", "password_hash_verify"],
                human_review_required=False,
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        company_id=getattr(user, "company_id", None),
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"User logged in: {user.id}")

    try:
        _company = getattr(user, "company_id", None)
        await audit_svc.log_decision(
            company_id=str(_company) if _company else None,
            agent_name="auth_module",
            decision_type="auth_event",
            action="authenticated",
            decision="approved",
            reasoning=["User authenticated successfully", "Method: password", f"Role: {user.role.value}", f"Source IP: {_masked_ip}"],
            criteria_used=["email_match", "password_hash_verify", "is_active_check"],
            score=None,
            confidence=1.0,
            human_review_required=False,
        )
    except Exception as audit_err:
        logger.warning(f"Audit log failed for login: {audit_err}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    repo: UserRepository = Depends(get_user_repo), 
):
    """
    Refresh access token using refresh token.
    """
    try:
        payload = decode_token(token_data.refresh_token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await repo.get_by_id(UUID(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        company_id=getattr(user, "company_id", None),
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"Token refreshed for user: {user.id}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get current authenticated user information.

    This is a protected endpoint that requires a valid access token.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        company_id=current_user.company_id,
        is_active=current_user.is_active,
        avatar_url=getattr(current_user, 'avatar_url', None),
        sso_provider=getattr(current_user, 'sso_provider', None),
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    repo: UserRepository = Depends(get_user_repo),
):
    """Update current user's profile (name, avatar)."""
    update_fields = {}
    if profile_data.name is not None:
        update_fields["name"] = profile_data.name
    if profile_data.avatar_url is not None:
        update_fields["avatar_url"] = profile_data.avatar_url

    if not update_fields:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    updated_user = await repo.update(current_user.id, update_fields)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    logger.info(f"Profile updated for user: {current_user.id}")

    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        role=updated_user.role,
        company_id=updated_user.company_id,
        is_active=updated_user.is_active,
        avatar_url=getattr(updated_user, 'avatar_url', None),
        sso_provider=getattr(updated_user, 'sso_provider', None),
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )


@router.put("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user_or_demo),
    repo: UserRepository = Depends(get_user_repo),
):
    """Change password for authenticated user (not available for SSO users)."""
    if getattr(current_user, 'sso_provider', None):
        raise HTTPException(
            status_code=400,
            detail="Usuários SSO não podem alterar senha pela plataforma"
        )

    if not current_user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="Conta sem senha definida (login via SSO)"
        )

    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    new_hash = get_password_hash(data.new_password)
    await repo.update(current_user.id, {"password_hash": new_hash})

    logger.info(f"Password changed for user: {current_user.id}")
    return {"message": "Senha alterada com sucesso"}


@router.post("/public-register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def public_register(
    user_data: UserPublicRegister,
    repo: UserRepository = Depends(get_user_repo),
    email_svc: EmailService = Depends(get_email_service),
):
    # multi-tenancy: public endpoint (public) — no tenant data
    """
    Public self-registration endpoint.
    Creates a new user account with email verification required.
    """
    existing_user = await repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

    verification_token = generate_secure_token()
    verification_expires = datetime.utcnow() + timedelta(days=EMAIL_VERIFICATION_EXPIRE_DAYS)

    user = await repo.create_flush({
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "name": user_data.name,
        "role": UserRole.viewer,
        "is_active": False,
        "email_verified": False,
        "email_verification_token": verification_token,
        "email_verification_token_expires": verification_expires,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    await email_svc.send_user_notification(
        db=repo.db,
        notification_type="email_verification",
        recipient_email=user.email,
        variables={
            "user_name": user.name,
            "verification_link": verification_link
        }
    )

    logger.info(f"User registered via public registration: {user.id}")

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


async def _forgot_password_rate_limit(request: Request, email: str) -> None:
    """Per-IP + per-email rate limit.

    Onda 4.2f-B4 (2026-05-24): mitiga email flood + enumeration timing.
    Limit: 5/15min por IP, 3/hora por email. Fail-open em erro de infra.
    """
    try:
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from app.middleware.rate_limiter import rate_limiter

        client_ip = request.client.host if request.client else "unknown"
        email_hash = _sha256_hash(email.lower().strip())[:16]

        redis_client = await rate_limiter._get_redis()
        if redis_client is None:
            # Fail-open: infra down não bloqueia password reset legítimo
            return

        allowed_ip, _ = await rate_limiter._redis_sliding_window(
            redis_client, key=f"forgot_pw:ip:{client_ip}", window_seconds=900, limit=5,
        )
        if not allowed_ip:
            logger.warning(f"forgot-password rate limit hit (IP): {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Muitas solicitações. Tente novamente em alguns minutos.",
            )

        allowed_email, _ = await rate_limiter._redis_sliding_window(
            redis_client, key=f"forgot_pw:email:{email_hash}", window_seconds=3600, limit=3,
        )
        if not allowed_email:
            logger.warning(f"forgot-password rate limit hit (email_hash): {email_hash}")
            raise HTTPException(
                status_code=429,
                detail="Muitas solicitações para este email. Tente novamente em 1 hora.",
            )
    except HTTPException:
        raise
    except Exception as e:
        # Fail-open · rate limit erro não bloqueia reset legítimo
        logger.warning(f"forgot-password rate limit check failed (fail-open): {e}")


@router.post("/forgot-password", response_model=None)
async def forgot_password(
    request_data: PasswordResetRequest,
    request: Request,
    repo: UserRepository = Depends(get_user_repo),
    email_svc: EmailService = Depends(get_email_service),
):
    """
    Request a password reset email.
    Always returns success to prevent email enumeration.

    Onda 4.2f-B4 (2026-05-24): rate limit 5/15min por IP + 3/hora por email
    para mitigar email flood e enumeration timing attack.
    """
    await _forgot_password_rate_limit(request, request_data.email)

    user = await repo.get_by_email(request_data.email)

    if user:
        reset_token = generate_secure_token()
        reset_expires = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)

        await repo.update_by_instance(user, {
            "password_reset_token": reset_token,
            "password_reset_token_expires": reset_expires,
            "updated_at": datetime.utcnow(),
        })

        reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        await email_svc.send_user_notification(
            db=repo.db,
            notification_type="password_reset",
            recipient_email=user.email,
            variables={
                "user_name": user.name,
                "reset_link": reset_link
            }
        )

        logger.info(f"Password reset requested for: {user.id}")

    return {"message": "Se o email existir em nosso sistema, você receberá um link para redefinir sua senha."}


@router.post("/reset-password", response_model=None)
async def reset_password(
    request_data: PasswordResetConfirm,
    repo: UserRepository = Depends(get_user_repo), 
):
    """
    Reset password using a valid token.
    """
    user = await repo.get_by_password_reset_token(request_data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )

    if user.password_reset_token_expires and user.password_reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Por favor, solicite um novo link de redefinição."
        )

    await repo.update_by_instance(user, {
        "password_hash": get_password_hash(request_data.new_password),
        "password_reset_token": None,
        "password_reset_token_expires": None,
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"Password reset completed for: {user.id}")

    return {"message": "Senha redefinida com sucesso. Você já pode fazer login."}


@router.post("/verify-email", response_model=None)
async def verify_email(
    request_data: EmailVerificationRequest,
    repo: UserRepository = Depends(get_user_repo), 
):
    """
    Verify email using a valid token.
    """
    user = await repo.get_by_email_verification_token(request_data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de verificação inválido"
        )

    if user.email_verification_token_expires and user.email_verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Por favor, solicite um novo email de verificação."
        )

    await repo.update_by_instance(user, {
        "email_verified": True,
        "is_active": True,
        "email_verification_token": None,
        "email_verification_token_expires": None,
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"Email verified for: {user.id}")

    return {"message": "Email verificado com sucesso!"}


@router.post("/resend-verification", response_model=None)
async def resend_verification(
    request_data: PasswordResetRequest,
    repo: UserRepository = Depends(get_user_repo),
    email_svc: EmailService = Depends(get_email_service),
):
    """
    Resend verification email.
    """
    user = await repo.get_by_email(request_data.email)

    if user and not user.email_verified:
        verification_token = generate_secure_token()
        verification_expires = datetime.utcnow() + timedelta(days=EMAIL_VERIFICATION_EXPIRE_DAYS)

        await repo.update_by_instance(user, {
            "email_verification_token": verification_token,
            "email_verification_token_expires": verification_expires,
            "updated_at": datetime.utcnow(),
        })

        verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
        await email_svc.send_user_notification(
            db=repo.db,
            notification_type="email_verification",
            recipient_email=user.email,
            variables={
                "user_name": user.name,
                "verification_link": verification_link
            }
        )

        logger.info(f"Verification email resent to: {user.id}")

    return {"message": "Se o email existir e não estiver verificado, você receberá um novo link de verificação."}


# ---------------------------------------------------------------------------
# DEPRECATED P2-W2-07: sistema legado de invite para entidade User (auth)
# ---------------------------------------------------------------------------
# Este bloco (/invitation-info + /accept-invitation) gerencia convites para
# a entidade User (recrutadores internos WeDOTalent), que usa:
#   - invitation_token (campo no User model)
#   - invitation_sent_at + INVITATION_EXPIRE_HOURS (logica app, sem coluna expires_at)
#
# O sistema CANONICAL de convites para clientes/tenants usa:
#   - ClientUser model (tabela client_users)
#   - invitation_expires_at como coluna dedicada (migration 193)
#   - Endpoints: POST /api/v1/client-users/invitations/accept
#                GET  /api/v1/client-users/invitations/validate
#     (client_users.py - invitation_router)
#
# TODO P2-W2-07: avaliar migracao da expiracao de convite User para coluna
#   invitation_expires_at (igual ao pattern ClientUser) em vez de
#   invitation_sent_at + timedelta. Enquanto isso: manter os dois sistemas
#   pois servem entidades distintas (User != ClientUser).
# ---------------------------------------------------------------------------
@router.get("/invitation-info/{token}", response_model=InvitationInfo)
async def get_invitation_info(
    token: str,
    repo: UserRepository = Depends(get_user_repo)
):
    """
    Get invitation information for a token.
    """
    user = await repo.get_by_invitation_token(token)

    if not user:
        return InvitationInfo(
            email="",
            name="",
            valid=False,
            message="Convite inválido ou não encontrado"
        )

    if user.invitation_sent_at:
        expires_at = user.invitation_sent_at + timedelta(hours=INVITATION_EXPIRE_HOURS)
        if expires_at < datetime.utcnow():
            return InvitationInfo(
                email=user.email,
                name=user.name,
                valid=False,
                message="Convite expirado. Por favor, solicite um novo convite."
            )

    return InvitationInfo(
        email=user.email,
        name=user.name,
        company_id=user.company_id,
        valid=True
    )


@router.post("/accept-invitation", response_model=None)
async def accept_invitation(
    request_data: InvitationAccept,
    repo: UserRepository = Depends(get_user_repo), 
):
    """
    Accept an invitation and set password.
    """
    user = await repo.get_by_invitation_token(request_data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Convite inválido ou não encontrado"
        )

    if user.invitation_sent_at:
        expires_at = user.invitation_sent_at + timedelta(hours=INVITATION_EXPIRE_HOURS)
        if expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Convite expirado. Por favor, solicite um novo convite."
            )

    await repo.update_by_instance(user, {
        "password_hash": get_password_hash(request_data.password),
        "invitation_token": None,
        "is_active": True,
        "email_verified": True,
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"Invitation accepted for: {user.id}")

    return {"message": "Conta ativada com sucesso! Você já pode fazer login."}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1b — Token exchange: Rails JWT → FastAPI JWT
# (2026-06-10, Rails Elimination Plan)
# ─────────────────────────────────────────────────────────────────────────────

class RailsTokenExchangeRequest(BaseModel):
    """Body for POST /auth/exchange — Rails JWT → FastAPI JWT conversion."""

    model_config = {"extra": "forbid"}

    rails_token: str


class RailsTokenExchangeResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    upgraded_from: str = "rails_jwt"


@router.post("/exchange", response_model=RailsTokenExchangeResponse)
async def exchange_rails_token(
    request: RailsTokenExchangeRequest,
    repo: UserRepository = Depends(get_user_repo),
    audit_svc: AuditService = Depends(get_audit_service),
):
    """
    Exchange a Rails-issued JWT for a FastAPI-issued JWT.

    Phase 1b Rails Elimination (2026-06-10):
    Allows users / API clients that hold a Rails JWT (signed with
    RAILS_JWT_SECRET_KEY) to upgrade to a FastAPI JWT (signed with SECRET_KEY)
    without re-authenticating. This endpoint is the migration path that makes
    FASTAPI_AUTH_PRIMARY=true safe to flip: all existing Rails sessions are
    upgraded on their first request after the flag is set.

    Flow:
    1. Validate the Rails JWT (signature + expiry via RAILS_JWT_SECRET_KEY)
    2. Resolve user from FastAPI DB (uses Phase 1a DB cache: no Rails HTTP call)
    3. Look up the FastAPI User record by email
    4. Issue a fresh FastAPI JWT (ACCESS + REFRESH) for that user
    5. Background: upsert user into DB cache if not already there

    Security:
    - RAILS_JWT_SECRET_KEY must be configured; missing secret → 503
    - Rails JWT must not be expired
    - User must be is_active=True in FastAPI DB
    - Audit trail logged (action=rails_token_exchange)
    """
    from app.auth.rails_jwt import validate_rails_token_from_env
    from app.auth.rails_user_sync import get_or_sync_rails_user
    from app.core.config import settings

    # Validate Rails JWT signature + expiry
    rails_payload = validate_rails_token_from_env(request.rails_token)
    if not rails_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Rails token",
        )

    # Resolve user info (L1 cache → L2 DB → Rails /v1/me)
    rails_info = await get_or_sync_rails_user(request.rails_token, rails_payload.user_id)
    if not rails_info or not rails_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot resolve user — Rails user resolution failed",
        )

    email = rails_info["email"]
    company_id = str(rails_info.get("account_id") or rails_info.get("company_id") or "")

    # Look up FastAPI user record
    user = await repo.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "User not found in FastAPI DB. "
                "Please log in with email + password to create your account."
            ),
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Issue FastAPI JWT
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        company_id=company_id or getattr(user, "company_id", None),
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info("[Phase1b] Rails→FastAPI token exchange for user: %s", str(user.id)[:8])

    try:
        await audit_svc.log_decision(
            company_id=company_id or None,
            agent_name="auth_module",
            decision_type="auth_event",
            action="rails_token_exchange",
            decision="approved",
            reasoning=[
                "Rails JWT validated and exchanged for FastAPI JWT",
                f"rails_user_id={rails_payload.user_id}",
                f"source={rails_info.get('_source', 'unknown')}",
            ],
            criteria_used=["rails_jwt_valid", "fastapi_user_found", "is_active"],
            confidence=1.0,
            human_review_required=False,
        )
    except Exception as audit_err:
        logger.warning("[Phase1b] Audit log failed for token exchange: %s", audit_err)

    return RailsTokenExchangeResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
