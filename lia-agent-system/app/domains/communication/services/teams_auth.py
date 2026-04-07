"""
Microsoft Bot Framework JWT validation.
Security layer for Teams webhook endpoints.
"""
import logging
from datetime import datetime, timedelta

import httpx
import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

# Microsoft Bot Framework OpenID configuration endpoints (multiple sources)
BOT_FRAMEWORK_OPENID_CONFIG = "https://login.botframework.com/v1/.well-known/openidconfiguration"
MSFT_OPENID_CONFIG_V2 = "https://login.microsoftonline.com/botframework.com/v2.0/.well-known/openid-configuration"
BOT_FRAMEWORK_TENANT = "d6d49420-f39b-4df7-a1dc-d59a935871db"
MSFT_TENANT_OPENID = f"https://login.microsoftonline.com/{BOT_FRAMEWORK_TENANT}/v2.0/.well-known/openid-configuration"

ALLOWED_SIGNING_ALGORITHMS = ["RS256"]

VALID_ISSUERS = [
    "https://api.botframework.com",
    f"https://sts.windows.net/{BOT_FRAMEWORK_TENANT}/",
    f"https://login.microsoftonline.com/{BOT_FRAMEWORK_TENANT}/v2.0",
]


class BotFrameworkAuthenticator:
    """
    Validates JWT tokens from Microsoft Bot Framework.
    Uses multiple JWKS sources to handle different token issuers.
    """

    def __init__(self):
        self._jwks_clients: list[PyJWKClient] = []
        self._cache_expires: datetime | None = None

    async def validate_token(self, authorization_header: str, expected_app_id: str) -> bool:
        """
        Validate Bot Framework JWT token.

        Args:
            authorization_header: Authorization header value (Bearer <token>)
            expected_app_id: Expected Microsoft App ID

        Returns:
            True if valid, False otherwise
        """
        try:
            if not authorization_header or not authorization_header.startswith("Bearer "):
                logger.warning("Missing or invalid Authorization header")
                return False

            token = authorization_header.replace("Bearer ", "").strip()

            if not self._jwks_clients or not self._cache_expires or datetime.utcnow() > self._cache_expires:
                await self._refresh_jwks_clients()

            # Try each JWKS client until we find a matching signing key
            last_error = None
            for jwks_client in self._jwks_clients:
                try:
                    signing_key = jwks_client.get_signing_key_from_jwt(token)

                    decoded = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=ALLOWED_SIGNING_ALGORITHMS,
                        audience=expected_app_id,
                        options={
                            "verify_signature": True,
                            "verify_exp": True,
                            "verify_aud": True,
                        },
                    )

                    issuer = decoded.get("iss")
                    if issuer not in VALID_ISSUERS:
                        logger.warning(f"Invalid issuer: {issuer}")
                        return False

                    logger.info(f"JWT token validated successfully (issuer={issuer})")
                    return True

                except Exception as e:
                    last_error = e
                    continue

            logger.warning(f"JWT validation failed across all JWKS sources: {last_error}")
            return False

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return False
        except jwt.InvalidAudienceError:
            logger.warning("Invalid JWT audience")
            return False
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating JWT token: {e}", exc_info=True)
            return False

    async def _refresh_jwks_clients(self):
        """Refresh JWKS clients from multiple Microsoft OpenID config endpoints."""
        openid_urls = [
            BOT_FRAMEWORK_OPENID_CONFIG,
            MSFT_OPENID_CONFIG_V2,
            MSFT_TENANT_OPENID,
        ]

        clients = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in openid_urls:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    config = response.json()

                    jwks_uri = config.get("jwks_uri")
                    if jwks_uri:
                        jwks_client = PyJWKClient(jwks_uri, cache_keys=True)
                        clients.append(jwks_client)
                        logger.info(f"JWKS client loaded from {jwks_uri}")
                except Exception as e:
                    logger.warning(f"Failed to load JWKS from {url}: {e}")

        if not clients:
            raise RuntimeError("Failed to load any JWKS clients")

        self._jwks_clients = clients
        self._cache_expires = datetime.utcnow() + timedelta(hours=6)
        logger.info(f"JWKS clients refreshed: {len(clients)} sources loaded")


# Global authenticator instance
bot_auth = BotFrameworkAuthenticator()
