
"""
OTP Service for Shared Searches feature.

Provides OTP generation, hashing, verification, and session token management
for secure access to shared search results.
"""
import logging
import os
import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "shared-search-secret-key"))
JWT_ALGORITHM = "HS256"
OTP_EXPIRY_MINUTES = 10
SESSION_EXPIRY_HOURS = 24


class OTPService:
    """Service for OTP and session token management for Shared Searches."""
    
    def generate_otp(self) -> str:
        """
        Generate a 6-digit numeric OTP.
        
        Returns:
            str: A 6-digit OTP string
        """
        otp = str(secrets.randbelow(1000000)).zfill(6)
        return otp
    
    def hash_otp(self, otp: str) -> str:
        """
        Hash the OTP using bcrypt.
        
        Args:
            otp: Plain text OTP to hash
            
        Returns:
            str: Bcrypt hash of the OTP
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(otp.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_otp(self, plain_otp: str, hashed_otp: str) -> bool:
        """
        Verify that a plain OTP matches its hash.
        
        Args:
            plain_otp: The plain text OTP to verify
            hashed_otp: The stored bcrypt hash
            
        Returns:
            bool: True if the OTP matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_otp.encode('utf-8'),
                hashed_otp.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False
    
    def generate_session_token(
        self, 
        email: str, 
        shared_search_id: str
    ) -> tuple[str, datetime]:
        """
        Generate a secure JWT session token.
        
        Args:
            email: User's email address
            shared_search_id: ID of the shared search
            
        Returns:
            Tuple[str, datetime]: (token, expires_at)
        """
        expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
        
        payload = {
            "email": email,
            "shared_search_id": shared_search_id,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "type": "shared_search_session"
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return token, expires_at
    
    def verify_session_token(self, token: str) -> dict | None:
        """
        Verify a session token and return its payload.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Optional[dict]: Payload with email and shared_search_id if valid,
                           None if invalid or expired
        """
        try:
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=[JWT_ALGORITHM]
            )
            
            if payload.get("type") != "shared_search_session":
                logger.warning("Invalid token type")
                return None
            
            return {
                "email": payload.get("email"),
                "shared_search_id": payload.get("shared_search_id"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat")
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("Session token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid session token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying session token: {e}")
            return None
    
    def get_otp_expiry(self) -> datetime:
        """
        Get the expiration time for an OTP (10 minutes from now).
        
        Returns:
            datetime: Expiration timestamp
        """
        return datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    async def send_otp_email(
        self, 
        email: str, 
        otp: str, 
        shared_search_title: str
    ) -> bool:
        """
        Send an OTP via email for shared search access.
        
        For now, logs the OTP. Will integrate with email service later.
        
        Args:
            email: Recipient email address
            otp: The OTP code to send
            shared_search_title: Title of the shared search
            
        Returns:
            bool: True if successful
        """
        logger.info(
            f"[OTP EMAIL] To: {email}, "
            f"OTP: {otp}, "
            f"Shared Search: {shared_search_title}"
        )
        
        return True


otp_service = OTPService()
