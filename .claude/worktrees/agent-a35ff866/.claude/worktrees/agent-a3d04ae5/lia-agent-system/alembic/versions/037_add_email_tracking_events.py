"""Add email tracking events table

Revision ID: 037
Revises: 035_add_user_agent_preferences
Create Date: 2026-03-11

COMP-7: Email tracking pixel + link tracking
LGPD Art. 7 VI: base legal legitimate interest (disclosure-based)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = "037"
down_revision = "035_add_user_agent_preferences"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_tracking_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("notification_id", sa.String(255), nullable=False, index=True),
        sa.Column("company_id", sa.String(255), nullable=False, index=True),
        sa.Column("token", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("event_type", sa.String(50), nullable=False),  # "open" | "click"
        sa.Column("recipient_hash", sa.String(64), nullable=True),  # SHA256 do email
        sa.Column("ip_hash", sa.String(64), nullable=True),         # SHA256 do IP
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("link_url", sa.Text, nullable=True),             # para click events
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metadata", JSONB, nullable=True),
    )
    # Índice composto para stats por notification
    op.create_index(
        "ix_email_tracking_notification_type",
        "email_tracking_events",
        ["notification_id", "event_type"],
    )


def downgrade():
    op.drop_index("ix_email_tracking_notification_type", "email_tracking_events")
    op.drop_table("email_tracking_events")
