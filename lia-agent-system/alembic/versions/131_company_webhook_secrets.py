"""Add company_webhook_secrets table for per-tenant webhook HMAC secrets (Task #1146).

Revision ID: 131_company_webhook_secrets
Revises: 130_culture_profile_defaults_not_null
Create Date: 2026-05-16

Closes the highest-value cross-tenant webhook gap identified in T-1129 §3.2:
the 6 external webhooks (Teams, OpenMic, Merge, Twilio, WhatsApp, Mailgun)
share a SINGLE global HMAC secret per provider. Compromising the secret
unlocks every tenant.

This migration introduces ``company_webhook_secrets`` so that each
``(company_id, provider)`` pair owns its own encrypted secret. The
``app.shared.security.webhook_ownership.verify_webhook_owner`` helper
prefers the per-tenant secret and falls back to the global one during a
90-day dual-validate window (see ``docs/runbooks/webhook_secret_rotation.md``).

Pattern mirrors 119_rls_t1_lgpd_pii (UUID company_id with ``::text`` cast):
- ENABLE + FORCE ROW LEVEL SECURITY
- 4 policies (select/insert/update/delete) gated on
  ``company_id::text = app_current_company_id()``
- ``secret_encrypted`` stores Fernet ciphertext (key shared with
  REDIS_ENCRYPTION_KEY via ``RedisCrypto``).

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "131_company_webhook_secrets"
down_revision = "130_culture_profile_defaults_not_null"
depends_on = None

TABLE = "company_webhook_secrets"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("secret_encrypted", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "rotated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "company_id", "provider", name="uq_company_webhook_secrets_tenant_provider"
        ),
        sa.CheckConstraint(
            "provider IN ('teams','openmic','merge','twilio','whatsapp','mailgun')",
            name="ck_company_webhook_secrets_provider",
        ),
        sa.CheckConstraint(
            "status IN ('active','rotating','revoked')",
            name="ck_company_webhook_secrets_status",
        ),
    )

    op.create_index(
        "idx_company_webhook_secrets_provider_status",
        TABLE,
        ["provider", "status"],
    )

    # RLS — same pattern as 119 (UUID company_id w/ ::text cast)
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY;")

    for op_kind in ("select", "insert", "update", "delete"):
        op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_{op_kind} ON {TABLE};")

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_select ON {TABLE}
            FOR SELECT
            USING (company_id::text = app_current_company_id());
    """)
    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_insert ON {TABLE}
            FOR INSERT
            WITH CHECK (company_id::text = app_current_company_id());
    """)
    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_update ON {TABLE}
            FOR UPDATE
            USING (company_id::text = app_current_company_id())
            WITH CHECK (company_id::text = app_current_company_id());
    """)
    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_delete ON {TABLE}
            FOR DELETE
            USING (company_id::text = app_current_company_id());
    """)


def downgrade() -> None:
    for op_kind in ("select", "insert", "update", "delete"):
        op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_{op_kind} ON {TABLE};")
    op.execute(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY;")
    op.drop_index("idx_company_webhook_secrets_provider_status", table_name=TABLE)
    op.drop_table(TABLE)
