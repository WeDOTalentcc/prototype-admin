"""add_manager_preferences

Revision ID: 104
Revises: 103_add_compensation_policy_id_to_jobs
Create Date: 2026-04-30

LGPD audit: stores only professional data (corporate email, work preferences).
No sensitive personal data. See libs/models/lia_models/manager_preferences.py.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "104"
down_revision = "103_add_compensation_policy_id_to_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manager_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("manager_email", sa.String(255), nullable=False),
        sa.Column("manager_name", sa.String(255), nullable=True),
        sa.Column("preferred_seniorities", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_departments", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_work_models", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("salary_percentile_preference", sa.Integer(), nullable=True),
        sa.Column("screening_style", sa.String(50), nullable=False, server_default="standard"),
        sa.Column("approve_before_publish", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("jobs_created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_job_created_at", sa.DateTime(), nullable=True),
        sa.Column("corrections_log", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_idempotency_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("company_id", "manager_email", name="uq_manager_prefs_company_email"),
    )
    op.create_index("idx_manager_prefs_company_id", "manager_preferences", ["company_id"])
    op.create_index("idx_manager_prefs_email", "manager_preferences", ["manager_email"])
    op.create_index(
        "idx_manager_prefs_company_email",
        "manager_preferences",
        ["company_id", "manager_email"],
    )


def downgrade() -> None:
    op.drop_index("idx_manager_prefs_company_email", table_name="manager_preferences")
    op.drop_index("idx_manager_prefs_email", table_name="manager_preferences")
    op.drop_index("idx_manager_prefs_company_id", table_name="manager_preferences")
    op.drop_table("manager_preferences")
