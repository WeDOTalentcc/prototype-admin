"""Add company_id to recruiter_field_preferences.

Revision ID: 135_recruiter_field_preferences_company_id
Revises: 134_calibration_events_company_id
Create Date: 2026-05-20

Sprint E.1 (Task #43 follow-up): close multi-tenancy gap.
Table is empty (0 rows) → ADD COLUMN NULL is fully safe.
Model declares String(255) nullable=True index=True.
"""
from alembic import op
import sqlalchemy as sa


revision = "135_recruiter_field_preferences_company_id"
down_revision = "134_calibration_events_company_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("company_id", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_recruiter_field_preferences_company_id",
        "recruiter_field_preferences",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recruiter_field_preferences_company_id",
        table_name="recruiter_field_preferences",
    )
    op.drop_column("recruiter_field_preferences", "company_id")
