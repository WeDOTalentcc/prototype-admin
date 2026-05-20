"""
Pydantic schemas for SaaS Metrics API.

All schemas use camelCase aliases for frontend compatibility.
"""

from datetime import date, datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class ChurnRiskEnum(StrEnum):
    """Churn risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EngagementLevelEnum(StrEnum):
    """Engagement level categories."""
    INACTIVE = "inactive"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    POWER_USER = "power_user"


class PaymentStatusEnum(StrEnum):
    """Payment status options."""
    PAID = "paid"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethodEnum(StrEnum):
    """Payment method types."""
    CARD = "card"
    BOLETO = "boleto"
    PIX = "pix"


class BillingCycleEnum(StrEnum):
    """Billing cycle options."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ClientSaasMetricsBase(BaseModel):
    """Base schema for SaaS metrics."""
    mrr: float = Field(0, description="Monthly Recurring Revenue", alias="mrr")
    arr: float = Field(0, description="Annual Recurring Revenue", alias="arr")
    ltv: float | None = Field(None, description="Lifetime Value", alias="ltv")
    cac: float | None = Field(None, description="Customer Acquisition Cost", alias="cac")
    payback_months: float | None = Field(None, description="CAC payback period in months", alias="paybackMonths")
    contract_start: date | None = Field(None, description="Contract start date", alias="contractStart")
    contract_end: date | None = Field(None, description="Contract end date", alias="contractEnd")
    plan_name: str | None = Field(None, description="Plan name", alias="planName")
    billing_cycle: str = Field("monthly", description="Billing cycle", alias="billingCycle")
    discount_percent: float = Field(0, description="Discount percentage", alias="discountPercent")
    currency: str = Field("BRL", description="Currency code")

    class Config:
        populate_by_name = True


class ClientSaasMetricsCreate(ClientSaasMetricsBase):
    """Schema for creating SaaS metrics."""
    client_id: str = Field(..., description="Client account ID", alias="clientId")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "clientId": "550e8400-e29b-41d4-a716-446655440000",
                "mrr": 2990.00,
                "arr": 35880.00,
                "planName": "Professional",
                "billingCycle": "monthly"
            }
        }


class ClientSaasMetricsResponse(ClientSaasMetricsBase):
    """Schema for SaaS metrics response."""
    id: str
    client_id: str = Field(..., alias="clientId")
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ClientUsageMetricsBase(BaseModel):
    """Base schema for usage metrics."""
    ai_credits_used: int = Field(0, description="AI credits used", alias="aiCreditsUsed")
    ai_credits_limit: int = Field(1000, description="AI credits limit", alias="aiCreditsLimit")
    users_active: int = Field(0, description="Active users", alias="usersActive")
    users_limit: int = Field(10, description="Users limit", alias="usersLimit")
    jobs_active: int = Field(0, description="Active jobs", alias="jobsActive")
    jobs_limit: int = Field(50, description="Jobs limit", alias="jobsLimit")
    storage_used_mb: float = Field(0, description="Storage used in MB", alias="storageUsedMb")
    storage_limit_mb: float = Field(5120, description="Storage limit in MB", alias="storageLimitMb")
    api_calls_month: int = Field(0, description="API calls this month", alias="apiCallsMonth")
    api_calls_limit: int = Field(10000, description="API calls limit", alias="apiCallsLimit")
    period_start: date | None = Field(None, description="Period start date", alias="periodStart")
    period_end: date | None = Field(None, description="Period end date", alias="periodEnd")

    class Config:
        populate_by_name = True


class ClientUsageMetricsCreate(ClientUsageMetricsBase):
    """Schema for creating usage metrics."""
    client_id: str = Field(..., description="Client account ID", alias="clientId")

    class Config:
        populate_by_name = True


