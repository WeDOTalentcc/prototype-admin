"""Add company_plan_configs table with seed data for 4 plans.

Revision ID: 292
Revises: 291
"""
from alembic import op
import sqlalchemy as sa
import json
from sqlalchemy.dialects import postgresql

revision = "292"
down_revision = "291"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_plan_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_code", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("plan_name", sa.String(100), nullable=False),
        sa.Column("max_seats", sa.Integer(), nullable=False),
        sa.Column("embedding_monthly_cap", sa.Integer(), nullable=False),
        sa.Column("embedding_overage_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_cost_per_1k_tokens_brl", sa.Numeric(10, 4), nullable=True),
        sa.Column("embedding_price_per_1k_tokens_brl", sa.Numeric(10, 4), nullable=True),
        sa.Column("llm_monthly_cap", sa.Integer(), nullable=False),
        sa.Column("llm_request_ceiling", sa.Integer(), nullable=False),
        sa.Column("llm_overage_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("llm_cost_per_1k_tokens_brl", sa.Numeric(10, 4), nullable=True),
        sa.Column("llm_price_per_1k_tokens_brl", sa.Numeric(10, 4), nullable=True),
        sa.Column("byok_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pearch_credits_monthly", sa.Integer(), nullable=False),
        sa.Column("pearch_credits_rollover", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pearch_credit_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("apify_credits_monthly", sa.Integer(), nullable=False),
        sa.Column("apify_credits_rollover", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("apify_credit_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_custom_agents", sa.Integer(), nullable=False),
        sa.Column("max_sourcing_agents", sa.Integer(), nullable=False),
        sa.Column("max_digital_twins", sa.Integer(), nullable=False),
        sa.Column("max_campaigns", sa.Integer(), nullable=False),
        sa.Column("agent_executions_monthly", sa.Integer(), nullable=False),
        sa.Column("agent_execution_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ala_carte_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("feature_flags", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_trial", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("trial_days", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    _seed_plans()


def _seed_plans() -> None:
    from sqlalchemy.sql import table, column

    t = table(
        "company_plan_configs",
        column("plan_code"),
        column("plan_name"),
        column("max_seats"),
        column("embedding_monthly_cap"),
        column("llm_monthly_cap"),
        column("llm_request_ceiling"),
        column("byok_enabled"),
        column("pearch_credits_monthly"),
        column("pearch_credits_rollover"),
        column("apify_credits_monthly"),
        column("apify_credits_rollover"),
        column("max_custom_agents"),
        column("max_sourcing_agents"),
        column("max_digital_twins"),
        column("max_campaigns"),
        column("agent_executions_monthly"),
        column("agent_execution_price_cents"),
        column("ala_carte_enabled"),
        column("feature_flags"),
        column("is_trial"),
        column("trial_days"),
    )

    plans = [
        {
            "plan_code": "trial", "plan_name": "Trial", "max_seats": 2,
            "embedding_monthly_cap": 10_000_000, "llm_monthly_cap": 500_000, "llm_request_ceiling": 2_000,
            "byok_enabled": True,
            "pearch_credits_monthly": 200, "pearch_credits_rollover": False,
            "apify_credits_monthly": 200, "apify_credits_rollover": False,
            "max_custom_agents": 1, "max_sourcing_agents": 1, "max_digital_twins": 0, "max_campaigns": 0,
            "agent_executions_monthly": 50, "agent_execution_price_cents": 0, "ala_carte_enabled": False,
            "feature_flags": json.dumps({'byok': True}),
            "is_trial": True, "trial_days": 30,
        },
        {
            "plan_code": "starter", "plan_name": "Starter", "max_seats": 5,
            "embedding_monthly_cap": 50_000_000, "llm_monthly_cap": 2_000_000, "llm_request_ceiling": 2_000,
            "byok_enabled": True,
            "pearch_credits_monthly": 500, "pearch_credits_rollover": False,
            "apify_credits_monthly": 500, "apify_credits_rollover": False,
            "max_custom_agents": 2, "max_sourcing_agents": 1, "max_digital_twins": 0, "max_campaigns": 0,
            "agent_executions_monthly": 200, "agent_execution_price_cents": 40, "ala_carte_enabled": True,
            "feature_flags": json.dumps({'bulk_actions': True, 'export_full': True, 'byok': True}),
            "is_trial": False, "trial_days": None,
        },
        {
            "plan_code": "pro", "plan_name": "Pro", "max_seats": 20,
            "embedding_monthly_cap": 200_000_000, "llm_monthly_cap": 10_000_000, "llm_request_ceiling": 10_000,
            "byok_enabled": True,
            "pearch_credits_monthly": 1_500, "pearch_credits_rollover": False,
            "apify_credits_monthly": 1_500, "apify_credits_rollover": False,
            "max_custom_agents": 10, "max_sourcing_agents": 5, "max_digital_twins": 0, "max_campaigns": 5,
            "agent_executions_monthly": 1_000, "agent_execution_price_cents": 30, "ala_carte_enabled": True,
            "feature_flags": json.dumps({'bulk_actions': True, 'export_full': True, 'custom_persona': True, 'analytics_advanced': True, 'integrations_ats': True, 'voice_screening': True, 'offer_concierge': True, 'byok': True, 'projetos_essencial': True}),
            "is_trial": False, "trial_days": None,
        },
        {
            "plan_code": "enterprise", "plan_name": "Enterprise", "max_seats": 100,
            "embedding_monthly_cap": 500_000_000, "llm_monthly_cap": 40_000_000, "llm_request_ceiling": 50_000,
            "byok_enabled": True,
            "pearch_credits_monthly": 4_000, "pearch_credits_rollover": True,
            "apify_credits_monthly": 4_000, "apify_credits_rollover": True,
            "max_custom_agents": 50, "max_sourcing_agents": 20, "max_digital_twins": 10, "max_campaigns": 20,
            "agent_executions_monthly": 5_000, "agent_execution_price_cents": 20, "ala_carte_enabled": True,
            "feature_flags": json.dumps({'bulk_actions': True, 'export_full': True, 'custom_persona': True, 'analytics_advanced': True, 'integrations_ats': True, 'voice_screening': True, 'offer_concierge': True, 'byok': True, 'projetos_essencial': True, 'projetos_advanced': True, 'digital_twins': True, 'api_access': True, 'white_label': True}),
            "is_trial": False, "trial_days": None,
        },
    ]

    op.bulk_insert(t, plans)


def downgrade() -> None:
    op.drop_table("company_plan_configs")
