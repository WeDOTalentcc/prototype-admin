"""
Encryption utilities for sensitive data (API keys, credentials).
Uses Fernet symmetric encryption with key from environment.
"""
import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_fernet_instance: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = os.getenv("ENCRYPTION_KEY")
        is_production = os.getenv("ENVIRONMENT", "").lower() == "production"
        if not key:
            if is_production:
                raise RuntimeError(
                    "ENCRYPTION_KEY must be set in production. "
                    "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
            key = Fernet.generate_key().decode()
            logger.warning(
                "ENCRYPTION_KEY not set — generated ephemeral key. "
                "Set ENCRYPTION_KEY env var for persistent encryption."
            )
        _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    try:
        fernet = _get_fernet()
        return fernet.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return ciphertext
