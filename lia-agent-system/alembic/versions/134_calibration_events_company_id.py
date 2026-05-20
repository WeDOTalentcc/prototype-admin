"""Add company_id to calibration_events.

Revision ID: 134_calibration_events_company_id
Revises: 133_calibration_weights_company_id
Create Date: 2026-05-20

Sprint E.1 (Task #43 follow-up): close multi-tenancy gap.
Model declares company_id (multi-tenant), but DB never had the column.
Adds NULLABLE column + index. Backfill of 3 existing rows is separate.
"""
from alembic import op
import sqlalchemy as sa


revision = "134_calibration_events_company_id"
down_revision = "133_calibration_weights_company_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "calibration_events",
        sa.Column("company_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_calibration_events_company_id",
        "calibration_events",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_calibration_events_company_id",
        table_name="calibration_events",
    )
    op.drop_column("calibration_events", "company_id")
