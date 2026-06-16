"""R-011: Adicionar company_id a SOXAuditLog + backfill + índice

Revision ID: 079_sox_audit_company_id
Revises: 078_few_shot_candidates
Create Date: 2026-05-01

Zero-downtime strategy:
  1. Adicionar company_id UUID NULL (nunca NOT NULL direto em tabela de alta escrita)
  2. Backfill via client_id cast para UUID (para rows com client_id em formato UUID)
  3. Criar índice composto (company_id, timestamp) para queries RLS-scoped
  4. NOT NULL constraint + RLS policy vêm em migration 080 após verificação de backfill

NOTA: Migration 080 adicionará:
  - ALTER TABLE sox_audit_logs ALTER COLUMN company_id SET NOT NULL
  - CREATE POLICY sox_audit_rls ON sox_audit_logs FOR ALL
      USING (company_id = current_setting('app.current_company_id')::uuid)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "079_sox_audit_company_id"
down_revision = "078_few_shot_candidates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Adicionar company_id UUID nullable
    op.add_column(
        "sox_audit_logs",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # 2. Backfill: tenta converter client_id → UUID para rows existentes
    # client_id é String(255) e pode conter UUIDs no formato padrão
    op.execute("""
        UPDATE sox_audit_logs
        SET company_id = client_id::uuid
        WHERE company_id IS NULL
          AND client_id IS NOT NULL
          AND client_id ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    """)

    # 3. Criar índice composto para queries scoped por tenant
    op.create_index(
        "idx_sox_audit_company_timestamp",
        "sox_audit_logs",
        ["company_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("idx_sox_audit_company_timestamp", table_name="sox_audit_logs")
    op.drop_column("sox_audit_logs", "company_id")
