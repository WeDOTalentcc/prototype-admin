"""
Global Policy model for platform and company-level policy configurations.

Supports policies for:
- Rate limits (per company or global)
- Domain blacklists/whitelists
- Content filters
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from typing import Dict, Any

from lia_config.database import Base


class PolicyType(str, enum.Enum):
    """Types of policies."""
    RATE_LIMIT_COMPANY = "rate_limit_company"
    RATE_LIMIT_GLOBAL = "rate_limit_global"
    BLACKLIST_DOMAINS = "blacklist_domains"
    WHITELIST_DOMAINS = "whitelist_domains"
    CONTENT_FILTER = "content_filter"


class PolicyScope(str, enum.Enum):
    """Scope of policy application."""
    PLATFORM = "platform"
    COMPANY = "company"


class GlobalPolicy(Base):
    """
    Global Policy model.
    
    Stores policy configurations that can be:
    - Platform-wide (company_id is NULL)
    - Company-specific (company_id is set)
    """
    __tablename__ = "global_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # WT-2022 P0.TENANT: TENANT-EXEMPT - tabela global de policies (scope=PLATFORM, company_id NULL p/ platform-wide; documentado linhas 39-40)
    company_id = Column(String(255), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    policy_type = Column(String(50), nullable=False, index=True)
    
    value = Column(JSON, nullable=False, default=dict)
    
    scope = Column(String(20), nullable=False, default=PolicyScope.COMPANY.value, index=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_policy_company_type', 'company_id', 'policy_type'),
        Index('idx_policy_scope_active', 'scope', 'is_active'),
        Index('idx_policy_type_scope', 'policy_type', 'scope'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<GlobalPolicy {self.id} - {self.name} - {self.policy_type}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type,
            "value": self.value or {},
            "scope": self.scope,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


POLICY_TYPES = [
    {
        "type": PolicyType.RATE_LIMIT_COMPANY.value,
        "description": "Rate limit for API requests per company",
        "value_schema": {
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }
    },
    {
        "type": PolicyType.RATE_LIMIT_GLOBAL.value,
        "description": "Global rate limit for platform-wide API requests",
        "value_schema": {
            "requests_per_minute": 1000,
            "requests_per_hour": 10000,
            "requests_per_day": 100000
        }
    },
    {
        "type": PolicyType.BLACKLIST_DOMAINS.value,
        "description": "List of email domains that are blocked",
        "value_schema": {
            "domains": ["spam.com", "blocked.com"]
        }
    },
    {
        "type": PolicyType.WHITELIST_DOMAINS.value,
        "description": "List of allowed email domains (when enabled, only these are accepted)",
        "value_schema": {
            "domains": ["company.com", "partner.com"],
            "enabled": True
        }
    },
    {
        "type": PolicyType.CONTENT_FILTER.value,
        "description": "Content filtering rules for messages and communications",
        "value_schema": {
            "blocked_keywords": ["spam", "inappropriate"],
            "max_message_length": 5000,
            "allow_links": True,
            "allow_attachments": True
        }
    }
]
