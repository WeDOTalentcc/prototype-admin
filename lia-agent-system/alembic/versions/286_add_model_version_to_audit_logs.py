"""add model_version to audit_logs — LGPD Art 15 GAP-10-004

Revision ID: 286_add_model_version_to_audit_logs
Revises: 285_add_fk_agent_deployments_approval_requests
Create Date: 2026-06-15

Adiciona coluna model_version ao audit_logs para rastrear qual modelo
de IA foi usado em cada decisao (LGPD Art. 15 direito de explicacao).
Preenchida automaticamente pelo AuditService via agent_model_config.
"""
from alembic import op
import sqlalchemy as sa


revision = "286_add_model_version_to_audit_logs"
down_revision = "285_add_fk_agent_deployments_approval_requests"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "audit_logs",
        sa.Column("model_version", sa.String(80), nullable=True),
    )
    op.create_index(
        "ix_audit_logs_model_version",
        "audit_logs",
        ["model_version"],
    )


def downgrade():
    op.drop_index("ix_audit_logs_model_version", table_name="audit_logs")
    op.drop_column("audit_logs", "model_version")
