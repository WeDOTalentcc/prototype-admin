"""
ClientAccount model for multi-tenant client management.

Represents a client company that uses the LIA platform.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer, Index, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from typing import Dict, Any, List

from lia_config.database import Base


class ClientStatus(str, enum.Enum):
    """Status of a client account."""
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CHURNED = "churned"
    PENDING_SETUP = "pending_setup"


class ClientAccount(Base):
    """
    ClientAccount model.
    
    Represents a client company with their subscription, limits and configuration.
    """
    __tablename__ = "client_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), nullable=False)
    trade_name = Column(String(255), nullable=True)
    cnpj = Column(String(20), unique=True, nullable=True)
    
    primary_email = Column(String(255), nullable=True)
    primary_phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    
    address = Column(JSON, nullable=True, default=dict)
    
    status = Column(String(50), default=ClientStatus.PENDING_SETUP.value, index=True)
    plan_id = Column(String(100), nullable=True, index=True)
    contract_start_date = Column(DateTime, nullable=True)
    contract_end_date = Column(DateTime, nullable=True)
    
    user_limit = Column(Integer, default=10)
    job_limit = Column(Integer, default=50)
    ai_credits_monthly = Column(Integer, default=1000)
    
    settings = Column(JSON, nullable=True, default=dict)
    features_enabled = Column(JSON, nullable=True, default=list)
    
    account_manager_id = Column(String(255), nullable=True)
    implementation_manager_id = Column(String(255), nullable=True)
    
    logo_url = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    onboarding_completed_at = Column(DateTime, nullable=True)
    
    welcome_email_sent = Column(Boolean, default=False)
    welcome_email_sent_at = Column(DateTime, nullable=True)
    workos_organization_created = Column(Boolean, default=False)
    workos_organization_created_at = Column(DateTime, nullable=True)
    sso_configured = Column(Boolean, default=False)
    sso_configured_at = Column(DateTime, nullable=True)
    
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_client_status', 'status'),
        Index('idx_client_plan', 'plan_id'),
        Index('idx_client_cnpj', 'cnpj'),
        Index('idx_client_not_deleted', 'is_deleted'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ClientAccount {self.id} - {self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "trade_name": self.trade_name,
            "cnpj": self.cnpj,
            "primary_email": self.primary_email,
            "primary_phone": self.primary_phone,
            "website": self.website,
            "address": self.address or {},
            "status": self.status,
            "plan_id": self.plan_id,
            "contract_start_date": self.contract_start_date.isoformat() if self.contract_start_date else None,
            "contract_end_date": self.contract_end_date.isoformat() if self.contract_end_date else None,
            "user_limit": self.user_limit,
            "job_limit": self.job_limit,
            "ai_credits_monthly": self.ai_credits_monthly,
            "settings": self.settings or {},
            "features_enabled": self.features_enabled or [],
            "account_manager_id": self.account_manager_id,
            "implementation_manager_id": self.implementation_manager_id,
            "logo_url": self.logo_url,
            "industry": self.industry,
            "company_size": self.company_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "onboarding_completed_at": self.onboarding_completed_at.isoformat() if self.onboarding_completed_at else None,
            "welcome_email_sent": self.welcome_email_sent or False,
            "welcome_email_sent_at": self.welcome_email_sent_at.isoformat() if self.welcome_email_sent_at else None,
            "workos_organization_created": self.workos_organization_created or False,
            "workos_organization_created_at": self.workos_organization_created_at.isoformat() if self.workos_organization_created_at else None,
            "sso_configured": self.sso_configured or False,
            "sso_configured_at": self.sso_configured_at.isoformat() if self.sso_configured_at else None,
        }


CLIENT_STATUS_OPTIONS = [
    {"value": ClientStatus.ACTIVE.value, "label": "Ativo", "description": "Cliente em operação normal"},
    {"value": ClientStatus.TRIAL.value, "label": "Trial", "description": "Cliente em período de teste"},
    {"value": ClientStatus.SUSPENDED.value, "label": "Suspenso", "description": "Cliente com conta suspensa"},
    {"value": ClientStatus.CHURNED.value, "label": "Churned", "description": "Cliente que cancelou"},
    {"value": ClientStatus.PENDING_SETUP.value, "label": "Setup Pendente", "description": "Aguardando configuração inicial"},
]

COMPANY_SIZE_OPTIONS = [
    {"value": "small", "label": "Pequena", "description": "Até 50 funcionários"},
    {"value": "medium", "label": "Média", "description": "51 a 200 funcionários"},
    {"value": "large", "label": "Grande", "description": "201 a 1000 funcionários"},
    {"value": "enterprise", "label": "Enterprise", "description": "Mais de 1000 funcionários"},
]
