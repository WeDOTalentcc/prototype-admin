"""
CompanyWebhookSecret — per-tenant HMAC secret for inbound webhooks.

Backs the 90-day dual-validate window introduced in Task #1146 (Multi-tenant
Ownership — Webhook ownership validators). Each row stores a Fernet-encrypted
secret for one ``(company_id, provider)`` pair. ``app.shared.security.
webhook_ownership.verify_webhook_owner`` reads/writes via raw SQL with the
tenant-scoped session so it inherits RLS protection from migration
``131_company_webhook_secrets``.

Plaintext secrets MUST NEVER reach this model. The helper encrypts via
``RedisCrypto`` (same Fernet key as ``REDIS_ENCRYPTION_KEY``) before insert
and decrypts on read.
"""
from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from lia_config.database import Base


class CompanyWebhookSecret(Base):
    """Encrypted per-tenant webhook secret.

    Status lifecycle:
        active   → currently valid for HMAC verification.
        rotating → both old (global) and new (this row) accepted (90d window).
        revoked  → ignored by ``verify_webhook_owner`` (compromise / churn).
    """

    __tablename__ = "company_webhook_secrets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    secret_encrypted = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rotated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "provider", name="uq_company_webhook_secrets_tenant_provider"),
        CheckConstraint(
            "provider IN ('teams','openmic','merge','twilio','whatsapp','mailgun')",
            name="ck_company_webhook_secrets_provider",
        ),
        CheckConstraint(
            "status IN ('active','rotating','revoked')",
            name="ck_company_webhook_secrets_status",
        ),
        Index("idx_company_webhook_secrets_provider_status", "provider", "status"),
    {"extend_existing": True}, )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<CompanyWebhookSecret company={self.company_id} "
            f"provider={self.provider} status={self.status}>"
        )