class ClientUsageMetricsResponse(ClientUsageMetricsBase):
    """Schema for usage metrics response."""
    id: str
    client_id: str = Field(..., alias="clientId")
    ai_credits_usage_percent: float | None = Field(None, alias="aiCreditsUsagePercent")
    storage_usage_percent: float | None = Field(None, alias="storageUsagePercent")
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ClientHealthMetricsBase(BaseModel):
    """Base schema for health metrics."""
    churn_risk: str = Field("low", description="Churn risk level", alias="churnRisk")
    health_score: int = Field(100, ge=0, le=100, description="Health score (0-100)", alias="healthScore")
    last_login: datetime | None = Field(None, description="Last login timestamp", alias="lastLogin")
    days_since_login: int = Field(0, description="Days since last login", alias="daysSinceLogin")
    nps_score: int | None = Field(None, ge=-100, le=100, description="NPS score", alias="npsScore")
    csat_score: float | None = Field(None, ge=0, le=5, description="CSAT score", alias="csatScore")
    support_tickets_open: int = Field(0, description="Open support tickets", alias="supportTicketsOpen")
    support_tickets_total: int = Field(0, description="Total support tickets", alias="supportTicketsTotal")
    engagement_level: str = Field("medium", description="Engagement level", alias="engagementLevel")
    feature_adoption_rate: float = Field(0, description="Feature adoption rate", alias="featureAdoptionRate")
    logins_last_30_days: int = Field(0, description="Logins in last 30 days", alias="loginsLast30Days")
    actions_last_30_days: int = Field(0, description="Actions in last 30 days", alias="actionsLast30Days")
    risk_factors: str | None = Field(None, description="Risk factors description", alias="riskFactors")

    class Config:
        populate_by_name = True


class ClientHealthMetricsCreate(ClientHealthMetricsBase):
    """Schema for creating health metrics."""
    client_id: str = Field(..., description="Client account ID", alias="clientId")

    class Config:
        populate_by_name = True


class ClientHealthMetricsResponse(ClientHealthMetricsBase):
    """Schema for health metrics response."""
    id: str
    client_id: str = Field(..., alias="clientId")
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class PaymentHistoryBase(BaseModel):
    """Base schema for payment history."""
    payment_date: date = Field(..., description="Payment date", alias="date")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field("BRL", description="Currency code")
    status: str = Field("pending", description="Payment status")
    method: str = Field("card", description="Payment method")
    invoice_id: str | None = Field(None, description="Invoice ID", alias="invoiceId")
    external_transaction_id: str | None = Field(None, description="External transaction ID", alias="externalTransactionId")
    description: str | None = Field(None, description="Payment description")
    notes: str | None = Field(None, description="Additional notes")

    class Config:
        populate_by_name = True


class PaymentHistoryCreate(PaymentHistoryBase):
    """Schema for creating payment record."""
    client_id: str = Field(..., description="Client account ID", alias="clientId")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "clientId": "550e8400-e29b-41d4-a716-446655440000",
                "date": "2024-01-15",
                "amount": 2990.00,
                "status": "paid",
                "method": "card",
                "description": "Mensalidade Janeiro 2024"
            }
        }


class PaymentHistoryResponse(PaymentHistoryBase):
    """Schema for payment history response."""
    id: str
    client_id: str = Field(..., alias="clientId")
    failure_reason: str | None = Field(None, alias="failureReason")
    retry_count: int = Field(0, alias="retryCount")
    paid_at: datetime | None = Field(None, alias="paidAt")
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class PaymentHistoryListResponse(BaseModel):
    """Schema for paginated payment history list."""
    payments: list[PaymentHistoryResponse]
    total: int
    limit: int
    offset: int

    class Config:
        populate_by_name = True


class ClientAllMetricsResponse(BaseModel):
    """Schema for all metrics combined response."""
    revenue: ClientSaasMetricsResponse | None = None
    usage: ClientUsageMetricsResponse | None = None
    health: ClientHealthMetricsResponse | None = None
    recent_payments: list[PaymentHistoryResponse] = Field(default=[], alias="recentPayments")

    class Config:
        populate_by_name = True


