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
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

from jose import jwt, JWTError

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
) -> Optional[RailsTokenPayload]:
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
            exp=datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.max.replace(tzinfo=timezone.utc),
            raw=payload,
        )
    except JWTError as e:
        logger.warning("[RailsJWT] Token validation failed: %s", e)
        return None
    except Exception as e:
        logger.error("[RailsJWT] Unexpected error validating token: %s", e)
        return None


def resolve_company_from_rails_user(
    user_id: int,
    ats_client: "WeDOTalentATSClient",
) -> Optional[str]:
    """
    Resolve company_id/account from a Rails user_id.

    Since Rails JWT doesn't carry company_id, we need to look it up.
    In the Rails schema, User.account_id → Account.tenant.

    This would call the Rails /v1/me endpoint to get the user's account.
    For now, returns None until the ATSClient is connected.
    """
    # TODO: Implement when Rails is accessible
    # response = await ats_client.get("/v1/me")
    # return response.get("account_id") or response.get("company_id")
    return None
