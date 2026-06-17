"""Create agent_execution_logs table.

Revision ID: 071_agent_execution_logs
Revises: 070_agent_deployments
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "071_agent_execution_logs"
down_revision = "070_agent_deployments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_execution_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("deployment_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("input_message", sa.Text(), nullable=False),
        sa.Column("output_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), server_default="0.0"),
        sa.Column("tokens_input", sa.Integer(), server_default="0"),
        sa.Column("tokens_output", sa.Integer(), server_default="0"),
        sa.Column("model_used", sa.String(128), server_default=""),
        sa.Column("latency_ms", sa.Integer(), server_default="0"),
        sa.Column("credits_consumed", sa.Integer(), server_default="0"),
        sa.Column("tool_calls", ARRAY(sa.String()), server_default="{}"),
        sa.Column("compliance_status", sa.String(32), server_default="pass"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("agent_execution_logs")
