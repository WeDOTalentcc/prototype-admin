"""
Microsoft Bot Framework JWT validation.
Security layer for Teams webhook endpoints.
"""
import logging
from typing import Optional
import jwt
from jwt import PyJWKClient
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Microsoft OpenID configuration endpoints
MICROSOFT_OPENID_CONFIG = "https://login.microsoftonline.com/botframework.com/v2.0/.well-known/openid-configuration"
ALLOWED_SIGNING_ALGORITHMS = ["RS256"]


class BotFrameworkAuthenticator:
    """
    Validates JWT tokens from Microsoft Bot Framework.
    """
    
    def __init__(self):
        self._jwks_uri: Optional[str] = None
        self._jwks_client: Optional[PyJWKClient] = None
        self._cache_expires: Optional[datetime] = None
    
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
            # Extract token from header
            if not authorization_header or not authorization_header.startswith("Bearer "):
                logger.warning("Missing or invalid Authorization header")
                return False
            
            token = authorization_header.replace("Bearer ", "").strip()
            
            # Get JWKS URI
            if not self._jwks_client or not self._cache_expires or datetime.utcnow() > self._cache_expires:
                await self._refresh_jwks_client()
            
            # Decode and validate token
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=ALLOWED_SIGNING_ALGORITHMS,
                audience=expected_app_id,  # Token must be for our app
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True
                }
            )
            
            # Verify issuer
            valid_issuers = [
                "https://api.botframework.com",
                "https://sts.windows.net/d6d49420-f39b-4df7-a1dc-d59a935871db/",  # BotFramework tenant
                "https://login.microsoftonline.com/d6d49420-f39b-4df7-a1dc-d59a935871db/v2.0"
            ]
            
            if decoded.get("iss") not in valid_issuers:
                logger.warning(f"Invalid issuer: {decoded.get('iss')}")
                return False
            
            logger.info("JWT token validated successfully")
            return True
            
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
    
    async def _refresh_jwks_client(self):
        """Refresh JWKS client from Microsoft OpenID config."""
        try:
            async with httpx.AsyncClient() as client:
                # Get OpenID configuration
                response = await client.get(MICROSOFT_OPENID_CONFIG)
                response.raise_for_status()
                config = response.json()
                
                jwks_uri = config.get("jwks_uri")
                if not jwks_uri:
                    raise ValueError("No jwks_uri in OpenID configuration")
                
                self._jwks_uri = jwks_uri
                self._jwks_client = PyJWKClient(jwks_uri)
                self._cache_expires = datetime.utcnow() + timedelta(hours=24)
                
                logger.info(f"JWKS client refreshed from {jwks_uri}")
                
        except Exception as e:
            logger.error(f"Failed to refresh JWKS client: {e}", exc_info=True)
            raise


# Global authenticator instance
bot_auth = BotFrameworkAuthenticator()
