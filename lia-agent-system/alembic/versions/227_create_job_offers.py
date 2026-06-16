"""create job_offers table

Revision ID: 227
Revises: 226
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa

revision = "227"
down_revision = "226"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_offers",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("company_id", sa.String, nullable=False),
        sa.Column("job_vacancy_id", sa.String, nullable=False),
        sa.Column("candidate_id", sa.String, nullable=False),
        sa.Column("salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="BRL"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("candidate_response", sa.String(30), nullable=True),
        sa.Column("response_notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.String, nullable=True),
        sa.Column("requires_manager_approval", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("manager_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_job_offers_company_job", "job_offers", ["company_id", "job_vacancy_id"])
    op.create_index("ix_job_offers_candidate", "job_offers", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_job_offers_candidate", table_name="job_offers")
    op.drop_index("ix_job_offers_company_job", table_name="job_offers")
    op.drop_table("job_offers")
