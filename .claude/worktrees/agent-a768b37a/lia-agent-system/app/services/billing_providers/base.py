"""
Abstract base class for billing providers.
Provides a unified interface for different payment gateway services (Iugu, Vindi).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


@dataclass
class CustomerData:
    """Data class representing a customer in the billing system."""
    id: Optional[str] = None
    external_id: Optional[str] = None
    name: str = ""
    email: str = ""
    document: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriptionData:
    """Data class representing a subscription."""
    id: Optional[str] = None
    external_id: Optional[str] = None
    customer_id: str = ""
    plan_code: str = ""
    plan_name: Optional[str] = None
    status: str = "pending"
    price_cents: int = 0
    currency: str = "BRL"
    billing_cycle: str = "monthly"
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvoiceData:
    """Data class representing an invoice."""
    id: Optional[str] = None
    external_id: Optional[str] = None
    subscription_id: Optional[str] = None
    customer_id: str = ""
    status: str = "pending"
    amount_cents: int = 0
    discount_cents: int = 0
    total_cents: int = 0
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
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentMethodData:
    """Data class representing a payment method."""
    id: Optional[str] = None
    external_id: Optional[str] = None
    customer_id: str = ""
    type: str = "credit_card"
    is_default: bool = False
    card_brand: Optional[str] = None
    card_last_digits: Optional[str] = None
    card_holder_name: Optional[str] = None
    card_expiry_month: Optional[int] = None
    card_expiry_year: Optional[int] = None
    token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BillingResult:
    """Result of a billing operation."""
    success: bool
    provider: str = ""
    operation: str = ""
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


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
        payment_method_id: Optional[str] = None,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
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
        plan_code: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
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
        reason: Optional[str] = None
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
        status: Optional[str] = None,
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
        items: List[Dict[str, Any]],
        due_date: Optional[date] = None,
        payment_method: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
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
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None
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
    def parse_webhook(self, payload: Dict[str, Any], signature: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse and validate a webhook payload.
        
        Args:
            payload: The webhook payload
            signature: Optional webhook signature for validation
        
        Returns:
            Parsed webhook data with event type and relevant information
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
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
