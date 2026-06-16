import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base

PLAN_AGENT_LIMITS: dict[str, int] = {
    "starter": 1,
    "basic": 2,
    "trial": 1,
    "free": 1,
    "pro": 5,
    "standard": 5,
    "business": 20,
    "premium": 20,
    "enterprise": -1,
}

DEFAULT_AGENT_LIMIT = 2


class AgentQuota(Base):
    __tablename__ = "agent_quotas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(64), nullable=False, unique=True, index=True)

    plan_code = Column(String(50), nullable=False, default="starter")
    max_sourcing_agents = Column(Integer, nullable=False, default=2)
    max_custom_agents = Column(Integer, nullable=False, default=2)
    max_digital_twins = Column(Integer, nullable=False, default=1)
    max_campaigns = Column(Integer, nullable=False, default=2)

    active_sourcing_agents = Column(Integer, nullable=False, default=0)
    active_custom_agents = Column(Integer, nullable=False, default=0)
    active_digital_twins = Column(Integer, nullable=False, default=0)
    active_campaigns = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_agent_quota_company", "company_id"),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<AgentQuota company={self.company_id} plan={self.plan_code}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "plan_code": self.plan_code,
            "max_sourcing_agents": self.max_sourcing_agents,
            "max_custom_agents": self.max_custom_agents,
            "max_digital_twins": self.max_digital_twins,
            "max_campaigns": self.max_campaigns,
            "active_sourcing_agents": self.active_sourcing_agents,
            "active_custom_agents": self.active_custom_agents,
            "active_digital_twins": self.active_digital_twins,
            "active_campaigns": self.active_campaigns,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def get_limits_for_plan(plan_code: str | None) -> dict[str, int]:
    normalized = (plan_code or "starter").lower().strip()
    limit = PLAN_AGENT_LIMITS.get(normalized, DEFAULT_AGENT_LIMIT)
    if limit == -1:
        return {
            "max_sourcing_agents": -1,
            "max_custom_agents": -1,
            "max_digital_twins": -1,
            "max_campaigns": -1,
        }
    return {
        "max_sourcing_agents": limit,
        "max_custom_agents": limit,
        "max_digital_twins": max(limit // 2, 1),
        "max_campaigns": limit,
    }
