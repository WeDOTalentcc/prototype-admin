"""create manager_alignments table

Revision ID: 229
Revises: 228
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa

revision = "229"
down_revision = "228"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manager_alignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("job_vacancy_id", sa.String(255), nullable=False),
        sa.Column("manager_email", sa.String(255), nullable=False),
        sa.Column("manager_name", sa.String(255), nullable=True),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("response_notes", sa.Text, nullable=True),
        sa.Column("responded_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_manager_alignments_company_id", "manager_alignments", ["company_id"])
    op.create_index("ix_manager_alignments_job_vacancy_id", "manager_alignments", ["job_vacancy_id"])
    op.create_index("ix_manager_alignments_token", "manager_alignments", ["token"], unique=True)
    op.create_index("ix_manager_alignments_company_job", "manager_alignments", ["company_id", "job_vacancy_id"])


def downgrade() -> None:
    op.drop_index("ix_manager_alignments_company_job", table_name="manager_alignments")
    op.drop_index("ix_manager_alignments_token", table_name="manager_alignments")
    op.drop_index("ix_manager_alignments_job_vacancy_id", table_name="manager_alignments")
    op.drop_index("ix_manager_alignments_company_id", table_name="manager_alignments")
    op.drop_table("manager_alignments")
