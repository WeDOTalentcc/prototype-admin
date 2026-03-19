"""Add scheduled_deletion_at to ai_consumption for LGPD retention (L-6).

Revision ID: 016_add_scheduled_deletion_ai_consumption
Revises: 015_add_fairness_audit_log
Create Date: 2026-03-02

L-6 — AI Log Retention:
Adiciona coluna scheduled_deletion_at à tabela ai_consumption para
implementar política de retenção de 365 dias conforme LGPD e Guia WeDOTalent v3.4.

O campo é preenchido automaticamente pelo TokenTrackingService em record_usage()
e verificado pelo LgpdCleanupService no job diário de limpeza.
"""
from alembic import op
import sqlalchemy as sa


revision = "016_add_scheduled_deletion_ai_consumption"
down_revision = "015_add_fairness_audit_log"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_consumption",
        sa.Column("scheduled_deletion_at", sa.DateTime, nullable=True, index=True),
    )
    # Preencher registros existentes: scheduled_deletion_at = created_at + 365 dias
    op.execute(
        """
        UPDATE ai_consumption
        SET scheduled_deletion_at = created_at + INTERVAL '365 days'
        WHERE scheduled_deletion_at IS NULL
        """
    )


def downgrade():
    op.drop_column("ai_consumption", "scheduled_deletion_at")