class PlatformAggregateMetrics(BaseModel):
    """Schema for platform-wide aggregated metrics."""
    total_mrr: float = Field(0, description="Total Monthly Recurring Revenue", alias="totalMrr")
    total_arr: float = Field(0, description="Total Annual Recurring Revenue", alias="totalArr")
    total_clients: int = Field(0, description="Total number of clients", alias="totalClients")
    active_clients: int = Field(0, description="Number of active clients", alias="activeClients")
    churned_clients: int = Field(0, description="Number of churned clients", alias="churnedClients")
    avg_mrr: float = Field(0, description="Average MRR per client", alias="avgMrr")
    avg_ltv: float | None = Field(None, description="Average LTV", alias="avgLtv")
    avg_cac: float | None = Field(None, description="Average CAC", alias="avgCac")
    avg_health_score: float = Field(0, description="Average health score", alias="avgHealthScore")
    avg_churn_risk: str = Field("low", description="Average churn risk", alias="avgChurnRisk")
    churn_rate: float = Field(0, description="Churn rate percentage", alias="churnRate")
    low_risk_count: int = Field(0, description="Clients with low churn risk", alias="lowRiskCount")
    medium_risk_count: int = Field(0, description="Clients with medium churn risk", alias="mediumRiskCount")
    high_risk_count: int = Field(0, description="Clients with high churn risk", alias="highRiskCount")
    total_revenue_last_30_days: float = Field(0, description="Total revenue last 30 days", alias="totalRevenueLast30Days")
    pending_payments: int = Field(0, description="Number of pending payments", alias="pendingPayments")
    failed_payments: int = Field(0, description="Number of failed payments", alias="failedPayments")
    currency: str = Field("BRL", description="Currency code")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, alias="calculatedAt")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "totalMrr": 150000.00,
                "totalArr": 1800000.00,
                "totalClients": 50,
                "activeClients": 45,
                "churnedClients": 5,
                "avgMrr": 3000.00,
                "avgHealthScore": 85,
                "avgChurnRisk": "low",
                "churnRate": 2.5,
                "lowRiskCount": 35,
                "mediumRiskCount": 10,
                "highRiskCount": 5,
                "currency": "BRL"
            }
        }


class SaasMetricsUpdate(WeDoBaseModel):
    """Schema for updating SaaS metrics."""
    mrr: float | None = Field(None, alias="mrr")
    arr: float | None = Field(None, alias="arr")
    ltv: float | None = Field(None, alias="ltv")
    cac: float | None = Field(None, alias="cac")
    payback_months: float | None = Field(None, alias="paybackMonths")
    contract_start: date | None = Field(None, alias="contractStart")
    contract_end: date | None = Field(None, alias="contractEnd")
    plan_name: str | None = Field(None, alias="planName")
    billing_cycle: str | None = Field(None, alias="billingCycle")

    class Config:
        populate_by_name = True


class UsageMetricsUpdate(WeDoBaseModel):
    """Schema for updating usage metrics."""
    ai_credits_used: int | None = Field(None, alias="aiCreditsUsed")
    ai_credits_limit: int | None = Field(None, alias="aiCreditsLimit")
    users_active: int | None = Field(None, alias="usersActive")
    users_limit: int | None = Field(None, alias="usersLimit")
    jobs_active: int | None = Field(None, alias="jobsActive")
    jobs_limit: int | None = Field(None, alias="jobsLimit")
    storage_used_mb: float | None = Field(None, alias="storageUsedMb")
    storage_limit_mb: float | None = Field(None, alias="storageLimitMb")

    class Config:
        populate_by_name = True


class HealthMetricsUpdate(WeDoBaseModel):
    """Schema for updating health metrics."""
    churn_risk: str | None = Field(None, alias="churnRisk")
    health_score: int | None = Field(None, ge=0, le=100, alias="healthScore")
    nps_score: int | None = Field(None, ge=-100, le=100, alias="npsScore")
    support_tickets_open: int | None = Field(None, alias="supportTicketsOpen")
    engagement_level: str | None = Field(None, alias="engagementLevel")

    class Config:
        populate_by_name = True


