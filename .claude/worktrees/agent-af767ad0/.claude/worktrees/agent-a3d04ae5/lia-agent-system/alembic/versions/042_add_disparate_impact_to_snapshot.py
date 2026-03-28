"""Add disparate_impact_data to bias_audit_snapshots (D3)

Revision ID: 042
Revises: 041
Create Date: 2026-03-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bias_audit_snapshots",
        sa.Column("disparate_impact_data", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bias_audit_snapshots", "disparate_impact_data")
