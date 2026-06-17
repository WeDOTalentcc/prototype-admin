"""add vacancy_alert_configs table

Revision ID: 264_add_vacancy_alert_configs
Revises: 263_add_vacancy_candidate_scoring_fields
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "264_add_vacancy_alert_configs"
down_revision = "263_add_vacancy_candidate_scoring_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vacancy_alert_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("vacancy_id", sa.String(), nullable=False),
        sa.Column("recruiter_id", sa.String(), nullable=False),
        sa.Column("alert_type", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="daily"),
        sa.UniqueConstraint("vacancy_id", "recruiter_id", "alert_type", name="uq_vacancy_alert"),
    )
    op.create_index("ix_vacancy_alert_configs_company_id", "vacancy_alert_configs", ["company_id"])
    op.create_index("ix_vacancy_alert_configs_vacancy_id", "vacancy_alert_configs", ["vacancy_id"])
    op.create_index("ix_vacancy_alert_configs_recruiter_id", "vacancy_alert_configs", ["recruiter_id"])


def downgrade():
    op.drop_index("ix_vacancy_alert_configs_recruiter_id")
    op.drop_index("ix_vacancy_alert_configs_vacancy_id")
    op.drop_index("ix_vacancy_alert_configs_company_id")
    op.drop_table("vacancy_alert_configs")
