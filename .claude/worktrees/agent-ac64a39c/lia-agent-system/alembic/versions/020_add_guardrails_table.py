"""Add guardrails table for persistent, DB-managed agent behavior rules.

Revision ID: 020_add_guardrails_table
Revises: 019_add_shared_searches_tables
Create Date: 2026-03-04

Fase 3 — Guardrails no Banco:
Regras de comportamento de agentes editáveis em produção via admin,
sem necessidade de deploy. Suporta regras globais (company_id=None)
e por tenant, por domínio e por tool específica.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "020_add_guardrails_table"
down_revision = "019_add_shared_searches_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "guardrails",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("level", sa.String(20), nullable=False, server_default="primary"),
        sa.Column("domain", sa.String(100), nullable=True),
        sa.Column("node", sa.String(100), nullable=True),
        sa.Column("tool", sa.String(200), nullable=True),
        sa.Column("rule", sa.Text, nullable=False),
        sa.Column("blocking_message", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("company_id", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=False, server_default="system"),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Índices para queries frequentes
    op.create_index("ix_guardrails_is_active", "guardrails", ["is_active"])
    op.create_index("ix_guardrails_domain", "guardrails", ["domain"])
    op.create_index("ix_guardrails_company_id", "guardrails", ["company_id"])
    op.create_index("ix_guardrails_level", "guardrails", ["level"])


def downgrade():
    op.drop_index("ix_guardrails_level", table_name="guardrails")
    op.drop_index("ix_guardrails_company_id", table_name="guardrails")
    op.drop_index("ix_guardrails_domain", table_name="guardrails")
    op.drop_index("ix_guardrails_is_active", table_name="guardrails")
    op.drop_table("guardrails")
