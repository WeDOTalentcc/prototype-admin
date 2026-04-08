"""
Migration 056: Create sourcing_agents and sourcing_agent_signals tables.

Persistent multi-agent sourcing per job/pool with feedback loop (Juicebox pattern).

Applies to: lia-agent-system (Replit)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "056"
down_revision = "055"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sourcing_agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("job_id", sa.String(64), nullable=True),  # nullable: can be linked to pool instead
        sa.Column("talent_pool_id", UUID(as_uuid=True), sa.ForeignKey("talent_pools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_template_id", sa.String(255), sa.ForeignKey("agent_templates.id", ondelete="SET NULL"), nullable=True),

        sa.Column("agent_name", sa.String(256), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),  # active, paused, completed
        sa.Column("calibration_v", sa.Integer, nullable=False, server_default="0"),

        # Search strategy (evolves with feedback)
        sa.Column("search_strategy", JSONB, nullable=False, server_default="{}"),
        # Keys: required_skills[], seniority, location, min_years_exp, exclusions[], positive_signals[]

        # Preferences (set by recruiter)
        sa.Column("preferences", JSONB, nullable=False, server_default="{}"),
        # Keys: candidates_per_day, channels[], schedule, notify_frequency

        # Outreach config
        sa.Column("outreach_config", JSONB, nullable=False, server_default="{}"),

        # Performance counters
        sa.Column("profiles_viewed", sa.Integer, server_default="0"),
        sa.Column("profiles_approved", sa.Integer, server_default="0"),
        sa.Column("profiles_rejected", sa.Integer, server_default="0"),
        sa.Column("emails_sent", sa.Integer, server_default="0"),

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index("idx_sourcing_agents_company_job", "sourcing_agents", ["company_id", "job_id"])
    op.create_index("idx_sourcing_agents_company_pool", "sourcing_agents", ["company_id", "talent_pool_id"])
    op.create_index("idx_sourcing_agents_status", "sourcing_agents", ["company_id", "status"])

    op.create_table(
        "sourcing_agent_signals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("sourcing_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_type", sa.String(16), nullable=False),  # positive, negative
        sa.Column("candidate_id", sa.String(64), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("criteria_extracted", sa.ARRAY(sa.String), server_default="{}"),  # LLM-extracted criteria from reason
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("idx_signals_agent", "sourcing_agent_signals", ["agent_id", "signal_type"])


def downgrade():
    op.drop_table("sourcing_agent_signals")
    op.drop_table("sourcing_agents")
