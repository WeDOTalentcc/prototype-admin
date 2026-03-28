"""
Pydantic schemas for Billing API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class SubscriptionStatusEnum(str, Enum):
    """Subscription status options."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PENDING = "pending"
    SUSPENDED = "suspended"


class InvoiceStatusEnum(str, Enum):
    """Invoice status options."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethodTypeEnum(str, Enum):
    """Payment method types."""
    CREDIT_CARD = "credit_card"
    BOLETO = "boleto"
    PIX = "pix"
    BANK_TRANSFER = "bank_transfer"


class BillingProviderEnum(str, Enum):
    """Supported billing providers."""
    IUGU = "iugu"
    VINDI = "vindi"


class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription."""
    client_id: str = Field(..., description="Client account ID")
    plan_code: str = Field(..., description="Plan identifier")
    plan_name: Optional[str] = Field(None, description="Plan display name")
    price_cents: int = Field(0, ge=0, description="Monthly price in cents")
    provider: Optional[str] = Field(None, description="Billing provider (iugu or vindi)")
    trial_days: Optional[int] = Field(None, ge=0, description="Trial period in days")
    billing_cycle: str = Field("monthly", description="Billing cycle (monthly or yearly)")
    payment_method_id: Optional[str] = Field(None, description="External payment method ID")

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "plan_code": "professional",
                "plan_name": "Plano Profissional",
                "price_cents": 29900,
                "provider": "iugu",
                "trial_days": 14,
                "billing_cycle": "monthly"
            }
        }


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    plan_code: Optional[str] = Field(None, description="New plan code")
    plan_name: Optional[str] = Field(None, description="New plan name")
    price_cents: Optional[int] = Field(None, ge=0, description="New price in cents")
    status: Optional[str] = Field(None, description="New status")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_code": "enterprise",
                "plan_name": "Plano Enterprise",
                "price_cents": 99900
            }
        }


class SubscriptionCancel(BaseModel):
    """Schema for cancelling a subscription."""
    at_period_end: bool = Field(True, description="Cancel at end of billing period")
    reason: Optional[str] = Field(None, description="Cancellation reason")

    class Config:
        json_schema_extra = {
            "example": {
                "at_period_end": True,
                "reason": "Cliente solicitou cancelamento"
            }
        }


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""
    id: str
    client_id: str
    provider: str
    external_id: Optional[str] = None
    external_customer_id: Optional[str] = None
    plan_code: str
    plan_name: Optional[str] = None
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    price_cents: int
    currency: str = "BRL"
    billing_cycle: str
    billing_day: Optional[int] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Schema for paginated subscription list response."""
    subscriptions: List[SubscriptionResponse]
    total: int
    limit: int
    offset: int


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""
    id: str
    subscription_id: str
    client_id: str
    external_id: Optional[str] = None
    provider: str
    status: str
    amount_cents: int
    discount_cents: int = 0
    total_cents: int
    currency: str = "BRL"
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    invoice_url: Optional[str] = None
    pdf_url: Optional[str] = None
    boleto_url: Optional[str] = None
    boleto_barcode: Optional[str] = None
    pix_qrcode: Optional[str] = None
    pix_qrcode_url: Optional[str] = None
    payment_method: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list response."""
    invoices: List[InvoiceResponse]
    total: int
    limit: int
    offset: int


class RefundRequest(BaseModel):
    """Schema for refund request."""
    amount_cents: Optional[int] = Field(None, ge=0, description="Partial refund amount in cents (None for full refund)")
    reason: Optional[str] = Field(None, description="Refund reason")

    class Config:
        json_schema_extra = {
            "example": {
                "amount_cents": 15000,
                "reason": "Cobranca duplicada"
            }
        }


class PaymentMethodCreate(BaseModel):
    """Schema for creating a payment method."""
    client_id: str = Field(..., description="Client account ID")
    subscription_id: str = Field(..., description="Subscription ID")
    payment_type: str = Field(..., description="Payment type (credit_card, boleto, pix)")
    card_token: Optional[str] = Field(None, description="Tokenized card data")
    card_brand: Optional[str] = Field(None, description="Card brand")
    card_last_digits: Optional[str] = Field(None, max_length=4, description="Last 4 digits of card")
    card_holder_name: Optional[str] = Field(None, description="Card holder name")
    card_expiry_month: Optional[int] = Field(None, ge=1, le=12, description="Card expiry month")
    card_expiry_year: Optional[int] = Field(None, description="Card expiry year")
    set_as_default: bool = Field(True, description="Set as default payment method")
    billing_name: Optional[str] = Field(None, description="Billing name")
    billing_email: Optional[str] = Field(None, description="Billing email")
    billing_document: Optional[str] = Field(None, description="Billing CPF/CNPJ")
    billing_phone: Optional[str] = Field(None, description="Billing phone")

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "subscription_id": "660e8400-e29b-41d4-a716-446655440001",
                "payment_type": "credit_card",
                "card_token": "tok_xxxxxxxxxxxxx",
                "card_brand": "visa",
                "card_last_digits": "4242",
                "card_holder_name": "JOAO SILVA",
                "card_expiry_month": 12,
                "card_expiry_year": 2028,
                "set_as_default": True
            }
        }


class PaymentMethodResponse(BaseModel):
    """Schema for payment method response."""
    id: str
    subscription_id: str
    client_id: str
    external_id: Optional[str] = None
    provider: str
    type: str
    is_default: bool
    is_active: bool
    card_brand: Optional[str] = None
    card_last_digits: Optional[str] = None
    card_holder_name: Optional[str] = None
    card_expiry_month: Optional[int] = None
    card_expiry_year: Optional[int] = None
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentMethodListResponse(BaseModel):
    """Schema for payment method list response."""
    payment_methods: List[PaymentMethodResponse]
    total: int


class WebhookPayload(BaseModel):
    """Schema for webhook payload."""
    event: Optional[str] = Field(None, description="Event type")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event data")

    class Config:
        extra = "allow"


class BillingStatusResponse(BaseModel):
    """Schema for billing status response."""
    status: str
    providers: Dict[str, Dict[str, Any]]
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "providers": {
                    "iugu": {"status": "connected", "configured": True},
                    "vindi": {"status": "connected", "configured": True}
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
