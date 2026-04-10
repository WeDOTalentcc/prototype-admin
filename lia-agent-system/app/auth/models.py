"""
User model for authentication.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum, StrEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, LargeBinary, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.core.database import Base
from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin


class UserRole(StrEnum):
    """User role enumeration."""
    admin = "admin"
    recruiter = "recruiter"
    viewer = "viewer"


class User(EncryptedFieldMixin, Base):
    """User model for authentication.

    PII encryption (post-migration 060, via EncryptedFieldMixin):
      - Every write to ``email`` sets ``email_encrypted`` (Fernet bytes), ``email_hash``
        (SHA-256 hex, unique index), and NULLS the plaintext ``email`` column.
      - Pre-migration rows retain plaintext email until pii.backfill_encrypt_existing runs.
      - Uniqueness is enforced on ``email_hash`` (not plaintext email).
      - Lookups: OR(email_hash == hash, email == plaintext) during transition period.
    """

    __tablename__ = "users"

    # _pii_encrypt_fields: (raw_attr, enc_attr, hash_attr)
    # "_email_raw" → hybrid_property "email" registered by EncryptedFieldMixin
    _pii_encrypt_fields = [
        ("_email_raw", "_email_encrypted", "email_hash"),
    ]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Raw DB column for email — NULL for new writes (post-migration 060).
    # Pre-migration rows retain plaintext until pii.backfill_encrypt_existing completes.
    # DB column name is "email" for schema backward compat. Access via hybrid "email".
    _email_raw = Column("email", String(255), nullable=True, index=True)
    # PII-encrypted backing columns (added by migration 060)
    _email_encrypted = Column("email_encrypted", LargeBinary, nullable=True)
    email_hash = Column(String(64), nullable=True, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    company_id = Column(String(255), nullable=True, index=True, default=None)
    is_active = Column(Boolean, default=True, nullable=False)
    permissions = Column(ARRAY(String), default=[], nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_token_expires = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_token_expires = Column(DateTime, nullable=True)
    invitation_token = Column(String(255), nullable=True)
    invitation_sent_at = Column(DateTime, nullable=True)
    
    notification_preferences = Column(JSONB, nullable=True, default=dict, server_default="{}")

    avatar_url = Column(String(1024), nullable=True)

    azure_ad_object_id = Column(String(255), nullable=True, index=True)
    workos_id = Column(String(255), unique=True, nullable=True, index=True)
    workos_directory_id = Column(String(255), nullable=True, index=True)
    workos_organization_id = Column(String(255), nullable=True, index=True)
    sso_provider = Column(String(100), nullable=True)
    is_scim_managed = Column(Boolean, default=False, nullable=False)
    last_sso_login_at = Column(DateTime, nullable=True)
    
    def get(self, key: str, default=None):
        """Compatibility bridge: 100+ endpoints use current_user.get() expecting dict-like access.
        Provides attribute lookup with key aliasing (user_id/sub → id)."""
        attr_map = {
            "user_id": "id",
            "sub": "id",
            "id": "id",
        }
        attr = attr_map.get(key, key)
        val = getattr(self, attr, default)
        if val is None:
            return default
        return val

    def can_access_company(self, company_id: str) -> bool:
        """Check if user can access the given company."""
        if self.role == UserRole.admin:
            return True
        return self.company_id == company_id
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, company={self.company_id})>"
