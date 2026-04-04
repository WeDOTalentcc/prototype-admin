"""Add company_retention_policies table for LGPD data retention

Revision ID: 053
Revises: 052
Create Date: 2026-04-04

WHY: LGPD Art. 15-16 exige que dados pessoais sejam eliminados após a finalidade.
     Para candidatos não contratados, o prazo de mercado é 24 meses.
     A política é opt-in (auto_anonymize=False por default) — o cliente ativa.
"""
import sqlalchemy as sa
from alembic import op

revision = '053'
down_revision = '052'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_retention_policies",
        sa.Column("id", sa.String(255), nullable=False, primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("retention_months", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("auto_anonymize", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("activated_by", sa.String(255), nullable=True),
        sa.Column("last_cleanup_at", sa.DateTime(), nullable=True),
        sa.Column("last_cleanup_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_company_retention_policies_company_id",
        "company_retention_policies",
        ["company_id"],
        unique=True,
    )

    # Adicionar coluna anonymized_at na tabela de candidatos (se não existir)
    # Verifica antes de adicionar para não quebrar em reenvio da migration
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'candidates' AND column_name = 'anonymized_at'
            ) THEN
                ALTER TABLE candidates
                    ADD COLUMN anonymized_at TIMESTAMP NULL,
                    ADD COLUMN anonymized_by VARCHAR(50) NULL;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.drop_index(
        "ix_company_retention_policies_company_id",
        table_name="company_retention_policies",
    )
    op.drop_table("company_retention_policies")
    # Não remover as colunas de candidatos no downgrade — dados de anonimização
    # são auditoria e não devem ser apagados mesmo num rollback de schema.
