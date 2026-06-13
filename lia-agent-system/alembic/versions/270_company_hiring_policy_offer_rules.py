"""268 — company_hiring_policies.offer_rules (N2/N3 offer configuration block)

Adiciona coluna JSONB `offer_rules` na tabela `company_hiring_policies`.
Default conservador: negociação desativada, 30 dias aviso prévio, dias 1 e 15.

Revision ID: 270_company_hiring_policy_offer_rules
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "270_company_hiring_policy_offer_rules"
down_revision = None
branch_labels = None
depends_on = None

_TABLE = "company_hiring_policies"
_DEFAULT = (
    '{"allowed_start_day_of_month": [1, 15],'
    ' "onboarding_blackout_periods": [],'
    ' "min_notice_days": 30,'
    ' "negotiation_enabled": false,'
    ' "salary_flex_pct_max": 0,'
    ' "benefits_flex_items": [],'
    ' "negotiation_hitl_threshold_pct": 5,'
    ' "counter_proposal_max_rounds": 2}'
)


def upgrade() -> None:
    op.add_column(
        _TABLE,
        sa.Column(
            "offer_rules",
            JSONB(),
            nullable=True,
            server_default=_DEFAULT,
        ),
    )


def downgrade() -> None:
    op.drop_column(_TABLE, "offer_rules")
