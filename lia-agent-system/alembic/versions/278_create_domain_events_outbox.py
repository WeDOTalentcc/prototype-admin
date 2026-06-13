"""278 — create domain_events_outbox table

Revision ID: 278_create_domain_events_outbox
Revises: 277_seed_voice_agent_studio
Create Date: 2026-06-13

Guide computacional Sprint E (harness-engineering):
  INSERT atomico garante entrega at-least-once de eventos criticos.
  Diferente de ai_consumption_outbox (billing): serve TODOS os dominios.

Indexes:
  - ix_outbox_status: leitura do worker de drain
  - ix_outbox_event_type: analytics e monitoramento
  - ix_outbox_company_id: isolamento multi-tenant
  - ix_outbox_correlation: rastreio distributed tracing
  - ix_outbox_pending: partial index (status=pending) para performance do drain worker
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "278_create_domain_events_outbox"
down_revision = "277_seed_voice_agent_studio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domain_events_outbox",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id",       sa.String(80),  nullable=False),
        sa.Column("event_type",     sa.String(100), nullable=False),
        sa.Column("company_id",     sa.String(255), nullable=False),
        sa.Column("payload",        JSONB,           nullable=False),
        sa.Column("status",         sa.String(20),  nullable=False, server_default="pending"),
        sa.Column("correlation_id", sa.String(80),  nullable=True),
        sa.Column("source_api",     sa.String(80),  nullable=True),
        sa.Column("version",        sa.String(10),  nullable=False, server_default="1.0"),
        sa.Column("created_at",     sa.DateTime,    nullable=False, server_default=sa.text("NOW()")),
        sa.Column("delivered_at",   sa.DateTime,    nullable=True),
        sa.Column("attempts",       sa.Integer,     nullable=False, server_default="0"),
        sa.Column("last_error",     sa.Text,        nullable=True),
        sa.UniqueConstraint("event_id", name="uq_domain_events_outbox_event_id"),
    )
    op.create_index("ix_outbox_status",      "domain_events_outbox", ["status"])
    op.create_index("ix_outbox_event_type",  "domain_events_outbox", ["event_type"])
    op.create_index("ix_outbox_company_id",  "domain_events_outbox", ["company_id"])
    op.create_index("ix_outbox_correlation", "domain_events_outbox", ["correlation_id"])
    op.create_index(
        "ix_outbox_pending",
        "domain_events_outbox",
        ["status", "created_at"],
        postgresql_where=sa.text("status = pending"),
    )


def downgrade() -> None:
    for idx in ["ix_outbox_pending", "ix_outbox_correlation", "ix_outbox_company_id",
                "ix_outbox_event_type", "ix_outbox_status"]:
        op.drop_index(idx, "domain_events_outbox")
    op.drop_table("domain_events_outbox")
