"""Add education_snapshot column to candidates table.

The candidates_crud.py serializer reads education via:
    getattr(c, "education_snapshot", None) or []

And the PUT /{candidate_id}/education endpoint writes to:
    UPDATE candidates SET education_snapshot = CAST(:edu AS jsonb)

But this column was never created in the DB (no prior migration).
This migration adds it as a nullable JSONB column with empty-array default.

Revision ID: 258
Revises: 257
"""

from alembic import op
import sqlalchemy as sa

revision = "258"
down_revision = "257"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS education_snapshot JSON DEFAULT '[]'::json"
    )


def downgrade():
    op.drop_column("candidates", "education_snapshot")
