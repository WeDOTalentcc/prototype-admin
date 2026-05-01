"""
AI Consumption tracking models.

This module provides models for:
- AI token/credit consumption tracking per client
- Credit balance and limits management
- Billing and usage metrics
"""
from datetime import datetime, date, timedelta
from sqlalchemy import Column, String, Integer, DateTime, Date, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from lia_config.database import Base
import uuid

AI_LOG_RETENTION_DAYS = 365


class AiConsumption(Base):
    """
    Tracks AI consumption (tokens/credits) for each operation.
    
    Records every AI usage including:
    - Agent type and operation performed
    - Model used and token counts
    - Cost in cents for billing
    - Associated candidate/vacancy for context
    """
    __tablename__ = "ai_consumption"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    agent_type = Column(String(50), nullable=False, index=True)
    agent_category = Column(String(20), nullable=False, default="core", index=True)
    operation = Column(String(100), nullable=False)
    model = Column(String(50), nullable=False, index=True)
    studio_agent_id = Column(String(64), nullable=True, index=True)
    
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_cents = Column(Integer, default=0)
    
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    vacancy_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    # LGPD — data agendada para deleção (365 dias após criação, conforme política L-6)
    scheduled_deletion_at = Column(DateTime, nullable=True, index=True)

    def __repr__(self):
        return f"<AiConsumption {self.id} - {self.agent_type}/{self.operation}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "agent_type": self.agent_type,
            "agent_category": self.agent_category,
            "operation": self.operation,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_cents": self.cost_cents,
            "studio_agent_id": self.studio_agent_id,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "vacancy_id": str(self.vacancy_id) if self.vacancy_id else None,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AiCreditsBalance(Base):
    """
    Tracks AI credit balance and limits per company.
    
    Manages:
    - Monthly token limits
    - Current period usage
    - Billing period dates
    - Overage settings
    """
    __tablename__ = "ai_credits_balance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    monthly_limit = Column(Integer, default=100000)
    current_usage = Column(Integer, default=0)
    
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    overage_allowed = Column(Boolean, default=False)
    overage_rate_cents = Column(Integer, default=0)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<AiCreditsBalance {self.id} - company {self.company_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "monthly_limit": self.monthly_limit,
            "current_usage": self.current_usage,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "overage_allowed": self.overage_allowed,
            "overage_rate_cents": self.overage_rate_cents,
            "usage_percentage": round((self.current_usage / self.monthly_limit) * 100, 2) if self.monthly_limit > 0 else 0,
            "remaining_tokens": max(0, self.monthly_limit - self.current_usage),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
