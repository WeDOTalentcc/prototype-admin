"""
Credentials crypto helper canonical — wraps app.shared.encryption for IntegrationConnection.

Provides dict↔ciphertext helpers using the canonical FIELD_ENCRYPTION_KEY
(single key for all at-rest encryption in lia-agent-system, per
app/shared/encryption/__init__.py).

LGPD context (P0.D — Wave 3 audit 2026-05-21)
─────────────────────────────────────────────
``IntegrationConnection.credentials`` historically stored API keys / OAuth
tokens / webhook secrets as a JSON dict in plaintext. This is a direct LGPD
Art. 46 violation (medidas técnicas de segurança) and breaks ADR-006
(secrets at rest).

This helper plus migration 168_encrypt_integration_credentials.py move all
credentials to ``credentials_encrypted`` (Text column, Fernet base64
ciphertext of the JSON-serialized dict). The legacy ``credentials`` JSON
column is kept temporarily as ``credentials_legacy`` (nullable) during
backfill, then set to NULL once each row migrates.

Pattern: REUSES canonical app.shared.encryption.{encrypt_value,decrypt_value}
— DO NOT introduce a separate Fernet key for credentials. ONE key for all
at-rest secrets in this service (FIELD_ENCRYPTION_KEY).
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.shared.encryption import DecryptionError, decrypt_value, encrypt_value

logger = logging.getLogger(__name__)


class CredentialsEncryptionError(RuntimeError):
    """Raised when credentials cannot be encrypted/decrypted.

    Common causes:
    - FIELD_ENCRYPTION_KEY not set in production
    - Key rotated without re-encrypting rows
    - Ciphertext corrupted
    - Legacy plaintext row consumed via the wrong code path
    """


def encrypt_credentials(credentials: dict[str, Any] | None) -> str | None:
    """
    Encrypt a credentials dict.

    Returns base64-encoded Fernet ciphertext, or None if input is None/empty.
    NEVER logs the credentials themselves (LGPD).

    Raises
    ------
    CredentialsEncryptionError
        If FIELD_ENCRYPTION_KEY is missing in production, or if the dict
        is not JSON-serializable.
    """
    if not credentials:
        return None
    try:
        serialized = json.dumps(credentials, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        # Do NOT include the dict content in logs (LGPD)
        logger.error(
            "credentials JSON serialization failed (keys=%s): %s",
            list(credentials.keys()),
            exc,
        )
        raise CredentialsEncryptionError(
            f"credentials dict is not JSON-serializable: {exc}"
        ) from exc

    try:
        return encrypt_value(serialized)
    except Exception as exc:
        logger.error("credentials encryption failed: %s", exc)
        raise CredentialsEncryptionError(
            f"credentials encryption failed: {exc}"
        ) from exc


def decrypt_credentials(ciphertext: str | None) -> dict[str, Any]:
    """
    Decrypt credentials ciphertext to a dict.

    Returns the dict, or an empty dict if ciphertext is None/empty.
    NEVER logs the decrypted credentials (LGPD).

    Raises
    ------
    CredentialsEncryptionError
        Possible causes: key rotation without re-encrypt, ciphertext
        corruption, or the value was legacy plaintext consumed via
        the wrong code path.
    """
    if not ciphertext:
        return {}
    try:
        plaintext = decrypt_value(ciphertext)
    except DecryptionError as exc:
        # Do NOT include the ciphertext in logs (it is a secret).
        logger.error("credentials decryption failed: %s", exc)
        raise CredentialsEncryptionError(
            "Credentials decryption failed — possible key rotation, "
            "ciphertext corruption, or legacy plaintext row consumed "
            "via the encrypted path. Investigate before silencing."
        ) from exc

    try:
        return json.loads(plaintext)
    except (TypeError, ValueError) as exc:
        logger.error("credentials JSON deserialization failed: %s", exc)
        raise CredentialsEncryptionError(
            f"decrypted credentials is not valid JSON: {exc}"
        ) from exc
