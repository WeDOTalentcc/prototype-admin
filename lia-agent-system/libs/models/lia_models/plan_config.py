"""Company Plan Configuration — single source of truth for plan limits and features.

Replaces hardcoded PLAN_DAILY_LIMITS, PLAN_REQUEST_LIMITS, PLAN_AGENT_QUOTAS dicts.
Seed migration inserts trial/starter/pro/enterprise rows matching current hardcoded values.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from lia_config.database import Base


class CompanyPlanConfig(Base):
    __tablename__ = "company_plan_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_code = Column(String(50), unique=True, nullable=False, index=True)
    plan_name = Column(String(100), nullable=False)

    # Dimension 1: Seats
    max_seats = Column(Integer, nullable=False, default=5)

    # Dimension 2a: Embedding (always WeDOTalent, never BYOK)
    embedding_monthly_cap = Column(Integer, nullable=False, default=50_000_000)
    embedding_overage_price_cents = Column(Integer, nullable=False, default=0)
    embedding_cost_per_1k_tokens_brl = Column(
        Numeric(10, 4), nullable=True
    )
    embedding_price_per_1k_tokens_brl = Column(
        Numeric(10, 4), nullable=True
    )

    # Dimension 2b: LLM General
    llm_monthly_cap = Column(Integer, nullable=False, default=2_000_000)
    llm_request_ceiling = Column(Integer, nullable=False, default=2_000)
    llm_overage_price_cents = Column(Integer, nullable=False, default=0)
    llm_cost_per_1k_tokens_brl = Column(Numeric(10, 4), nullable=True)
    llm_price_per_1k_tokens_brl = Column(Numeric(10, 4), nullable=True)
    byok_enabled = Column(Boolean, default=False, nullable=False)

    # Dimension 3a: Pearch credits
    pearch_credits_monthly = Column(Integer, nullable=False, default=500)
    pearch_credits_rollover = Column(Boolean, default=False, nullable=False)
    pearch_credit_price_cents = Column(Integer, nullable=False, default=0)

    # Dimension 3b: Apify credits
    apify_credits_monthly = Column(Integer, nullable=False, default=500)
    apify_credits_rollover = Column(Boolean, default=False, nullable=False)
    apify_credit_price_cents = Column(Integer, nullable=False, default=0)

    # Dimension 4a: Agent quotas
    max_custom_agents = Column(Integer, nullable=False, default=2)
    max_sourcing_agents = Column(Integer, nullable=False, default=1)
    max_digital_twins = Column(Integer, nullable=False, default=0)
    max_campaigns = Column(Integer, nullable=False, default=0)

    # Dimension 4b: Agent executions
    agent_executions_monthly = Column(Integer, nullable=False, default=200)
    agent_execution_price_cents = Column(Integer, nullable=False, default=40)
    ala_carte_enabled = Column(Boolean, default=True, nullable=False)

    # Dimension 5: Feature flags (binary per plan)
    feature_flags = Column(JSONB, nullable=False, default=dict)

    # Trial config
    is_trial = Column(Boolean, default=False, nullable=False)
    trial_days = Column(Integer, nullable=True)

    # Versioning
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CompanyPlanConfig plan_code={self.plan_code!r}>"
