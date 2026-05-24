"""
SaaS Metrics models for client-specific financial and usage metrics.

This module provides models for tracking:
- Revenue metrics (MRR, ARR, LTV, CAC)
- Usage metrics (AI credits, users, jobs, storage)
- Health metrics (churn risk, health score, engagement)
- Payment history
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, DateTime, Date, Boolean, Numeric, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from typing import Dict, Any, Optional

from lia_config.database import Base


class ChurnRisk(str, enum.Enum):
    """Churn risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EngagementLevel(str, enum.Enum):
    """Engagement level categories."""
    INACTIVE = "inactive"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    POWER_USER = "power_user"


class PaymentStatus(str, enum.Enum):
    """Payment status options."""
    PAID = "paid"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method types."""
    CARD = "card"
    BOLETO = "boleto"
    PIX = "pix"


class BillingCycle(str, enum.Enum):
    """Billing cycle options."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ClientSaasMetrics(Base):
    """
    Client SaaS revenue metrics.
    
    Tracks financial KPIs for each client including MRR, ARR, LTV, CAC.
    """
    __tablename__ = "client_saas_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    
    mrr = Column(Numeric(12, 2), nullable=False, default=0)
    arr = Column(Numeric(14, 2), nullable=False, default=0)
    ltv = Column(Numeric(14, 2), nullable=True)
    cac = Column(Numeric(12, 2), nullable=True)
    payback_months = Column(Numeric(6, 2), nullable=True)
    
    contract_start = Column(Date, nullable=True)
    contract_end = Column(Date, nullable=True)
    
    plan_name = Column(String(100), nullable=True)
    billing_cycle = Column(String(20), default=BillingCycle.MONTHLY.value)
    
    discount_percent = Column(Numeric(5, 2), default=0)
    currency = Column(String(10), default="BRL")
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_saas_metrics_client', 'client_id'),
        Index('idx_saas_metrics_plan', 'plan_name'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ClientSaasMetrics {self.id} - Client: {self.client_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "clientId": str(self.client_id),
            "mrr": float(self.mrr) if self.mrr else 0,
            "arr": float(self.arr) if self.arr else 0,
            "ltv": float(self.ltv) if self.ltv else None,
            "cac": float(self.cac) if self.cac else None,
            "paybackMonths": float(self.payback_months) if self.payback_months else None,
            "contractStart": self.contract_start.isoformat() if self.contract_start else None,
            "contractEnd": self.contract_end.isoformat() if self.contract_end else None,
            "planName": self.plan_name,
            "billingCycle": self.billing_cycle,
            "discountPercent": float(self.discount_percent) if self.discount_percent else 0,
            "currency": self.currency,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class ClientUsageMetrics(Base):
    """
    Client usage metrics.
    
    Tracks resource usage including AI credits, users, jobs, and storage.
    """
    __tablename__ = "client_usage_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    
    ai_credits_used = Column(Integer, default=0)
    ai_credits_limit = Column(Integer, default=1000)
    
    users_active = Column(Integer, default=0)
    users_limit = Column(Integer, default=10)
    
    jobs_active = Column(Integer, default=0)
    jobs_limit = Column(Integer, default=50)
    
    storage_used_mb = Column(Numeric(12, 2), default=0)
    storage_limit_mb = Column(Numeric(12, 2), default=5120)
    
    api_calls_month = Column(Integer, default=0)
    api_calls_limit = Column(Integer, default=10000)
    
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_usage_metrics_client', 'client_id'),
        Index('idx_usage_metrics_period', 'period_start', 'period_end'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ClientUsageMetrics {self.id} - Client: {self.client_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "clientId": str(self.client_id),
            "aiCreditsUsed": self.ai_credits_used,
            "aiCreditsLimit": self.ai_credits_limit,
            "usersActive": self.users_active,
            "usersLimit": self.users_limit,
            "jobsActive": self.jobs_active,
            "jobsLimit": self.jobs_limit,
            "storageUsedMb": float(self.storage_used_mb) if self.storage_used_mb else 0,
            "storageLimitMb": float(self.storage_limit_mb) if self.storage_limit_mb else 0,
            "apiCallsMonth": self.api_calls_month,
            "apiCallsLimit": self.api_calls_limit,
            "periodStart": self.period_start.isoformat() if self.period_start else None,
            "periodEnd": self.period_end.isoformat() if self.period_end else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def ai_credits_usage_percent(self) -> float:
        """Calculate AI credits usage percentage."""
        if not self.ai_credits_limit or self.ai_credits_limit == 0:
            return 0
        return (self.ai_credits_used / self.ai_credits_limit) * 100
    
    @property
    def storage_usage_percent(self) -> float:
        """Calculate storage usage percentage."""
        if not self.storage_limit_mb or self.storage_limit_mb == 0:
            return 0
        return (float(self.storage_used_mb) / float(self.storage_limit_mb)) * 100


class ClientHealthMetrics(Base):
    """
    Client health metrics.
    
    Tracks client health indicators including churn risk, engagement, and NPS.
    """
    __tablename__ = "client_health_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    
    churn_risk = Column(String(20), default=ChurnRisk.LOW.value)
    health_score = Column(Integer, default=100)
    
    last_login = Column(DateTime, nullable=True)
    days_since_login = Column(Integer, default=0)
    
    nps_score = Column(Integer, nullable=True)
    csat_score = Column(Numeric(3, 2), nullable=True)
    
    support_tickets_open = Column(Integer, default=0)
    support_tickets_total = Column(Integer, default=0)
    avg_response_time_hours = Column(Numeric(8, 2), nullable=True)
    
    engagement_level = Column(String(20), default=EngagementLevel.MEDIUM.value)
    feature_adoption_rate = Column(Numeric(5, 2), default=0)
    
    logins_last_30_days = Column(Integer, default=0)
    actions_last_30_days = Column(Integer, default=0)
    
    risk_factors = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_health_metrics_client', 'client_id'),
        Index('idx_health_metrics_churn_risk', 'churn_risk'),
        Index('idx_health_metrics_health_score', 'health_score'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ClientHealthMetrics {self.id} - Client: {self.client_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "clientId": str(self.client_id),
            "churnRisk": self.churn_risk,
            "healthScore": self.health_score,
            "lastLogin": self.last_login.isoformat() if self.last_login else None,
            "daysSinceLogin": self.days_since_login,
            "npsScore": self.nps_score,
            "csatScore": float(self.csat_score) if self.csat_score else None,
            "supportTicketsOpen": self.support_tickets_open,
            "supportTicketsTotal": self.support_tickets_total,
            "avgResponseTimeHours": float(self.avg_response_time_hours) if self.avg_response_time_hours else None,
            "engagementLevel": self.engagement_level,
            "featureAdoptionRate": float(self.feature_adoption_rate) if self.feature_adoption_rate else 0,
            "loginsLast30Days": self.logins_last_30_days,
            "actionsLast30Days": self.actions_last_30_days,
            "riskFactors": self.risk_factors,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class PaymentHistory(Base):
    """
    Payment history for clients.
    
    Records all payment transactions for billing and audit purposes.
    """
    __tablename__ = "payment_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    
    date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="BRL")
    
    status = Column(String(20), default=PaymentStatus.PENDING.value, index=True)
    method = Column(String(20), default=PaymentMethod.CARD.value)
    
    invoice_id = Column(String(255), nullable=True)
    external_transaction_id = Column(String(255), nullable=True)
    
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    paid_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_payment_history_client', 'client_id'),
        Index('idx_payment_history_date', 'date'),
        Index('idx_payment_history_status', 'status'),
        Index('idx_payment_history_client_date', 'client_id', 'date'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<PaymentHistory {self.id} - Client: {self.client_id} - {self.amount}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "clientId": str(self.client_id),
            "date": self.date.isoformat() if self.date else None,
            "amount": float(self.amount) if self.amount else 0,
            "currency": self.currency,
            "status": self.status,
            "method": self.method,
            "invoiceId": self.invoice_id,
            "externalTransactionId": self.external_transaction_id,
            "description": self.description,
            "notes": self.notes,
            "failureReason": self.failure_reason,
            "retryCount": self.retry_count,
            "paidAt": self.paid_at.isoformat() if self.paid_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_paid(self) -> bool:
        """Check if payment is paid."""
        return self.status == PaymentStatus.PAID.value
    
    @property
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED.value


CHURN_RISK_OPTIONS = [
    {"value": ChurnRisk.LOW.value, "label": "Baixo", "description": "Cliente estável, baixo risco de churn"},
    {"value": ChurnRisk.MEDIUM.value, "label": "Médio", "description": "Alguns sinais de risco"},
    {"value": ChurnRisk.HIGH.value, "label": "Alto", "description": "Alto risco de cancelamento"},
]

ENGAGEMENT_LEVEL_OPTIONS = [
    {"value": EngagementLevel.INACTIVE.value, "label": "Inativo", "description": "Sem atividade recente"},
    {"value": EngagementLevel.LOW.value, "label": "Baixo", "description": "Uso esporádico"},
    {"value": EngagementLevel.MEDIUM.value, "label": "Médio", "description": "Uso regular"},
    {"value": EngagementLevel.HIGH.value, "label": "Alto", "description": "Uso frequente"},
    {"value": EngagementLevel.POWER_USER.value, "label": "Power User", "description": "Uso intensivo"},
]

PAYMENT_STATUS_OPTIONS = [
    {"value": PaymentStatus.PAID.value, "label": "Pago", "description": "Pagamento confirmado"},
    {"value": PaymentStatus.PENDING.value, "label": "Pendente", "description": "Aguardando pagamento"},
    {"value": PaymentStatus.FAILED.value, "label": "Falhou", "description": "Pagamento falhou"},
    {"value": PaymentStatus.REFUNDED.value, "label": "Reembolsado", "description": "Pagamento estornado"},
]

PAYMENT_METHOD_OPTIONS = [
    {"value": PaymentMethod.CARD.value, "label": "Cartão", "description": "Cartão de crédito"},
    {"value": PaymentMethod.BOLETO.value, "label": "Boleto", "description": "Boleto bancário"},
    {"value": PaymentMethod.PIX.value, "label": "PIX", "description": "Pagamento via PIX"},
]
