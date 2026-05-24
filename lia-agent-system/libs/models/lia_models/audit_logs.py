"""
SOX-Compliant Centralized Audit Logs Module.

This module provides comprehensive audit logging following SOX Section 802 requirements:
- 7-year retention for financial records
- Immutable audit trail
- Comprehensive action tracking across all system components
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from lia_config.database import Base
import enum
import uuid


class ActionCategory(str, enum.Enum):
    """Categories of auditable actions."""
    AUTHENTICATION = "authentication"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    AI_DECISION = "ai_decision"
    FINANCIAL = "financial"
    USER_MANAGEMENT = "user_management"
    SYSTEM = "system"


class AuditStatus(str, enum.Enum):
    """Status of audited actions."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PARTIAL = "partial"


class SOXAuditLog(Base):
    """
    SOX-Compliant Centralized Audit Log.
    
    Tracks all significant system actions with full traceability:
    - Authentication events (login, logout, password changes)
    - Data access (view, export, delete, modify)
    - Configuration changes (settings, policies, permissions)
    - AI decisions (scoring, recommendations, automated actions)
    - Financial operations (billing, subscriptions, credits)
    
    SOX Section 802 Compliance:
    - Minimum 7-year retention for financial records
    - Immutable records (no updates or deletes)
    - Complete audit trail with timestamps
    """
    __tablename__ = "sox_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    user_id = Column(String(255), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)

    # R-011: company_id para multi-tenancy RLS (nullable durante migração gradual)
    # Será tornado NOT NULL após backfill completo (migration 080)
    # TENANT-EXEMPT: SOXAuditLog cross-tenant compliance (auditor WeDOTalent ve todos os tenants)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    client_id = Column(String(255), nullable=True, index=True, server_default="system")
    client_name = Column(String(255), nullable=True)
    
    action = Column(String(255), nullable=False, index=True)
    action_category = Column(String(50), nullable=False, index=True)
    
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    status = Column(String(20), nullable=False, default="success", index=True)
    
    details = Column(JSON, default=dict)
    
    retention_years = Column(Integer, default=7)
    retention_until = Column(DateTime, nullable=True)
    
    request_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_sox_audit_timestamp_client', 'timestamp', 'client_id'),
        Index('idx_sox_audit_action_category', 'action_category', 'timestamp'),
        Index('idx_sox_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_sox_audit_status_timestamp', 'status', 'timestamp'),
        Index('idx_sox_audit_company_timestamp', 'company_id', 'timestamp'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<SOXAuditLog {self.id} - {self.action} by {self.user_email or 'system'}>"
    
    def to_dict(self):
        """Convert audit log to dictionary for API responses."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "company_id": str(self.company_id) if self.company_id else None,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "action": self.action,
            "action_category": self.action_category,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "details": self.details,
            "retention_years": self.retention_years,
            "retention_until": self.retention_until.isoformat() if self.retention_until else None,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditRetentionPolicy(Base):
    """
    Audit Retention Policy Configuration.
    
    Defines retention periods for different categories of audit logs
    based on regulatory requirements (SOX, LGPD, GDPR).
    """
    __tablename__ = "audit_retention_policies"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    category = Column(String(50), nullable=False, unique=True, index=True)
    
    retention_months = Column(Integer, nullable=False)
    
    description = Column(Text, nullable=True)
    
    is_sox_required = Column(Boolean, default=False)
    
    legal_basis = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AuditRetentionPolicy {self.category} - {self.retention_months} months>"
    
    def to_dict(self):
        """Convert retention policy to dictionary for API responses."""
        return {
            "id": str(self.id),
            "category": self.category,
            "retention_months": self.retention_months,
            "description": self.description,
            "is_sox_required": self.is_sox_required,
            "legal_basis": self.legal_basis,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


DEFAULT_RETENTION_POLICIES = [
    {
        "category": "financial",
        "retention_months": 84,
        "description": "Financial records including billing, invoices, and transactions",
        "is_sox_required": True,
        "legal_basis": "SOX Section 802 - 7 year retention"
    },
    {
        "category": "authentication",
        "retention_months": 36,
        "description": "Login, logout, password changes, and session events",
        "is_sox_required": False,
        "legal_basis": "Security best practices - 3 year retention"
    },
    {
        "category": "data_access",
        "retention_months": 60,
        "description": "Data access, export, and deletion events",
        "is_sox_required": True,
        "legal_basis": "SOX/LGPD - 5 year retention"
    },
    {
        "category": "configuration",
        "retention_months": 84,
        "description": "System configuration and settings changes",
        "is_sox_required": True,
        "legal_basis": "SOX Section 802 - 7 year retention"
    },
    {
        "category": "ai_decision",
        "retention_months": 84,
        "description": "AI-driven decisions, scoring, and recommendations",
        "is_sox_required": True,
        "legal_basis": "SOX/AI Ethics - 7 year retention for explainability"
    },
    {
        "category": "user_management",
        "retention_months": 60,
        "description": "User creation, modification, and access control changes",
        "is_sox_required": True,
        "legal_basis": "SOX access controls - 5 year retention"
    },
    {
        "category": "system",
        "retention_months": 24,
        "description": "System events, errors, and operational logs",
        "is_sox_required": False,
        "legal_basis": "Operational requirements - 2 year retention"
    },
]
