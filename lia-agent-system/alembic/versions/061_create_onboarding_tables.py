"""Create onboarding agent state + WhatsApp sessions tables.

Revision ID: 061_create_onboarding_tables
Revises: 060
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

revision = "061_create_onboarding_tables"
down_revision = "060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Onboarding agent state (tracks FSM state per user)
    op.create_table(
        "onboarding_agent_state",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("account_id", sa.Integer, nullable=False),
        sa.Column("phase", sa.String(30), nullable=False, default="pending"),
        sa.Column("channel", sa.String(20)),  # whatsapp, email, web
        sa.Column("session_data", JSONB, default={}),
        sa.Column("whatsapp_context", JSONB, default={}),  # Messages for web handoff
        sa.Column("onboarding_metadata", JSONB, default={}),  # Learned preferences
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_onboarding_agent_state_user_phase",
        "onboarding_agent_state",
        ["user_id", "phase"],
    )

    # WhatsApp sessions (tracks 24h window, flow state)
    op.create_table(
        "whatsapp_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("twilio_conversation_sid", sa.String(100)),
        sa.Column("flow_id", sa.String(100)),  # WhatsApp Flow ID
        sa.Column("flow_token", sa.String(200)),  # Flow session token
        sa.Column("flow_status", sa.String(20), default="pending"),  # pending, in_progress, completed
        sa.Column("flow_response_data", JSONB, default={}),  # Flow completion data
        sa.Column("session_active", sa.Boolean, default=True),
        sa.Column("expires_at", sa.DateTime),  # 24h window
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_whatsapp_sessions_phone",
        "whatsapp_sessions",
        ["phone_number"],
    )
    op.create_index(
        "ix_whatsapp_sessions_active",
        "whatsapp_sessions",
        ["user_id", "session_active"],
    )


def downgrade() -> None:
    op.drop_table("whatsapp_sessions")
    op.drop_table("onboarding_agent_state")
