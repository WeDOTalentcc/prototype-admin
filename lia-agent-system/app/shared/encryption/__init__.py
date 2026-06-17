"""
Encryption utilities canonical — symmetric encryption for JSON nested fields,
Redis-cached values, and other at-rest secrets that don't fit the
EncryptedFieldMixin (per-column hybrid_property) pattern.

Canonical env var: FIELD_ENCRYPTION_KEY (same as EncryptedFieldMixin — ONE key
for all at-rest encryption in lia-agent-system).

Deprecated env var: ENCRYPTION_KEY (legacy fork from pre-2026-05-20 — still
accepted with deprecation warning. Will be removed after 1 release cycle.)

Behavior contract:
- decrypt_value(): raises DecryptionError on failure (canonical fail-loud).
  REGRA 4 (CLAUDE.md): NEVER return ciphertext as if it were plaintext.
- safe_decrypt_value(): returns None on failure with WARN log (opt-in
  soft-fail for callers that legitimately need it — should be rare).

Re-exports EncryptedFieldMixin for backward compat.
"""
from __future__ import annotations

import logging
import os

from cryptography.fernet import Fernet, InvalidToken

from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin  # noqa: F401

logger = logging.getLogger(__name__)

_fernet_instance: Fernet | None = None


class DecryptionError(RuntimeError):
    """Raised when ciphertext cannot be decrypted with the current key.

    Common causes:
    - Key mismatch: FIELD_ENCRYPTION_KEY differs from key used to encrypt
    - Ciphertext corrupted
    - Value was actually plaintext (pre-encryption legacy row)
    """


def _get_fernet() -> Fernet:
    """
    Return a singleton Fernet instance for symmetric encryption.

    Resolution order:
    1. FIELD_ENCRYPTION_KEY (canonical) — same key as EncryptedFieldMixin
    2. ENCRYPTION_KEY (DEPRECATED) — emits warning, will be removed
    3. Ephemeral key — ONLY if IS_DEVELOPMENT=true; raises otherwise
    """
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    key = os.getenv("FIELD_ENCRYPTION_KEY")
    if not key:
        legacy = os.getenv("ENCRYPTION_KEY")
        if legacy:
            logger.warning(
                "ENCRYPTION_KEY is DEPRECATED — set FIELD_ENCRYPTION_KEY "
                "(same Fernet format) and remove ENCRYPTION_KEY. "
                "Backward compat will be removed in next release."
            )
            key = legacy

    env = os.getenv("ENVIRONMENT", "").lower()
    is_production = env == "production"
    # P1-W3-06 fix: staging também exige key persistente — ephemeral em staging
    # causa falhas de decrypt entre restarts (webhook secrets, tenant API keys, etc.)
    # criados num processo não decriptam no próximo. Antes apenas "production" bloqueava.
    is_staging = env in ("staging", "homologation", "homolog")
    is_dev = os.getenv("IS_DEVELOPMENT", "").lower() in ("true", "1", "yes")

    if not key:
        if is_production:
            raise RuntimeError(
                "FIELD_ENCRYPTION_KEY must be set in production. "
                "Generate with: python3 -c \"from cryptography.fernet import "
                "Fernet; print(Fernet.generate_key().decode())\""
            )
        if is_staging:
            raise RuntimeError(
                "FIELD_ENCRYPTION_KEY must be set in staging/homologation. "
                "Ephemeral keys cause decrypt failures across restarts — "
                "encrypted data (webhook secrets, LLM API keys) becomes "
                "unreadable after each process restart. "
                "Set FIELD_ENCRYPTION_KEY in the staging environment. "
                "Generate with: python3 -c \"from cryptography.fernet import "
                "Fernet; print(Fernet.generate_key().decode())\""
            )
        if not is_dev:
            raise RuntimeError(
                "FIELD_ENCRYPTION_KEY not set and IS_DEVELOPMENT not 'true'. "
                "Refusing to use ephemeral key — set FIELD_ENCRYPTION_KEY or "
                "set IS_DEVELOPMENT=true to acknowledge dev mode."
            )
        generated = Fernet.generate_key().decode()
        logger.warning(
            "FIELD_ENCRYPTION_KEY not set, IS_DEVELOPMENT=true — generated "
            "EPHEMERAL key. Encrypted values WILL NOT survive process "
            "restart. For persistent dev encryption, add to .env: "
            "FIELD_ENCRYPTION_KEY=%s",
            generated,
        )
        key = generated

    _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    """Encrypt plaintext string. Returns base64-encoded ciphertext."""
    if not plaintext:
        return plaintext
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt ciphertext. Raises DecryptionError on failure (canonical fail-loud).

    REGRA 4 (CLAUDE.md): NEVER returns ciphertext on failure — that's a
    silent fallback that masks broken encryption.

    For opt-in soft-fail (returns None on error), use safe_decrypt_value().
    """
    if not ciphertext:
        return ciphertext
    try:
        fernet = _get_fernet()
        return fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise DecryptionError(
            "Decryption failed (InvalidToken). Possible causes: "
            "(a) key mismatch — FIELD_ENCRYPTION_KEY differs from key "
            "used to encrypt; (b) ciphertext corrupted; "
            "(c) ciphertext was actually plaintext. Investigate before silencing."
        ) from e
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {e}") from e


def safe_decrypt_value(ciphertext: str) -> str | None:
    """
    Decrypt ciphertext, returning None on failure (with WARN log).

    Use ONLY when caller has a legitimate soft-fail path (e.g. legacy
    rows that may be plaintext from pre-encryption era). Logs the failure
    so it's still visible in observability — never silent.

    For canonical fail-loud behavior, use decrypt_value().
    """
    if not ciphertext:
        return ciphertext
    try:
        return decrypt_value(ciphertext)
    except DecryptionError as e:
        logger.warning("safe_decrypt_value failed (returning None): %s", e)
        return None
