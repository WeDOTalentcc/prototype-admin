"""
Security utilities for password hashing and JWT token handling.
"""

import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
PASSWORD_RESET_EXPIRE_HOURS = 24
INVITATION_EXPIRE_HOURS = 24
EMAIL_VERIFICATION_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def generate_secure_token() -> str:
    """
    Generate a secure random token for password reset, email verification, or invitations.

    Returns:
        A URL-safe base64-encoded token.
    """
    return secrets.token_urlsafe(32)


def create_access_token(
    subject: str, role: str | None = None, company_id: str | None = None, expires_delta: timedelta | None = None
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (typically user ID or email).
        role: The user's role.
        expires_delta: Optional custom expiration time.

    Returns:
        The encoded JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "role": role,
        "company_id": company_id,
        "iat": datetime.utcnow(),
    }
    # R-007 (Sprint 1): adiciona aud + iss se settings configurados.
    # Tokens emitidos sem aud/iss continuam sendo aceitos pelo decode_token
    # quando settings.JWT_AUDIENCE/ISSUER tambem nao estao setados (backward compat).
    if getattr(settings, "JWT_AUDIENCE", None):
        to_encode["aud"] = settings.JWT_AUDIENCE
    if getattr(settings, "JWT_ISSUER", None):
        to_encode["iss"] = settings.JWT_ISSUER

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: The subject of the token (typically user ID or email).
        expires_delta: Optional custom expiration time.

    Returns:
        The encoded JWT refresh token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"sub": str(subject), "exp": expire, "type": "refresh", "iat": datetime.utcnow()}

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    R-007 (Sprint 1 Quick Wins): valida exp + aud (se configurado) + iss
    (se configurado) explicitamente. exp e' sempre validado pela lib
    (jwt.decode raises ExpiredSignatureError automaticamente). aud/iss
    sao validados quando settings.JWT_AUDIENCE/ISSUER estao setados —
    rejeicao retorna erro JWT correspondente, traduzido em 401 pelo
    middleware auth_enforcement.

    Args:
        token: The JWT token to decode.

    Returns:
        The decoded token payload.

    Raises:
        ExpiredSignatureError: token expirado (exp passou).
        InvalidAudienceError: aud incorreto (quando settings.JWT_AUDIENCE setado).
        InvalidIssuerError: iss incorreto (quando settings.JWT_ISSUER setado).
        JWTError: outras falhas (assinatura, formato, etc.).
    """
    # Sprint E.1 #26: dual-key rotation support (ADR-AUTH-001 / Option B).
    # Try current SECRET_KEY first. On InvalidSignatureError, fall back to
    # SECRET_KEY_LEGACY (when set). All other errors (expired, audience,
    # issuer) bubble up immediately on the first attempt — they are not
    # signature mismatches and should not retry.
    decode_kwargs_common: dict = {
        "algorithms": [settings.ALGORITHM],
    }
    audience = getattr(settings, "JWT_AUDIENCE", None)
    issuer = getattr(settings, "JWT_ISSUER", None)
    if audience:
        decode_kwargs_common["audience"] = audience
    if issuer:
        decode_kwargs_common["issuer"] = issuer

    try:
        return jwt.decode(token, settings.SECRET_KEY, **decode_kwargs_common)
    except jwt.InvalidSignatureError:
        legacy = getattr(settings, "SECRET_KEY_LEGACY", None)
        if not legacy:
            raise
        # Token may have been signed before the rotation window — try the
        # previous key. If it also fails, the original InvalidSignatureError
        # bubbles up unchanged for the caller.
        return jwt.decode(token, legacy, **decode_kwargs_common)
