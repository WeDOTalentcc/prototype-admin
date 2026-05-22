"""PII crypto helper canonical — wraps ``app.shared.encryption`` for LGPD-sensitive
scalar PII fields (CPF, CNPJ, RG, passport, taxId).

LGPD context (Wave 4 audit 2026-05-22)
──────────────────────────────────────
``PaymentMethod.billing_document`` historically stored CPF/CNPJ as a plaintext
``VARCHAR(20)`` column. Per LGPD Art. 5 II this is "dado pessoal" — CPF
is the canonical Brazilian personal identifier. Plaintext storage breaks
LGPD Art. 46 ("medidas técnicas de segurança aptas a proteger os dados
pessoais") and ADR-006 (secrets at rest).

This helper plus migration 169_encrypt_billing_document.py move all
billing_document values to ``billing_document_encrypted`` (Text, Fernet
base64 ciphertext). The legacy column is kept temporarily as
``billing_document_legacy`` (nullable) during backfill, then set to NULL
once each row migrates.

Pattern: REUSES canonical ``app.shared.encryption.{encrypt_value,
decrypt_value}`` — DO NOT introduce a separate Fernet key for PII. ONE key
for all at-rest secrets in this service (FIELD_ENCRYPTION_KEY).

Difference from ``credentials_crypto``
──────────────────────────────────────
``credentials_crypto`` encrypts JSON dicts (multi-key integration secrets).
``pii_crypto`` encrypts scalar strings (single PII value). Both share the
same Fernet key.

For dict-shaped PII (e.g., a future ``billing_address`` dict including CEP
+ street + complement) use ``credentials_crypto`` instead.

NEVER logs the plaintext value (LGPD Art. 7 + Art. 46).
"""
from __future__ import annotations

import logging

from app.shared.encryption import DecryptionError, decrypt_value, encrypt_value

logger = logging.getLogger(__name__)


class PIIEncryptionError(RuntimeError):
    """Raised when scalar PII cannot be encrypted/decrypted.

    Common causes:
    - FIELD_ENCRYPTION_KEY not set in production
    - Key rotated without re-encrypting rows
    - Ciphertext corrupted
    - Legacy plaintext row consumed via the wrong code path
    """


def encrypt_pii(value: str | None) -> str | None:
    """Encrypt a scalar PII string (CPF, CNPJ, RG, etc.).

    Returns base64-encoded Fernet ciphertext, or ``None`` if input is
    ``None`` or empty (whitespace-only treated as empty).

    NEVER logs the plaintext value (LGPD).

    Raises
    ------
    PIIEncryptionError
        If ``FIELD_ENCRYPTION_KEY`` is missing in production.
    """
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return encrypt_value(stripped)
    except Exception as exc:
        # Do NOT include the plaintext value in logs (LGPD).
        logger.error("PII encryption failed: %s", exc)
        raise PIIEncryptionError(
            f"PII encryption failed: {exc}"
        ) from exc


def decrypt_pii(ciphertext: str | None) -> str | None:
    """Decrypt a scalar PII ciphertext.

    Returns the plaintext value, or ``None`` if ciphertext is ``None`` or
    empty.

    NEVER logs the decrypted value (LGPD).

    Raises
    ------
    PIIEncryptionError
        Key rotation, ciphertext corruption, or legacy plaintext consumed
        via the encrypted path.
    """
    if not ciphertext:
        return None
    try:
        return decrypt_value(ciphertext)
    except DecryptionError as exc:
        # Do NOT include the ciphertext in logs (it is a secret).
        logger.error("PII decryption failed: %s", exc)
        raise PIIEncryptionError(
            "PII decryption failed — possible key rotation, "
            "ciphertext corruption, or legacy plaintext row consumed "
            "via the encrypted path. Investigate before silencing."
        ) from exc


def mask_document_for_log(value: str | None) -> str:
    """Return a masked CPF/CNPJ safe for logging/UI.

    Examples:
        >>> mask_document_for_log("123.456.789-00")
        '***.456.789-**'
        >>> mask_document_for_log("12345678900")
        '***456789**'
        >>> mask_document_for_log("12.345.678/0001-00")  # CNPJ
        '**.345.678/0001-**'

    Returns ``"***"`` for None/empty/short values.
    Use this when you MUST surface a partial identifier (e.g., user-facing
    confirmation prompt) — never log the full plaintext.
    """
    if not value:
        return "***"
    stripped = value.strip()
    if len(stripped) < 6:
        return "***"
    # Mask first 3 and last 2 chars; leave middle visible for ops.
    return "***" + stripped[3:-2] + "**"
