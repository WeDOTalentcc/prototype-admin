"""268 - add fairness_audit_log_id FK to fairness_policy_violations

Revision ID: 268_add_fairness_audit_log_id_to_violations
Revises: 267_add_screening_thresholds_defaults
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "268_add_fairness_audit_log_id_to_violations"
down_revision = "267_add_screening_thresholds_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fairness_policy_violations",
        sa.Column(
            "fairness_audit_log_id",
            UUID(as_uuid=True),
            nullable=True,
            comment="FK para fairness_audit_log - link entre trail regulatorio e log operacional",
        ),
    )
    op.create_index(
        "ix_violations_audit_log_id",
        "fairness_policy_violations",
        ["fairness_audit_log_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_violations_audit_log_id", table_name="fairness_policy_violations")
    op.drop_column("fairness_policy_violations", "fairness_audit_log_id")
