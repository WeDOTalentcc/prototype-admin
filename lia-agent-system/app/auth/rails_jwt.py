"""
Rails JWT Validator — validates JWTs issued by WeDOTalent ats_api (Rails).

Rails JWT format:
  Payload: {"user_id": <int>, "exp": <unix_timestamp>}
  Algorithm: HS256
  Secret: Rails.application.secrets.secret_key_base

Usage:
    from app.auth.rails_jwt import validate_rails_token, RailsTokenPayload

    payload = validate_rails_token(token, rails_secret_key)
    user_id = payload.user_id
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import jwt
from jwt.exceptions import InvalidTokenError as JWTError

logger = logging.getLogger(__name__)


@dataclass
class RailsTokenPayload:
    """Decoded Rails JWT payload."""
    user_id: int
    exp: datetime
    # Rails JWT doesn't include company_id — resolved via user → account lookup
    raw: dict


def validate_rails_token(
    token: str,
    rails_secret_key: str,
    algorithm: str = "HS256",
) -> RailsTokenPayload | None:
    """
    Validate a JWT issued by the Rails ats_api.

    Args:
        token: The Bearer token string.
        rails_secret_key: Rails secret_key_base (shared secret).
        algorithm: JWT algorithm (HS256 default, same as Rails).

    Returns:
        RailsTokenPayload if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            rails_secret_key,
            algorithms=[algorithm],
            options={"verify_aud": False},  # Rails usa aud="wedo-agent"; validamos via secret + exp
        )
        user_id = payload.get("user_id")
        exp = payload.get("exp")

        if not user_id:
            logger.warning("[RailsJWT] Token missing user_id claim")
            return None

        return RailsTokenPayload(
            user_id=int(user_id),
            exp=datetime.fromtimestamp(exp, tz=UTC) if exp else datetime.max.replace(tzinfo=UTC),
            raw=payload,
        )
    except JWTError as e:
        logger.warning("[RailsJWT] Token validation failed: %s", e)
        return None
    except Exception as e:
        logger.error("[RailsJWT] Unexpected error validating token: %s", e)
        return None


class RailsCompanyResolutionError(Exception):
    """Raised when company_id cannot be resolved for a Rails user_id.

    LIA-SEC-02 (PE-9): Callers MUST handle this exception and reject the request.
    Do NOT fall back to a default company_id — that would break tenant isolation (RLS).
    """


async def resolve_company_from_rails_user(
    user_id: int,
    ats_client: "WeDOTalentATSClient",  # noqa: F821 (forward ref string)
) -> str:
    """
    Resolve company_id/account from a Rails user_id via /v1/me.

    Fail-closed: raises RailsCompanyResolutionError if resolution fails.
    This prevents RLS bypass — if we cannot resolve the tenant, the request
    MUST be rejected, not processed with a default/empty company_id.

    Raises:
        RailsCompanyResolutionError: when /v1/me fails or returns empty account_id.
    """
    try:
        user_info = await ats_client.get_current_user()
    except Exception as e:
        logger.error("[RailsJWT][PE-9] /v1/me call failed for user_id=%s: %s", user_id, e)
        raise RailsCompanyResolutionError(
            f"Cannot resolve company for Rails user {user_id}: /v1/me call failed"
        ) from e

    if not user_info:
        raise RailsCompanyResolutionError(
            f"Cannot resolve company for Rails user {user_id}: /v1/me returned empty"
        )

    company_id = user_info.get("account_id") or user_info.get("company_id")
    if not company_id:
        raise RailsCompanyResolutionError(
            f"Cannot resolve company for Rails user {user_id}: /v1/me response missing account_id/company_id"
        )

    return str(company_id)


def get_rails_jwt_secret() -> str | None:
    """Return the Rails JWT secret from settings (RAILS_JWT_SECRET_KEY env var)."""
    from app.core.config import settings
    return getattr(settings, "RAILS_JWT_SECRET_KEY", None)


def validate_rails_token_from_env(token: str) -> RailsTokenPayload | None:
    """Convenience: validate a Rails JWT using the configured env var secret."""
    secret = get_rails_jwt_secret()
    if not secret:
        logger.warning("[RailsJWT] RAILS_JWT_SECRET_KEY not configured")
        return None
    return validate_rails_token(token, secret)


# Cache simples em memória: rails_user_id → {email, name, account_id, fetched_at}
# TTL curto para refletir mudanças de email/conta no Rails.
_RAILS_ME_CACHE: dict[int, dict] = {}
_RAILS_ME_CACHE_TTL_SECONDS = 300  # 5 min


async def fetch_rails_user_info(token: str, user_id: int) -> dict | None:
    """
    Fetch Rails user info via /v1/me using the Bearer token.

    Returns dict with keys: email, name, account_id. None on failure.
    Cached per user_id for _RAILS_ME_CACHE_TTL_SECONDS.
    """
    import os
    import time

    import httpx

    cached = _RAILS_ME_CACHE.get(user_id)
    if cached and (time.time() - cached["fetched_at"]) < _RAILS_ME_CACHE_TTL_SECONDS:
        return cached

    rails_url = os.environ.get("RAILS_API_URL", "").rstrip("/")
    if not rails_url:
        logger.warning("[RailsJWT] RAILS_API_URL not configured — cannot resolve user")
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{rails_url}/v1/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                logger.warning("[RailsJWT] /v1/me returned %s", resp.status_code)
                return None
            data = resp.json()
    except Exception as e:
        logger.error("[RailsJWT] /v1/me call failed: %s", e)
        return None

    user = data.get("user") or data
    info = {
        "email": user.get("email"),
        "name": user.get("name"),
        "account_id": user.get("account_id"),
        "is_admin": bool(user.get("is_admin")),
        "fetched_at": time.time(),
    }
    _RAILS_ME_CACHE[user_id] = info
    return info
