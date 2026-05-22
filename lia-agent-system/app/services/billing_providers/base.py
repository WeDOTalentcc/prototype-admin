"""
Abstract base class for billing providers.
Provides a unified interface for different payment gateway services (Iugu, Vindi).
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class CustomerData:
    """Data class representing a customer in the billing system."""
    id: str | None = None
    external_id: str | None = None
    name: str = ""
    email: str = ""
    document: str | None = None
    phone: str | None = None
    address: dict[str, str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriptionData:
    """Data class representing a subscription."""
    id: str | None = None
    external_id: str | None = None
    customer_id: str = ""
    plan_code: str = ""
    plan_name: str | None = None
    status: str = "pending"
    price_cents: int = 0
    currency: str = "BRL"
    billing_cycle: str = "monthly"
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    trial_end: datetime | None = None
    cancelled_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InvoiceData:
    """Data class representing an invoice."""
    id: str | None = None
    external_id: str | None = None
    subscription_id: str | None = None
    customer_id: str = ""
    status: str = "pending"
    amount_cents: int = 0
    discount_cents: int = 0
    total_cents: int = 0
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
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentMethodData:
    """Data class representing a payment method."""
    id: str | None = None
    external_id: str | None = None
    customer_id: str = ""
    type: str = "credit_card"
    is_default: bool = False
    card_brand: str | None = None
    card_last_digits: str | None = None
    card_holder_name: str | None = None
    card_expiry_month: int | None = None
    card_expiry_year: int | None = None
    token: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BillingResult:
    """Result of a billing operation."""
    success: bool
    provider: str = ""
    operation: str = ""
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    raw_response: dict[str, Any] | None = None


class WebhookSignatureError(RuntimeError):
    """Raised when a webhook signature is missing or invalid.

    Translates to HTTP 403 at the API layer. Fail-loud per REGRA 4 (CLAUDE.md):
    invalid signature = potential forgery attempt, NEVER silently downgrade
    to template fallback or accept-as-OK.

    Wave 4 audit 2026-05-22: closes P0 where `signature` param was accepted
    but never validated in `iugu_provider.parse_webhook` /
    `vindi_provider.parse_webhook`. Attacker could forge
    `invoice.payment_failed` -> mark subscription as suspended, OR
    `invoice.paid` -> grant access to features without payment.
    """


class BillingProviderBase(ABC):
    """
    Abstract base class for billing providers.

    Implementations should handle:
    - Customer management
    - Subscription lifecycle
    - Invoice management
    - Payment method management
    - Webhook processing
    """
    
    provider_name: str = "base"
    
    @abstractmethod
    async def create_customer(self, customer: CustomerData) -> BillingResult:
        """
        Create a customer in the payment gateway.
        
        Args:
            customer: CustomerData with customer information
        
        Returns:
            BillingResult with the created customer external_id
        """
        pass
    
    @abstractmethod
    async def update_customer(self, external_id: str, customer: CustomerData) -> BillingResult:
        """
        Update a customer in the payment gateway.
        
        Args:
            external_id: The customer ID in the gateway
            customer: CustomerData with updated information
        
        Returns:
            BillingResult with operation status
        """
        pass
    
    @abstractmethod
    async def get_customer(self, external_id: str) -> BillingResult:
        """
        Get customer details from the payment gateway.
        
        Args:
            external_id: The customer ID in the gateway
        
        Returns:
            BillingResult with customer data
        """
        pass
    
    @abstractmethod
    async def create_subscription(
        self, 
        customer_id: str, 
        plan_code: str,
        payment_method_id: str | None = None,
        trial_days: int | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """
        Create a subscription for a customer.
        
        Args:
            customer_id: The customer external ID
            plan_code: The plan identifier
            payment_method_id: Optional payment method to use
            trial_days: Optional trial period in days
            metadata: Optional metadata for the subscription
        
        Returns:
            BillingResult with subscription data
        """
        pass
    
    @abstractmethod
    async def update_subscription(
        self, 
        subscription_id: str, 
        plan_code: str | None = None,
        payment_method_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """
        Update a subscription.
        
        Args:
            subscription_id: The subscription external ID
            plan_code: Optional new plan to switch to
            payment_method_id: Optional new payment method
            metadata: Optional updated metadata
        
        Returns:
            BillingResult with updated subscription data
        """
        pass
    
    @abstractmethod
    async def cancel_subscription(
        self, 
        subscription_id: str,
        at_period_end: bool = True,
        reason: str | None = None
    ) -> BillingResult:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: The subscription external ID
            at_period_end: If True, cancel at end of billing period
            reason: Optional cancellation reason
        
        Returns:
            BillingResult with cancellation status
        """
        pass
    
    @abstractmethod
    async def reactivate_subscription(self, subscription_id: str) -> BillingResult:
        """
        Reactivate a cancelled subscription.
        
        Args:
            subscription_id: The subscription external ID
        
        Returns:
            BillingResult with reactivation status
        """
        pass
    
    @abstractmethod
    async def get_subscription(self, subscription_id: str) -> BillingResult:
        """
        Get subscription details.
        
        Args:
            subscription_id: The subscription external ID
        
        Returns:
            BillingResult with subscription data
        """
        pass
    
    @abstractmethod
    async def list_invoices(
        self, 
        customer_id: str,
        status: str | None = None,
        limit: int = 100
    ) -> BillingResult:
        """
        List invoices for a customer.
        
        Args:
            customer_id: The customer external ID
            status: Optional filter by status
            limit: Maximum number of invoices to return
        
        Returns:
            BillingResult with list of invoices
        """
        pass
    
    @abstractmethod
    async def get_invoice(self, invoice_id: str) -> BillingResult:
        """
        Get invoice details.
        
        Args:
            invoice_id: The invoice external ID
        
        Returns:
            BillingResult with invoice data
        """
        pass
    
    @abstractmethod
    async def create_invoice(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
        due_date: date | None = None,
        payment_method: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """
        Create a one-off invoice.
        
        Args:
            customer_id: The customer external ID
            items: List of invoice items with description, quantity, price_cents
            due_date: Optional due date
            payment_method: Optional payment method (boleto, pix, credit_card)
            metadata: Optional metadata
        
        Returns:
            BillingResult with created invoice data
        """
        pass
    
    @abstractmethod
    async def refund_invoice(
        self, 
        invoice_id: str,
        amount_cents: int | None = None,
        reason: str | None = None
    ) -> BillingResult:
        """
        Refund an invoice (fully or partially).
        
        Args:
            invoice_id: The invoice external ID
            amount_cents: Optional partial refund amount (full if not provided)
            reason: Optional refund reason
        
        Returns:
            BillingResult with refund status
        """
        pass
    
    @abstractmethod
    async def add_payment_method(
        self,
        customer_id: str,
        payment_method: PaymentMethodData
    ) -> BillingResult:
        """
        Add a payment method to a customer.
        
        Args:
            customer_id: The customer external ID
            payment_method: Payment method data
        
        Returns:
            BillingResult with payment method data
        """
        pass
    
    @abstractmethod
    async def remove_payment_method(self, payment_method_id: str) -> BillingResult:
        """
        Remove a payment method.
        
        Args:
            payment_method_id: The payment method external ID
        
        Returns:
            BillingResult with removal status
        """
        pass
    
    @abstractmethod
    async def set_default_payment_method(
        self, 
        customer_id: str, 
        payment_method_id: str
    ) -> BillingResult:
        """
        Set default payment method for a customer.
        
        Args:
            customer_id: The customer external ID
            payment_method_id: The payment method external ID
        
        Returns:
            BillingResult with operation status
        """
        pass
    
    @abstractmethod
    def parse_webhook(
        self,
        payload: dict[str, Any],
        signature: str | None = None,
        payload_raw: bytes | None = None,
    ) -> dict[str, Any]:
        """
        Parse and validate a webhook payload.

        Args:
            payload: The webhook payload (parsed JSON dict).
            signature: HMAC signature from the provider header
                (Iugu: ``X-Iugu-Signature``, Vindi: ``X-Vindi-Signature``).
                Required for canonical providers — fail-loud if missing.
            payload_raw: Raw request body bytes for HMAC computation.
                MUST be the exact bytes the provider signed. JSON re-serialization
                after parsing breaks the signature (whitespace, key order, etc.).

        Returns:
            Parsed webhook data with event type and relevant information.

        Raises:
            WebhookSignatureError: signature missing/invalid (canonical providers).
                Translate to HTTP 403 at the API layer.
        """
        pass
    
    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Get provider status for health checks.
        
        Returns:
            Dictionary with status information:
            - provider: Provider name
            - configured: Whether API key is set
            - healthy: Whether provider is operational
            - details: Additional status details
        """
        pass
    
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        status = self.get_status()
        return status.get("configured", False)
    
    def is_healthy(self) -> bool:
        """Check if the provider is healthy and ready for operations."""
        status = self.get_status()
        return status.get("healthy", False)
