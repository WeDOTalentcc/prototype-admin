"""
EncryptedFieldMixin — Fernet at-rest encryption for PII fields.

Provides transparent encryption/decryption of sensitive string fields
(CPF, email) using AES-128-CBC via the `cryptography` library (Fernet).

Key management
--------------
The encryption key is read from FIELD_ENCRYPTION_KEY env variable, which
must be a URL-safe base-64 encoded 32-byte Fernet key.  Generate with:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Design: transparent encryption via hybrid_property
----------------------------------------------------
Each PII field (e.g. "email") maps to:
  _email_raw      (Column String, nullable=True, DB column "email")
                   — The actual DB storage column. NULL for new writes (post-migration).
                     May have plaintext for pre-migration rows (backfill pending).
  _email_encrypted (Column LargeBinary, nullable=True, DB column "email_encrypted")
                   — Fernet-encrypted bytes for all new writes.
  email_hash      (Column String(64), nullable=True, DB column "email_hash")
                   — SHA-256 deterministic hash for indexed lookup.

The public `email` attribute is a SQLAlchemy hybrid_property (registered by the mixin):
  - Instance GET: returns `_email_raw` if non-None (pre-migration row), else
                  decrypts `_email_encrypted` → always returns plaintext string.
  - Instance SET: encrypts → `_email_encrypted`; hashes → `email_hash`;
                  sets `_email_raw = None` (via SQLAlchemy ORM column setter,
                  bypassing the hybrid setter) → DB stores NULL, not plaintext.
  - Class-level SQL expression: returns `cls._email_raw` for ORM query compat.

This achieves:
  - DB column `_email_raw` always NULL for new writes → PII not persisted in plaintext.
  - `obj.email` always returns decrypted plaintext → fully transparent to callers.
  - Auth, JWT, email services, WorkOS SSO, API responses — zero changes needed.

Model column convention for each encrypted field (plaintext_col, enc_col, hash_col):
  - Use `_email_raw` as the Column attribute name, mapped to DB column "email"
    (via Column("email", ...)) — this keeps the DB schema unchanged.
  - Declare `email` as the hybrid_property name (populated by this mixin).

Security posture
----------------
- FAIL CLOSED: if FIELD_ENCRYPTION_KEY is not set, raises EncryptionKeyMissingError.
- Exception: IS_DEVELOPMENT=true disables enforcement for local dev.
- Transition risk: pre-migration rows have plaintext in `_email_raw` DB column
  until pii.backfill_encrypt_existing completes (Phase 2).
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

_IS_DEVELOPMENT = os.environ.get("IS_DEVELOPMENT", "").lower() in ("true", "1", "yes")


class EncryptionKeyMissingError(RuntimeError):
    """Raised when FIELD_ENCRYPTION_KEY is not set in production mode."""


def _get_fernet():
    """
    Return a Fernet instance using FIELD_ENCRYPTION_KEY env var.

    Raises EncryptionKeyMissingError when the key is absent and
    IS_DEVELOPMENT is not set.
    """
    from cryptography.fernet import Fernet

    key = os.environ.get("FIELD_ENCRYPTION_KEY")
    if not key:
        if _IS_DEVELOPMENT:
            logger.warning(
                "FIELD_ENCRYPTION_KEY not set — PII fields will NOT be encrypted "
                "(IS_DEVELOPMENT=true). Set FIELD_ENCRYPTION_KEY for production."
            )
            return None
        raise EncryptionKeyMissingError(
            "FIELD_ENCRYPTION_KEY environment variable is not set. "
            "PII encryption cannot proceed. Configure this key before storing sensitive data."
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        raise EncryptionKeyMissingError(f"Invalid FIELD_ENCRYPTION_KEY: {exc}") from exc


def _encrypt(value: str | None) -> bytes | None:
    """
    Encrypt a plaintext string value.

    Returns encrypted bytes, or None if value is None.
    Raises EncryptionKeyMissingError in production mode without a key.
    In development mode (IS_DEVELOPMENT=true) without a key, returns
    raw UTF-8 bytes (unencrypted, for dev only).
    """
    if value is None:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return value.encode("utf-8")
    return fernet.encrypt(value.encode("utf-8"))


def _decrypt(token: bytes | None) -> str | None:
    """
    Decrypt Fernet token to plaintext string.

    Returns decrypted string, or None if token is None.
    Raises EncryptionKeyMissingError in production mode without a key.
    """
    if token is None:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return token.decode("utf-8") if isinstance(token, bytes) else token
    try:
        return fernet.decrypt(token).decode("utf-8")
    except Exception as exc:
        logger.warning("Decryption failed (returning None): %s", exc)
        return None


def _sha256_hash(value: str | None) -> str | None:
    """
    One-way SHA-256 hash for deterministic lookup (email_hash).
    Lower-cased and stripped before hashing for consistency.
    """
    if value is None:
        return None
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def _normalize_cpf_digits(value: str | None) -> str:
    """CPF canonical form for hashing: digits only ('123.456.789-00' -> '12345678900')."""
    return re.sub(r"\D", "", value or "")


def _normalize_phone_digits(value: str | None) -> str:
    """Phone canonical form for hashing: digits only, strip BR country code (55) and
    leading zeros. Best-effort: '+55 (11) 99999-9999' / '11999999999' -> '11999999999'.
    NOTE: hash exact-match is fragile for phones (DDD/9-digit/country variance); CPF
    and email are deterministic. Documented limitation (ADR-LGPD-002 resolve-then-strip)."""
    d = re.sub(r"\D", "", value or "")
    if len(d) > 11 and d.startswith("55"):
        d = d[2:]
    return d.lstrip("0")


# Per-hash-attr normalizer. email_hash uses the default strip().lower() (_sha256_hash).
_HASH_NORMALIZERS = {
    "cpf_hash": _normalize_cpf_digits,
    "phone_hash": _normalize_phone_digits,
}


def _sha256_hash_for_attr(hash_attr: str | None, value: str | None) -> str | None:
    """SHA-256 hash for a specific hash column, applying per-field normalization.

    cpf_hash/phone_hash normalize to a digits-only canonical form BEFORE hashing so a
    formatted value typed by the recruiter ('123.456.789-00') matches the stored hash.
    Other hash columns fall back to _sha256_hash (strip+lower) — preserves email_hash."""
    if value is None:
        return None
    norm = _HASH_NORMALIZERS.get(hash_attr or "")
    if norm is not None:
        canon = norm(value)
        if not canon:
            return None
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return _sha256_hash(value)


class EncryptedField:
    """
    Python descriptor that transparently encrypts/decrypts a SQLAlchemy column.

    The backing column stores bytes (LargeBinary).
    The descriptor exposes a str interface with transparent Fernet encryption.

    Parameters
    ----------
    storage_attr : str
        Name of the underlying SQLAlchemy column attribute (stores bytes).
    hash_attr : str | None
        If given, the descriptor also updates this attribute with a SHA-256
        hash of the plaintext on every write — used for indexed lookups.
    """

    def __init__(self, storage_attr: str, hash_attr: str | None = None):
        self.storage_attr = storage_attr
        self.hash_attr = hash_attr

    def __set_name__(self, owner: type, name: str) -> None:
        self.public_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> str | None:
        if obj is None:
            return self  # type: ignore[return-value]
        raw = getattr(obj, self.storage_attr, None)
        return _decrypt(raw)

    def __set__(self, obj: Any, value: str | None) -> None:
        setattr(obj, self.storage_attr, _encrypt(value))
        if self.hash_attr:
            setattr(obj, self.hash_attr, _sha256_hash_for_attr(self.hash_attr, value))


class EncryptedFieldMixin:
    """
    Mixin for SQLAlchemy models with transparent at-rest PII encryption.

    Each field spec in `_pii_encrypt_fields`:
        (raw_attr, enc_attr, hash_attr)
    where:
        raw_attr  = Python attribute name of the underlying ORM column (e.g. "_email_raw")
        enc_attr  = Python attribute name of the encrypted LargeBinary column
        hash_attr = Python attribute name of the SHA-256 hash column (or None)

    The mixin registers a hybrid_property with the public field name (derived from
    raw_attr by stripping the leading "_" and trailing "_raw" suffix, e.g. "email").

    Write path (obj.email = "x@y.com"):
      hybrid setter → _email_encrypted = encrypt(value); email_hash = sha256(value);
                    → _email_raw = None (DB column NULL, no plaintext stored)

    Read path (obj.email → "x@y.com"):
      hybrid getter → if _email_raw is not None: return _email_raw (pre-migration row)
                    → else: return decrypt(_email_encrypted)

    SQL expression (User.email == "x@y.com"):
      hybrid expression → User._email_raw (ORM column for SQL-level filtering)
      Repositories also use OR(email_hash == hash, _email_raw == plaintext).

    Model column declarations:
        _email_raw       = Column("email", String(255), nullable=True, index=True)
        _email_encrypted = Column("email_encrypted", LargeBinary, nullable=True)
        email_hash       = Column("email_hash", String(64), nullable=True, index=True)
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        pii_fields: list[tuple[str, str, str | None]] = getattr(cls, "_pii_encrypt_fields", [])
        if not pii_fields:
            return

        from sqlalchemy.ext.hybrid import hybrid_property

        for raw_attr, enc_attr, hash_attr in pii_fields:
            # Derive public property name: "_email_raw" → "email", "_cpf_raw" → "cpf"
            pub_name = raw_attr.lstrip("_").removesuffix("_raw")

            _raw = raw_attr
            _enc = enc_attr
            _hash = hash_attr

            def _make_hybrid(raw: str, enc: str, h: str | None):
                @hybrid_property
                def _prop(self) -> str | None:
                    raw_val = getattr(self, raw, None)
                    if raw_val is not None:
                        return raw_val  # Pre-migration row: return DB plaintext
                    return _decrypt(getattr(self, enc, None))

                @_prop.setter
                def _prop(self, value: str | None) -> None:
                    # Set encrypted backing column and hash
                    setattr(self, enc, _encrypt(value))
                    if h:
                        setattr(self, h, _sha256_hash_for_attr(h, value))
                    # Null the raw/plaintext column via the ORM column attribute
                    # (using the underlying column name, not the hybrid property)
                    setattr(self, raw, None)

                @_prop.expression
                def _prop(cls_):
                    return getattr(cls_, raw)

                return _prop

            setattr(cls, pub_name, _make_hybrid(_raw, _enc, _hash))

    @classmethod
    def email_hash_for(cls, email: str | None) -> str | None:
        """Return the SHA-256 hash of a plaintext email for indexed lookup."""
        return _sha256_hash(email)

    @classmethod
    def cpf_hash_for(cls, cpf: str | None) -> str | None:
        """SHA-256 hash of a CPF (digits-only normalized) for indexed lookup."""
        return _sha256_hash_for_attr("cpf_hash", cpf)

    @classmethod
    def phone_hash_for(cls, phone: str | None) -> str | None:
        """SHA-256 hash of a phone (digits-only, BR-normalized) for indexed lookup."""
        return _sha256_hash_for_attr("phone_hash", phone)
