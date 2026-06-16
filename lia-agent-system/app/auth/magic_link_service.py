"""
Magic-link authentication service (Phase 2 — Rails Elimination).

Replaces Rails GET /v1/auth/magic-link/verify. Stores one-time-tokens in Redis
with a 15-minute TTL. Falls back to simulated mode when no email provider is
configured (development) — in that mode the token is logged, not mailed.

Storage layout (Redis):
    key  : magic_link:{uid}            (uid = URL-safe random 16 bytes)
    value: JSON {"email", "hash", "first_login", "created_at"}
    TTL  : _MAGIC_LINK_TTL_SECONDS (900 s)

The `token` in the URL is a 32-byte URL-safe random string whose SHA-256 hex
digest is stored in Redis. The raw token is NEVER stored — only the hash.
LGPD note: email is stored transiently for token resolution only; it is not
used for profiling or analytics.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from datetime import datetime

logger = logging.getLogger(__name__)

_MAGIC_LINK_TTL_SECONDS: int = 900  # 15 minutes
_MAGIC_LINK_REDIS_PREFIX: str = "magic_link"

# ── helpers ──────────────────────────────────────────────────────────────────

def _redis_key(uid: str) -> str:
    return f"{_MAGIC_LINK_REDIS_PREFIX}:{uid}"


def _hash_token(token: str) -> str:
    """SHA-256 hex digest of the raw token.  Raw token never stored."""
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_uid_and_token() -> tuple[str, str]:
    """Return (uid, token) pair.  uid goes in the Redis key; token in the URL."""
    uid = secrets.token_urlsafe(16)
    token = secrets.token_urlsafe(32)
    return uid, token


# ── public API ────────────────────────────────────────────────────────────────

async def generate_magic_link(
    email: str,
    frontend_url: str,
    first_login: bool = False,
) -> str:
    """
    Generate and persist a magic-link OTT for *email*.

    Returns the full URL that should be sent to the user:
        {frontend_url}/api/auth/magic-link?token=T&uid=U

    The token is persisted in Redis with a TTL.  If Redis is unavailable
    the call raises RuntimeError (caller should surface this as 500).
    """
    from app.core.redis_client import get_redis_connection

    uid, token = _generate_uid_and_token()
    payload = json.dumps(
        {
            "email": email,
            "hash": _hash_token(token),
            "first_login": first_login,
            "created_at": datetime.utcnow().isoformat(),
        }
    )

    redis = await get_redis_connection()
    if redis is None:
        raise RuntimeError("Redis unavailable — cannot issue magic-link token")

    async with redis:
        await redis.set(_redis_key(uid), payload, ex=_MAGIC_LINK_TTL_SECONDS)

    magic_url = f"{frontend_url}/api/auth/magic-link?token={token}&uid={uid}"
    logger.info("[magic_link] OTT stored for uid=%s (TTL=%ds)", uid, _MAGIC_LINK_TTL_SECONDS)
    return magic_url


async def send_magic_link_email(
    email: str,
    magic_url: str,
    company_name: str | None = None,
) -> bool:
    """
    Send the magic-link URL to *email* via the configured email provider.

    Returns True on success, False in simulated/dev mode (no provider configured).
    Raises on hard send failure.
    """
    from app.domains.communication.services.email_providers import get_email_provider

    subject = f"Seu link de acesso — {company_name or 'WeDOTalent'}"
    body_html = (
        f"<p>Clique no link abaixo para acessar a plataforma WeDOTalent:</p>"
        f'<p><a href="{magic_url}" style="font-weight:bold">Acessar agora</a></p>'
        f"<p><small>Este link expira em 15 minutos e pode ser usado uma única vez.</small></p>"
    )
    body_text = (
        f"Clique no link para acessar:\n{magic_url}\n\n"
        "Este link expira em 15 minutos e pode ser usado uma única vez."
    )

    try:
        provider = get_email_provider()
        result = await provider.send_email(
            to_email=email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )
        logger.info("[magic_link] Email sent to %s via %s", email[:4] + "***", provider.provider_name)
        return True
    except Exception as exc:
        # Simulated / unconfigured provider — log URL, don't fail hard in dev
        if os.getenv("APP_ENV", "development") == "development":
            logger.warning("[magic_link][DEV] Email provider unavailable. Magic URL: %s", magic_url)
            return False
        raise RuntimeError(f"Failed to send magic-link email: {exc}") from exc


async def verify_magic_link(token: str, uid: str) -> dict | None:
    """
    Validate the magic-link token.

    Returns ``{"email": str, "first_login": bool}`` on success, ``None`` on
    failure (expired, wrong token, already used).  On success the Redis entry
    is deleted (single-use guarantee).
    """
    from app.core.redis_client import get_redis_connection

    redis = await get_redis_connection()
    if redis is None:
        logger.error("[magic_link] Redis unavailable during verify for uid=%s", uid)
        return None

    key = _redis_key(uid)
    async with redis:
        raw = await redis.get(key)
        if not raw:
            logger.warning("[magic_link] Token not found / expired: uid=%s", uid)
            return None

        try:
            stored = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.error("[magic_link] Corrupt Redis entry for uid=%s", uid)
            return None

        if stored.get("hash") != _hash_token(token):
            logger.warning("[magic_link] Token hash mismatch for uid=%s", uid)
            return None

        # Single-use: delete immediately after successful validation
        await redis.delete(key)

    return {
        "email": stored["email"],
        "first_login": stored.get("first_login", False),
    }
