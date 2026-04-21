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
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash.
        
    Returns:
        The hashed password.
    """
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def generate_secure_token() -> str:
    """
    Generate a secure random token for password reset, email verification, or invitations.
    
    Returns:
        A URL-safe base64-encoded token.
    """
    return secrets.token_urlsafe(32)


def create_access_token(
    subject: str,
    role: str | None = None,
    company_id: str | None = None,
    expires_delta: timedelta | None = None
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
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None
) -> str:
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
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token to decode.
        
    Returns:
        The decoded token payload.
        
    Raises:
        JWTError: If the token is invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    return payload


# ── JWT Blacklist (logout / token revocation) ─────────────────────────────────

import hashlib
from datetime import timezone

_BLACKLIST_PREFIX = "jwt_blacklist:"


def _token_key(token: str) -> str:
    digest = hashlib.sha256(token.encode()).hexdigest()
    return f"{_BLACKLIST_PREFIX}{digest}"


async def blacklist_token(token: str) -> None:
    """Add token to Redis blacklist until its natural expiry."""
    try:
        from app.core.redis_client import get_redis
        payload = decode_token(token)
        exp = payload.get("exp")
        if exp is None:
            return
        ttl = int(exp - datetime.now(timezone.utc).timestamp())
        if ttl <= 0:
            return
        redis = await get_redis()
        if redis is None:
            return
        await redis.setex(_token_key(token), ttl, "1")
    except Exception:
        pass  # non-blocking — logout proceeds even if Redis is down


async def is_token_blacklisted(token: str) -> bool:
    """Return True if the token has been explicitly revoked."""
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        if redis is None:
            return False
        return bool(await redis.exists(_token_key(token)))
    except Exception:
        return False
