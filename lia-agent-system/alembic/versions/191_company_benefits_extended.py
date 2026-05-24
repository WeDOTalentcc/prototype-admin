"""191 — company_benefits: filiais, validade, carência; company_benefit_history

Mudanças:
1. company_benefits: adicionar colunas subsidiaries (JSONB), valid_from, valid_until,
   review_frequency_months, next_review_date, provider_cnpj
2. Criar tabela company_benefit_history (auditoria de alterações)

Revision ID: 191_company_benefits_extended
Revises: 190_suggestion_clicks_feedback_check
Create Date: 2026-05-24
"""
revision = "191_company_benefits_extended"
down_revision = "190_suggestion_clicks_feedback_check"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    # Novos campos em company_benefits
    op.add_column("company_benefits", sa.Column("subsidiaries", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="[]"))
    op.add_column("company_benefits", sa.Column("valid_from", sa.Date(), nullable=True))
    op.add_column("company_benefits", sa.Column("valid_until", sa.Date(), nullable=True))
    op.add_column("company_benefits", sa.Column("review_frequency_months", sa.Integer(), nullable=True))
    op.add_column("company_benefits", sa.Column("next_review_date", sa.Date(), nullable=True))
    op.add_column("company_benefits", sa.Column("provider_cnpj", sa.String(length=20), nullable=True))

    # Nova tabela de histórico
    op.create_table(
        "company_benefit_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "benefit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("company_benefits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column("change_type", sa.String(50), nullable=False),
        sa.Column("previous_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("change_notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_benefit_history_benefit_id", "company_benefit_history", ["benefit_id"])
    op.create_index("ix_benefit_history_company_id", "company_benefit_history", ["company_id"])


def downgrade():
    op.drop_index("ix_benefit_history_company_id", "company_benefit_history")
    op.drop_index("ix_benefit_history_benefit_id", "company_benefit_history")
    op.drop_table("company_benefit_history")
    op.drop_column("company_benefits", "provider_cnpj")
    op.drop_column("company_benefits", "next_review_date")
    op.drop_column("company_benefits", "review_frequency_months")
    op.drop_column("company_benefits", "valid_until")
    op.drop_column("company_benefits", "valid_from")
    op.drop_column("company_benefits", "subsidiaries")