class PlatformMetricsSummary(BaseModel):
    """Platform-wide SaaS metrics summary (legacy compatibility)."""
    mrr: float = Field(default=0, description="Monthly Recurring Revenue in BRL")
    arr: float = Field(default=0, description="Annual Recurring Revenue in BRL")
    total_clients: int = Field(default=0, description="Total number of clients", alias="totalClients")
    active_clients: int = Field(default=0, description="Number of active clients", alias="activeClients")
    trial_clients: int = Field(default=0, description="Number of clients in trial", alias="trialClients")
    churned_clients: int = Field(default=0, description="Number of churned clients", alias="churnedClients")
    total_users: int = Field(default=0, description="Total users across all clients", alias="totalUsers")
    active_users: int = Field(default=0, description="Active users in the last 30 days", alias="activeUsers")
    churn_rate: float = Field(default=0, description="Monthly churn rate percentage", alias="churnRate")
    growth_rate: float = Field(default=0, description="Monthly growth rate percentage", alias="growthRate")
    average_revenue_per_client: float = Field(default=0, description="ARPC in BRL", alias="averageRevenuePerClient")
    total_ai_tokens_used: int = Field(default=0, description="Total AI tokens consumed", alias="totalAiTokensUsed")
    total_ai_cost_cents: int = Field(default=0, description="Total AI cost in cents", alias="totalAiCostCents")
    timestamp: str = Field(default="", description="Timestamp of the metrics")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ClientMetrics(BaseModel):
    """Metrics for a specific client (legacy compatibility)."""
    client_id: str = Field(..., alias="clientId")
    client_name: str = Field(..., alias="clientName")
    status: str
    plan_id: str | None = Field(None, alias="planId")
    mrr: float = Field(default=0, description="Monthly revenue from this client")
    total_users: int = Field(default=0, description="Total users for this client", alias="totalUsers")
    active_users: int = Field(default=0, description="Active users in last 30 days", alias="activeUsers")
    total_jobs: int = Field(default=0, description="Total job vacancies", alias="totalJobs")
    active_jobs: int = Field(default=0, description="Active job vacancies", alias="activeJobs")
    ai_tokens_used: int = Field(default=0, description="AI tokens used this period", alias="aiTokensUsed")
    ai_tokens_limit: int = Field(default=0, description="AI tokens limit", alias="aiTokensLimit")
    ai_usage_percentage: float = Field(default=0, description="AI usage percentage", alias="aiUsagePercentage")
    days_since_signup: int = Field(default=0, description="Days since client signup", alias="daysSinceSignup")
    contract_start: str | None = Field(None, alias="contractStart")
    contract_end: str | None = Field(None, alias="contractEnd")
    health_score: float = Field(default=0, description="Client health score 0-100", alias="healthScore")
    timestamp: str = Field(default="", description="Timestamp of the metrics")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ClientMetricsList(BaseModel):
    """List of client metrics."""
    clients: list[ClientMetrics]
    total: int
    limit: int
    offset: int


class MetricsTrend(BaseModel):
    """Trend data point for metrics over time."""
    date: str
    value: float
    label: str | None = None


class MetricsTrendResponse(BaseModel):
    """Response with trend data for a metric."""
    metric_name: str = Field(..., alias="metricName")
    period_start: str = Field(..., alias="periodStart")
    period_end: str = Field(..., alias="periodEnd")
    data_points: list[MetricsTrend] = Field(..., alias="dataPoints")
    total_change: float = Field(..., alias="totalChange")
    percentage_change: float = Field(..., alias="percentageChange")

    class Config:
        populate_by_name = True


class ChurnAnalysis(BaseModel):
    """Churn analysis data."""
    current_month_churned: int = Field(..., alias="currentMonthChurned")
    previous_month_churned: int = Field(..., alias="previousMonthChurned")
    churn_rate: float = Field(..., alias="churnRate")
    at_risk_clients: int = Field(..., alias="atRiskClients")
    reasons: dict[str, int] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class RevenueBreakdown(BaseModel):
    """Revenue breakdown by plan or category."""
    category: str
    revenue: float
    percentage: float
    client_count: int = Field(..., alias="clientCount")

    class Config:
        populate_by_name = True


class RevenueAnalysis(BaseModel):
    """Revenue analysis response."""
    total_mrr: float = Field(..., alias="totalMrr")
    total_arr: float = Field(..., alias="totalArr")
    by_plan: list[RevenueBreakdown] = Field(..., alias="byPlan")
    by_company_size: list[RevenueBreakdown] = Field(..., alias="byCompanySize")
    growth_rate: float = Field(..., alias="growthRate")

    class Config:
        populate_by_name = True
