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
        payload = jwt.decode(token, rails_secret_key, algorithms=[algorithm])
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


async def resolve_company_from_rails_user(
    user_id: int,
    ats_client: "WeDOTalentATSClient",
) -> str | None:
    """
    Resolve company_id/account from a Rails user_id.
    Calls /v1/me to get the users account_id.
    """
    try:
        user_info = await ats_client.get_current_user()
        if user_info:
            return str(user_info.get("account_id") or user_info.get("company_id") or "")
        return None
    except Exception as e:
        logger.warning("[RailsJWT] Failed to resolve company: %s", e)
        return None


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
