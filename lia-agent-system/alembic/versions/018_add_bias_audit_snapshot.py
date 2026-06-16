"""Add bias_audit_snapshots table for historical fairness auditing (G.4).

Revision ID: 018_add_bias_audit_snapshot
Revises: 017_add_company_calendar_credentials
Create Date: 2026-03-02

G.4 — BiasAuditSnapshot:
Persiste snapshots históricos de auditoria de viés (Four-Fifths Rule) por vaga.
Apenas dados agregados — sem PII (LGPD-safe).
Rastreabilidade exigida por SOX / ISO 27001 / EU AI Act.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "018_add_bias_audit_snapshot"
down_revision = "017_add_company_calendar_credentials"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bias_audit_snapshots",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("evaluated_at", sa.DateTime, nullable=False),
        sa.Column("total_candidates", sa.Integer, nullable=False, server_default="0"),
        sa.Column("has_alerts", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("dimensions_json", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_bias_audit_snapshots_company_id",
        "bias_audit_snapshots",
        ["company_id"],
    )
    op.create_index(
        "ix_bias_audit_snapshots_job_id",
        "bias_audit_snapshots",
        ["job_id"],
    )


def downgrade():
    op.drop_index("ix_bias_audit_snapshots_job_id", "bias_audit_snapshots")
    op.drop_index("ix_bias_audit_snapshots_company_id", "bias_audit_snapshots")
    op.drop_table("bias_audit_snapshots")
