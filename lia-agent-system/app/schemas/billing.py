"""
Pydantic schemas for Billing API.
"""

from datetime import date, datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class SubscriptionStatusEnum(StrEnum):
    """Subscription status options."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PENDING = "pending"
    SUSPENDED = "suspended"


class InvoiceStatusEnum(StrEnum):
    """Invoice status options."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethodTypeEnum(StrEnum):
    """Payment method types."""
    CREDIT_CARD = "credit_card"
    BOLETO = "boleto"
    PIX = "pix"
    BANK_TRANSFER = "bank_transfer"


class BillingProviderEnum(StrEnum):
    """Supported billing providers."""
    IUGU = "iugu"
    VINDI = "vindi"


class SubscriptionCreate(WeDoBaseModel):
    """Schema for creating a subscription."""
    client_id: str = Field(..., description="Client account ID")
    plan_code: str = Field(..., description="Plan identifier")
    plan_name: str | None = Field(None, description="Plan display name")
    price_cents: int = Field(0, ge=0, description="Monthly price in cents")
    provider: str | None = Field(None, description="Billing provider (iugu or vindi)")
    trial_days: int | None = Field(None, ge=0, description="Trial period in days")
    billing_cycle: str = Field("monthly", description="Billing cycle (monthly or yearly)")
    payment_method_id: str | None = Field(None, description="External payment method ID")

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


class SubscriptionUpdate(WeDoBaseModel):
    """Schema for updating a subscription."""
    plan_code: str | None = Field(None, description="New plan code")
    plan_name: str | None = Field(None, description="New plan name")
    price_cents: int | None = Field(None, ge=0, description="New price in cents")
    status: str | None = Field(None, description="New status")

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
    reason: str | None = Field(None, description="Cancellation reason")

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
    external_id: str | None = None
    external_customer_id: str | None = None
    plan_code: str
    plan_name: str | None = None
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    trial_end: datetime | None = None
    price_cents: int
    currency: str = "BRL"
    billing_cycle: str
    billing_day: int | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Schema for paginated subscription list response."""
    subscriptions: list[SubscriptionResponse]
    total: int
    limit: int
    offset: int


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""
    id: str
    subscription_id: str
    client_id: str
    external_id: str | None = None
    provider: str
    status: str
    amount_cents: int
    discount_cents: int = 0
    total_cents: int
    currency: str = "BRL"
    due_date: date | None = None
    paid_at: datetime | None = None
    invoice_url: str | None = None
    pdf_url: str | None = None
    boleto_url: str | None = None
    boleto_barcode: str | None = None
    pix_qrcode: str | None = None
    pix_qrcode_url: str | None = None
    payment_method: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list response."""
    invoices: list[InvoiceResponse]
    total: int
    limit: int
    offset: int


class RefundRequest(WeDoBaseModel):
    """Schema for refund request."""
    amount_cents: int | None = Field(None, ge=0, description="Partial refund amount in cents (None for full refund)")
    reason: str | None = Field(None, description="Refund reason")

    class Config:
        json_schema_extra = {
            "example": {
                "amount_cents": 15000,
                "reason": "Cobranca duplicada"
            }
        }


class PaymentMethodCreate(WeDoBaseModel):
    """Schema for creating a payment method."""
    client_id: str = Field(..., description="Client account ID")
    subscription_id: str = Field(..., description="Subscription ID")
    payment_type: str = Field(..., description="Payment type (credit_card, boleto, pix)")
    card_token: str | None = Field(None, description="Tokenized card data")
    card_brand: str | None = Field(None, description="Card brand")
    card_last_digits: str | None = Field(None, max_length=4, description="Last 4 digits of card")
    card_holder_name: str | None = Field(None, description="Card holder name")
    card_expiry_month: int | None = Field(None, ge=1, le=12, description="Card expiry month")
    card_expiry_year: int | None = Field(None, description="Card expiry year")
    set_as_default: bool = Field(True, description="Set as default payment method")
    billing_name: str | None = Field(None, description="Billing name")
    billing_email: str | None = Field(None, description="Billing email")
    billing_document: str | None = Field(None, description="Billing CPF/CNPJ")
    billing_phone: str | None = Field(None, description="Billing phone")

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
    external_id: str | None = None
    provider: str
    type: str
    is_default: bool
    is_active: bool
    card_brand: str | None = None
    card_last_digits: str | None = None
    card_holder_name: str | None = None
    card_expiry_month: int | None = None
    card_expiry_year: int | None = None
    billing_name: str | None = None
    billing_email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class PaymentMethodListResponse(BaseModel):
    """Schema for payment method list response."""
    payment_methods: list[PaymentMethodResponse]
    total: int


class WebhookPayload(WeDoBaseModel):
    """Schema for webhook payload."""
    event: str | None = Field(None, description="Event type")
    data: dict[str, Any] | None = Field(default_factory=dict, description="Event data")

    class Config:
        extra = "allow"


class BillingStatusResponse(BaseModel):
    """Schema for billing status response."""
    status: str
    providers: dict[str, dict[str, Any]]
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
