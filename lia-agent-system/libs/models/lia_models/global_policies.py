"""
Global Policies models for platform-wide configuration and compliance.

This module provides models for:
- GlobalPolicy: Platform-wide configuration settings
- PolicyAuditLog: Audit trail for policy changes
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from lia_config.database import Base
import enum
import uuid


class PolicyCategory(str, enum.Enum):
    """Categories for global policies."""
    DATA_RETENTION = "data_retention"
    AI_LIMITS = "ai_limits"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class PolicyValueType(str, enum.Enum):
    """Value types for policies."""
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    SELECT = "select"


class PlatformPolicy(Base):
    """
    Global platform policies for configuration and compliance.
    
    Tracks platform-wide settings including:
    - Data retention periods
    - AI usage limits
    - Security settings
    - Compliance requirements
    """
    __tablename__ = "platform_global_policies"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    value_type = Column(String(20), nullable=False)
    current_value = Column(String(500), nullable=False)
    unit = Column(String(50), nullable=True)
    min_value = Column(Numeric(20, 4), nullable=True)
    max_value = Column(Numeric(20, 4), nullable=True)
    options = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    audit_logs = relationship("PlatformPolicyAuditLog", back_populates="policy", lazy="dynamic")
    
    def __repr__(self):
        return f"<PlatformPolicy {self.name} ({self.category})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "value_type": self.value_type,
            "current_value": self.current_value,
            "unit": self.unit,
            "min_value": float(self.min_value) if self.min_value else None,
            "max_value": float(self.max_value) if self.max_value else None,
            "options": self.options,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PlatformPolicyAuditLog(Base):
    """
    Audit log for tracking policy changes.
    
    Tracks:
    - Previous and new values
    - Who made the change
    - When the change was made
    - Reason for the change
    """
    __tablename__ = "platform_policy_audit_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("platform_global_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_value = Column(String(500), nullable=True)
    new_value = Column(String(500), nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=True)
    changed_at = Column(DateTime, server_default=func.now(), index=True)
    change_reason = Column(Text, nullable=True)
    
    policy = relationship("PlatformPolicy", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<PlatformPolicyAuditLog {self.id} for policy {self.policy_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "policy_id": str(self.policy_id),
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "changed_by": str(self.changed_by) if self.changed_by else None,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "change_reason": self.change_reason,
        }


DEFAULT_POLICIES = [
    {
        "name": "candidate_data_retention_months",
        "description": "Number of months to retain candidate data before anonymization",
        "category": "data_retention",
        "value_type": "number",
        "current_value": "24",
        "unit": "months",
        "min_value": 6,
        "max_value": 120,
    },
    {
        "name": "audit_log_retention_years",
        "description": "Number of years to retain audit logs",
        "category": "data_retention",
        "value_type": "number",
        "current_value": "7",
        "unit": "years",
        "min_value": 1,
        "max_value": 20,
    },
    {
        "name": "ai_decision_retention_months",
        "description": "Number of months to retain AI decision records for explainability",
        "category": "data_retention",
        "value_type": "number",
        "current_value": "36",
        "unit": "months",
        "min_value": 12,
        "max_value": 120,
    },
    {
        "name": "max_tokens_per_request",
        "description": "Maximum number of tokens allowed per AI request",
        "category": "ai_limits",
        "value_type": "number",
        "current_value": "4000",
        "unit": "tokens",
        "min_value": 100,
        "max_value": 32000,
    },
    {
        "name": "daily_token_limit_per_client",
        "description": "Maximum daily token usage per client",
        "category": "ai_limits",
        "value_type": "number",
        "current_value": "100000",
        "unit": "tokens",
        "min_value": 1000,
        "max_value": 10000000,
    },
    {
        "name": "rate_limit_requests_per_minute",
        "description": "Maximum API requests allowed per minute",
        "category": "ai_limits",
        "value_type": "number",
        "current_value": "60",
        "unit": "requests/minute",
        "min_value": 10,
        "max_value": 1000,
    },
    {
        "name": "password_min_length",
        "description": "Minimum password length required",
        "category": "security",
        "value_type": "number",
        "current_value": "12",
        "unit": "characters",
        "min_value": 8,
        "max_value": 128,
    },
    {
        "name": "session_timeout_minutes",
        "description": "Session timeout duration",
        "category": "security",
        "value_type": "number",
        "current_value": "60",
        "unit": "minutes",
        "min_value": 5,
        "max_value": 1440,
    },
    {
        "name": "mfa_required",
        "description": "Whether multi-factor authentication is required",
        "category": "security",
        "value_type": "boolean",
        "current_value": "true",
    },
    {
        "name": "max_login_attempts",
        "description": "Maximum failed login attempts before account lockout",
        "category": "security",
        "value_type": "number",
        "current_value": "5",
        "unit": "attempts",
        "min_value": 3,
        "max_value": 20,
    },
    {
        "name": "gdpr_consent_required",
        "description": "Whether GDPR consent is required for data processing",
        "category": "compliance",
        "value_type": "boolean",
        "current_value": "true",
    },
    {
        "name": "lgpd_dpo_required",
        "description": "Whether LGPD Data Protection Officer designation is required",
        "category": "compliance",
        "value_type": "boolean",
        "current_value": "true",
    },
    {
        "name": "bias_audit_frequency",
        "description": "Frequency of AI bias audits",
        "category": "compliance",
        "value_type": "select",
        "current_value": "quarterly",
        "options": ["monthly", "quarterly", "semi_annual", "annual"],
    },
]
