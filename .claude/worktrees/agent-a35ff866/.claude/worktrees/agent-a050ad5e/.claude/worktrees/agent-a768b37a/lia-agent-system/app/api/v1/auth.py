"""
Authentication API endpoints.
"""
import logging
import os
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.models import User, UserRole
from app.auth.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse, TokenRefresh,
    PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest,
    UserPublicRegister, InvitationAccept, InvitationInfo
)
from app.auth.security import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token,
    decode_token, ACCESS_TOKEN_EXPIRE_MINUTES,
    generate_secure_token, PASSWORD_RESET_EXPIRE_HOURS,
    INVITATION_EXPIRE_HOURS, EMAIL_VERIFICATION_EXPIRE_DAYS
)
from app.auth.dependencies import get_current_active_user
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://plataforma-lia.replit.app")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    For testing purposes - creates a new user account.
    """
    existing_user = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        role=UserRole(user_data.role.value),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"User registered: {user.email}")
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns JWT access token and refresh token.
    """
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
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
        role=user.role.value
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    
    logger.info(f"User logged in: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
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
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    logger.info(f"Token refreshed for user: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
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
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post("/public-register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def public_register(
    user_data: UserPublicRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Public self-registration endpoint.
    Creates a new user account with email verification required.
    """
    existing_user = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    verification_token = generate_secure_token()
    verification_expires = datetime.utcnow() + timedelta(days=EMAIL_VERIFICATION_EXPIRE_DAYS)
    
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        role=UserRole.viewer,
        is_active=False,
        email_verified=False,
        email_verification_token=verification_token,
        email_verification_token_expires=verification_expires,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    await email_service.send_user_notification(
        db=db,
        notification_type="email_verification",
        recipient_email=user.email,
        variables={
            "user_name": user.name,
            "verification_link": verification_link
        }
    )
    
    logger.info(f"User registered via public registration: {user.email}")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/forgot-password")
async def forgot_password(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email.
    Always returns success to prevent email enumeration.
    """
    result = await db.execute(
        select(User).where(User.email == request_data.email)
    )
    user = result.scalar_one_or_none()
    
    if user:
        reset_token = generate_secure_token()
        reset_expires = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
        
        user.password_reset_token = reset_token
        user.password_reset_token_expires = reset_expires
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        await email_service.send_user_notification(
            db=db,
            notification_type="password_reset",
            recipient_email=user.email,
            variables={
                "user_name": user.name,
                "reset_link": reset_link
            }
        )
        
        logger.info(f"Password reset requested for: {user.email}")
    
    return {"message": "Se o email existir em nosso sistema, você receberá um link para redefinir sua senha."}


@router.post("/reset-password")
async def reset_password(
    request_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a valid token.
    """
    result = await db.execute(
        select(User).where(User.password_reset_token == request_data.token)
    )
    user = result.scalar_one_or_none()
    
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
    
    user.password_hash = get_password_hash(request_data.new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Password reset completed for: {user.email}")
    
    return {"message": "Senha redefinida com sucesso. Você já pode fazer login."}


@router.post("/verify-email")
async def verify_email(
    request_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email using a valid token.
    """
    result = await db.execute(
        select(User).where(User.email_verification_token == request_data.token)
    )
    user = result.scalar_one_or_none()
    
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
    
    user.email_verified = True
    user.is_active = True
    user.email_verification_token = None
    user.email_verification_token_expires = None
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Email verified for: {user.email}")
    
    return {"message": "Email verificado com sucesso!"}


@router.post("/resend-verification")
async def resend_verification(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend verification email.
    """
    result = await db.execute(
        select(User).where(User.email == request_data.email)
    )
    user = result.scalar_one_or_none()
    
    if user and not user.email_verified:
        verification_token = generate_secure_token()
        verification_expires = datetime.utcnow() + timedelta(days=EMAIL_VERIFICATION_EXPIRE_DAYS)
        
        user.email_verification_token = verification_token
        user.email_verification_token_expires = verification_expires
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
        await email_service.send_user_notification(
            db=db,
            notification_type="email_verification",
            recipient_email=user.email,
            variables={
                "user_name": user.name,
                "verification_link": verification_link
            }
        )
        
        logger.info(f"Verification email resent to: {user.email}")
    
    return {"message": "Se o email existir e não estiver verificado, você receberá um novo link de verificação."}


@router.get("/invitation-info/{token}", response_model=InvitationInfo)
async def get_invitation_info(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get invitation information for a token.
    """
    result = await db.execute(
        select(User).where(User.invitation_token == token)
    )
    user = result.scalar_one_or_none()
    
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


@router.post("/accept-invitation")
async def accept_invitation(
    request_data: InvitationAccept,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept an invitation and set password.
    """
    result = await db.execute(
        select(User).where(User.invitation_token == request_data.token)
    )
    user = result.scalar_one_or_none()
    
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
    
    user.password_hash = get_password_hash(request_data.password)
    user.invitation_token = None
    user.is_active = True
    user.email_verified = True
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Invitation accepted for: {user.email}")
    
    return {"message": "Conta ativada com sucesso! Você já pode fazer login."}
