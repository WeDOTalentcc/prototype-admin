"""create hiring_nps table

Revision ID: 228
Revises: 227
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa

revision = "228"
down_revision = "227"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hiring_nps",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("company_id", sa.String, nullable=False),
        sa.Column("job_vacancy_id", sa.String, nullable=False),
        sa.Column("candidate_id", sa.String, nullable=True),
        sa.Column("respondent_type", sa.String(20), nullable=False),
        sa.Column("respondent_email", sa.String(320), nullable=True),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Integer, nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_by", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_hiring_nps_company_job", "hiring_nps", ["company_id", "job_vacancy_id"])
    op.create_index("ix_hiring_nps_token", "hiring_nps", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_hiring_nps_token", table_name="hiring_nps")
    op.drop_index("ix_hiring_nps_company_job", table_name="hiring_nps")
    op.drop_table("hiring_nps")
