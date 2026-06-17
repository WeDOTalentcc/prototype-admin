"""Add can_comment and can_rate columns to shared_searches table.

Revision ID: 021_add_can_comment_can_rate_shared_searches
Revises: 020_add_guardrails_table
Create Date: 2026-03-04

S1 — canComment/canRate permissions:
Allow recruiters to control whether hiring managers can comment or rate
candidates in shared searches. Both default to True for backward compatibility.
"""
from alembic import op
import sqlalchemy as sa

revision = "021_add_can_comment_can_rate_shared_searches"
down_revision = "020_add_guardrails_table"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shared_searches",
        sa.Column("can_comment", sa.Boolean, nullable=False, server_default="true"),
    )
    op.add_column(
        "shared_searches",
        sa.Column("can_rate", sa.Boolean, nullable=False, server_default="true"),
    )


def downgrade():
    op.drop_column("shared_searches", "can_rate")
    op.drop_column("shared_searches", "can_comment")
