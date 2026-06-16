"""Create agent_quotas and recruitment_campaigns tables, add studio columns to ai_consumption.

Revision ID: 064
Revises: 063
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "064_create_agent_quotas_recruitment_campaigns"
down_revision = "063_create_scheduling_links_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_quotas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("plan_code", sa.String(32), nullable=False, server_default="starter"),
        sa.Column("max_sourcing_agents", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_custom_agents", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_digital_twins", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_campaigns", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active_sourcing_agents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_custom_agents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_digital_twins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_campaigns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "recruitment_campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("created_by", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("job_id", sa.String(64), nullable=True, index=True),
        sa.Column("talent_pool_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("stages", JSONB(), nullable=False, server_default="[]"),
        sa.Column("current_stage_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("automation_level", sa.String(20), nullable=False, server_default="semi"),
        sa.Column("total_candidates", sa.Integer(), server_default="0"),
        sa.Column("candidates_screened", sa.Integer(), server_default="0"),
        sa.Column("candidates_contacted", sa.Integer(), server_default="0"),
        sa.Column("candidates_interviewed", sa.Integer(), server_default="0"),
        sa.Column("candidates_offered", sa.Integer(), server_default="0"),
        sa.Column("candidates_hired", sa.Integer(), server_default="0"),
        sa.Column("stage_history", JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.add_column(
        "ai_consumption",
        sa.Column("agent_category", sa.String(20), nullable=False, server_default="core"),
    )
    op.add_column(
        "ai_consumption",
        sa.Column("studio_agent_id", sa.String(64), nullable=True),
    )


def downgrade():
    op.drop_column("ai_consumption", "studio_agent_id")
    op.drop_column("ai_consumption", "agent_category")
    op.drop_table("recruitment_campaigns")
    op.drop_table("agent_quotas")
