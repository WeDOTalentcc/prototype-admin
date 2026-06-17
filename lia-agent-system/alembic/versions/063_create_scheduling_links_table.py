"""Create scheduling_links table for self-scheduling feature.

Revision ID: 063
Revises: 062
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "063_create_scheduling_links_table"
down_revision = "062_add_prompt_version_to_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduling_links",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token", sa.String(24), nullable=False, unique=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("is_used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("used_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_scheduling_links_candidate_id", "scheduling_links", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_scheduling_links_candidate_id", table_name="scheduling_links")
    op.drop_table("scheduling_links")
