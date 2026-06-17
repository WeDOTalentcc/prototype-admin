"""Add draft_data + last_saved_draft_at to job_vacancies (GAP-05-005).

Revision ID: 288
Revises: 287
Create Date: 2026-06-16

These two nullable columns enable the wizard draft-recovery pattern:
- draft_data (JSONB): stores partial form snapshot from build_draft_snapshot().
  Cleared (set to NULL) when the vacancy transitions out of rascunho status.
- last_saved_draft_at (TIMESTAMP): tracks when the last auto-save occurred so
  the FE can display a "saved X minutes ago" indicator.

No data migration required — both columns are nullable with no default.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "288"
down_revision = "287"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_vacancies",
        sa.Column("draft_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "job_vacancies",
        sa.Column("last_saved_draft_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("job_vacancies", "last_saved_draft_at")
    op.drop_column("job_vacancies", "draft_data")
