"""Add prompt_version column to messages table for A/B testing audit trail.

Revision ID: 062
Revises: 061_create_onboarding_tables
Create Date: 2026-04-11

Stores SHA-256 hash prefix (12 chars) of the system prompt used in each
interaction, enabling per-prompt-version metric analysis and A/B test
result tracing.
"""
from alembic import op
import sqlalchemy as sa


revision = "062_add_prompt_version_to_messages"
down_revision = "061_create_onboarding_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("prompt_version", sa.String(16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "prompt_version")
