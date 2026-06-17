"""Create agent_deployments table for binding Studio agents to targets.

Revision ID: 070_agent_deployments
Revises: 069_agent_studio_parity
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "070_agent_deployments"
down_revision = "069_agent_studio_parity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_deployments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("target_name", sa.String(512), nullable=True),
        sa.Column("trigger_mode", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("schedule_cron", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config_overrides", JSONB, server_default="{}"),
        sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("candidates_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Check constraints
    op.create_check_constraint(
        "ck_agent_deployments_target_type",
        "agent_deployments",
        "target_type IN ('job', 'talent_pool', 'pipeline_stage', 'candidate_list')",
    )
    op.create_check_constraint(
        "ck_agent_deployments_trigger_mode",
        "agent_deployments",
        "trigger_mode IN ('manual', 'on_new_candidate', 'on_stage_change', 'scheduled')",
    )

    # Unique constraint: one agent per target
    op.create_unique_constraint(
        "uq_agent_deployment_agent_target",
        "agent_deployments",
        ["agent_id", "target_type", "target_id"],
    )


def downgrade():
    op.drop_constraint("uq_agent_deployment_agent_target", "agent_deployments", type_="unique")
    op.drop_constraint("ck_agent_deployments_trigger_mode", "agent_deployments", type_="check")
    op.drop_constraint("ck_agent_deployments_target_type", "agent_deployments", type_="check")
    op.drop_table("agent_deployments")
