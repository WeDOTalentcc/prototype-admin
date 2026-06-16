"""Add agent_ragas_evaluations table — ACH-027

Revision ID: 041
Revises: 040
Create Date: 2026-03-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "041"
down_revision = "040_add_rls_multi_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_ragas_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(255), nullable=False, index=True),
        sa.Column("domain", sa.String(100), nullable=False, index=True),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("faithfulness", sa.Float, nullable=True),
        sa.Column("answer_relevancy", sa.Float, nullable=True),
        sa.Column("context_precision", sa.Float, nullable=True),
        sa.Column("context_recall", sa.Float, nullable=True),
        sa.Column("overall_score", sa.Float, nullable=True, index=True),
        sa.Column(
            "evaluated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
            index=True,
        ),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
    )

    # Índice composto para queries de sumário por domínio + período
    op.create_index(
        "ix_ragas_domain_date",
        "agent_ragas_evaluations",
        ["domain", "evaluated_at"],
    )

    # Retenção automática: registros com mais de 90 dias serão limpos pelo LGPD cleanup
    # (agent_ragas_evaluations é dado operacional, não PII — retenção menor aceitável)


def downgrade() -> None:
    op.drop_index("ix_ragas_domain_date", table_name="agent_ragas_evaluations")
    op.drop_table("agent_ragas_evaluations")
