"""
User model for authentication.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum, StrEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, LargeBinary, String, ForeignKey, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import validates

from app.core.database import Base
from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin


# Whitelist of legacy non-UUID company_id values still tolerated read-only
# during the migration window. Writes go through ``_validate_company_id``
# below — adding a new entry is a conscious, audited decision.
_LEGACY_NON_UUID_COMPANY_IDS_ALLOWED: frozenset[str] = frozenset()


class UserRole(StrEnum):
    """User role enumeration.

    NOTE on tenant vs. WeDOTalent scope (audit 2026-05-21, P1-7/E4-prep):

    - ``admin`` / ``recruiter`` / ``viewer`` are TENANT roles. A user with
      ``admin`` administers ONE customer organization (e.g. Acme Corp).
    - ``wedotalent_admin`` is the WeDOTalent-staff role. Reserved for the
      WeDOTalent team (Anderson + ops) who operate the platform across
      ALL tenants. Only this role can edit per-tenant YAML overrides at
      ``/admin/prompts/tenant-overrides/*`` and other cross-tenant
      surfaces. Grant via the user-management admin UI in
      admin2.wedotalent.cc — NEVER assign to a customer-end user.
    """
    admin = "admin"
    manager = "manager"  # RBAC Sprint 0 (2026-05-25): consolida ClientUserRole.MANAGER (tenant-level) com canonical UserRole.
    recruiter = "recruiter"
    viewer = "viewer"
    wedotalent_admin = "wedotalent_admin"


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

    # RBAC Sprint 2 (2026-05-25): department + manager FK for scope filter.
    # Backward compat soft launch: NULL = legacy/tenant-wide (no filter enforcement).
    # Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # RBAC Sprint 5 (2026-05-25): financial PII privilege grant — LGPD Art. 6 III minimização.
    # Default False (no one sees salary). Admin grants explicit per-user via UI.
    # Bootstrap: migration 204 backfilled True for role='admin'.
    can_view_salary = Column(Boolean, default=False, nullable=False, server_default=text("false"))

    @validates("company_id")
    def _validate_company_id(self, _key: str, value):  # noqa: ANN001
        """Fail-LOUD on non-UUID writes to ``company_id``.

        Task #1043 PR-D. The original T-E regression was caused by writing
        the literal string ``"demo_company"`` to ``users.company_id``,
        which then failed to bind to the canonical Demo Company row
        (UUID-keyed). This validator runs on every assignment and rejects
        any non-UUID, non-null value (except an explicit, empty
        whitelist for emergency rollback).
        """
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        if not isinstance(value, str):
            raise TypeError(
                f"User.company_id must be str | UUID | None, got {type(value).__name__}"
            )
        candidate = value.strip()
        if not candidate:
            return None
        if candidate in _LEGACY_NON_UUID_COMPANY_IDS_ALLOWED:
            return candidate
        try:
            uuid.UUID(candidate)
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                f"User.company_id must be a UUID v4 string (got {candidate!r}). "
                f"Writing legacy literals like 'demo_company' caused the T-E "
                f"regression (Task #1043). If you need to bypass during a "
                f"controlled migration, add the value to "
                f"_LEGACY_NON_UUID_COMPANY_IDS_ALLOWED with a code review."
            ) from exc
        return candidate
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
        """Check if user can access the given company.

        Cross-tenant access rules:
        - ``wedotalent_admin`` (WeDOTalent staff) → True for any company_id.
          Operate platform across ALL tenants (per UserRole docstring).
        - ``admin`` (tenant admin) → CURRENTLY also returns True for any
          company_id. This is a TRANSITIONAL behavior: historically ``admin``
          was the only WeDOTalent-staff role; ``wedotalent_admin`` was
          introduced later but staff users were not migrated. Flipping ``admin``
          now would lock WeDOTalent staff out of legit cross-tenant ops.

        Onda 1.1 fix (2026-05-23): adicionado branch ``wedotalent_admin`` —
        antes ele caia no ``self.company_id == company_id`` e era negado
        em endpoints cross-tenant (Recovery #3 wsi/reports.py descobriu).

        TODO follow-up (Onda 1.x ou separado): migrar usuarios WeDOTalent-staff
        de role ``admin`` → ``wedotalent_admin`` no banco, depois remover o
        branch ``admin`` desta funcao. Sem essa migracao, tenant admins (admin
        de Acme Corp) tem acesso cross-tenant indevido. ``assert_resource_
        ownership`` ja loga warning quando ``admin`` cruza tenant (defense-in-
        depth temporario).
        """
        if self.role in (UserRole.admin, UserRole.wedotalent_admin):
            return True
        return self.company_id == company_id
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, company={self.company_id})>"
