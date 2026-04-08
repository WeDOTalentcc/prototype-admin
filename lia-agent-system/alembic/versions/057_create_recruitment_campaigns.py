"""
Migration 057: Create recruitment_campaigns tables for FastAPI.

Lightweight mirror of Rails tables — used for AI workflow orchestration.

Applies to: lia-agent-system (Replit)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "057"
down_revision = "056"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recruitment_campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("talent_pool_id", UUID(as_uuid=True), nullable=True),
        sa.Column("current_stage", sa.String(32), nullable=False, server_default="definition"),
        sa.Column("automation_level", sa.String(16), nullable=False, server_default="semi"),
        sa.Column("stages_config", JSONB, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index("idx_campaigns_company_status", "recruitment_campaigns", ["company_id", "status"])

    op.create_table(
        "campaign_stage_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("recruitment_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("event_data", JSONB, server_default="{}"),
        sa.Column("candidates_count", sa.Integer, server_default="0"),
        sa.Column("triggered_by", sa.String(64), nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("idx_cse_campaign_stage", "campaign_stage_events", ["campaign_id", "stage"])


def downgrade():
    op.drop_table("campaign_stage_events")
    op.drop_table("recruitment_campaigns")
