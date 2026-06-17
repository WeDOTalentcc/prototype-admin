"""
Iugu billing provider implementation.

Iugu is a Brazilian payment gateway that supports:
- Credit card payments
- Boleto bancário
- PIX
- Recurring subscriptions

Webhook security (Wave 4 audit 2026-05-22)
──────────────────────────────────────────
Iugu webhooks são autenticados via HMAC-SHA256 do raw body usando
``IUGU_API_TOKEN`` como secret. Header: ``X-Iugu-Signature``.

Doc: https://dev.iugu.com/reference/webhook-validacao

Fail-closed obrigatório (REGRA 4):
- Signature ausente -> 403
- Signature inválida -> 403
- IUGU_API_TOKEN ausente -> 403 (NUNCA aceitar webhook em prod sem secret)

Atacante forjando ``invoice.paid`` poderia conceder acesso à plataforma sem
pagamento. Forjando ``subscription.suspended`` poderia DoS contra cliente real.
"""
import hashlib
import hmac
import logging
import os
from datetime import date, datetime
from typing import Any


from app.services.billing_providers.base import (
    BillingProviderBase,
    BillingResult,
    CustomerData,
    PaymentMethodData,
    WebhookSignatureError,
)
from app.shared.resilience.circuit_breaker import IUGU_CIRCUIT, circuit_breaker_decorator

logger = logging.getLogger(__name__)


def _verify_iugu_signature(payload_raw: bytes, signature: str) -> bool:
    """Verify Iugu webhook signature via HMAC-SHA256.

    Iugu signs the raw request body with ``IUGU_API_TOKEN`` and sends the
    hex digest in ``X-Iugu-Signature``. Constant-time comparison via
    ``hmac.compare_digest`` to resist timing oracles.

    Fail-closed: returns ``False`` if either ``payload_raw`` is empty,
    ``signature`` is empty, or ``IUGU_API_TOKEN`` env var is unset.

    NEVER logs the secret or the signature value (LGPD/secrets at rest).
    """
    if not signature or not payload_raw:
        return False
    secret_str = os.environ.get("IUGU_API_TOKEN", "")
    if not secret_str:
        logger.error(
            "IUGU_API_TOKEN not set — webhook validation cannot proceed (fail-closed). "
            "All Iugu webhooks will be rejected with 403 until configured."
        )
        return False
    secret = secret_str.encode("utf-8")
    expected = hmac.new(secret, payload_raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


class IuguProvider(BillingProviderBase):
    """
    Iugu payment gateway provider.
    
    API Documentation: https://dev.iugu.com/reference
    
    Note: This is a placeholder implementation. 
    Actual API calls will be implemented when SDK is installed.
    """
    
    provider_name = "iugu"
    
    def __init__(self, api_key: str | None = None, account_id: str | None = None):
        """
        Initialize Iugu provider.
        
        Args:
            api_key: Iugu API key (or from IUGU_API_KEY env var)
            account_id: Iugu account ID (or from IUGU_ACCOUNT_ID env var)
        """
        self.api_key = api_key or os.environ.get("IUGU_API_KEY")
        self.account_id = account_id or os.environ.get("IUGU_ACCOUNT_ID")
        self.base_url = "https://api.iugu.com/v1"
        self.is_test_mode = os.environ.get("IUGU_TEST_MODE", "true").lower() == "true"
    
    @circuit_breaker_decorator(IUGU_CIRCUIT)
    async def create_customer(self, customer: CustomerData) -> BillingResult:
        """Create a customer in Iugu."""
        logger.info(f"[Iugu] Creating customer: {customer.id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_customer",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        try:
            external_id = f"iugu_cust_{datetime.utcnow().timestamp()}"
            
            return BillingResult(
                success=True,
                provider=self.provider_name,
                operation="create_customer",
                data={
                    "external_id": external_id,
                    "name": customer.name,
                    "email": customer.email,
                    "cpf_cnpj": customer.document,
                }
            )
        except Exception as e:
            logger.error(f"[Iugu] Error creating customer: {e}")
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_customer",
                error=str(e),
                error_code="UNKNOWN_ERROR"
            )
    
    async def update_customer(self, external_id: str, customer: CustomerData) -> BillingResult:
        """Update a customer in Iugu."""
        logger.info(f"[Iugu] Updating customer: {external_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="update_customer",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="update_customer",
            data={"external_id": external_id, "updated": True}
        )
    
    async def get_customer(self, external_id: str) -> BillingResult:
        """Get customer details from Iugu."""
        logger.info(f"[Iugu] Getting customer: {external_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="get_customer",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="get_customer",
            data={"external_id": external_id}
        )
    
    @circuit_breaker_decorator(IUGU_CIRCUIT)
    async def create_subscription(
        self,
        customer_id: str,
        plan_code: str,
        payment_method_id: str | None = None,
        trial_days: int | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """Create a subscription in Iugu."""
        logger.info(f"[Iugu] Creating subscription for customer {customer_id}, plan {plan_code}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_subscription",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        try:
            external_id = f"iugu_sub_{datetime.utcnow().timestamp()}"
            now = datetime.utcnow()
            
            return BillingResult(
                success=True,
                provider=self.provider_name,
                operation="create_subscription",
                data={
                    "external_id": external_id,
                    "customer_id": customer_id,
                    "plan_code": plan_code,
                    "status": "active" if not trial_days else "trialing",
                    "current_period_start": now.isoformat(),
                    "current_period_end": now.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"[Iugu] Error creating subscription: {e}")
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_subscription",
                error=str(e),
                error_code="UNKNOWN_ERROR"
            )
    
    async def update_subscription(
        self,
        subscription_id: str,
        plan_code: str | None = None,
        payment_method_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """Update a subscription in Iugu."""
        logger.info(f"[Iugu] Updating subscription: {subscription_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="update_subscription",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="update_subscription",
            data={"external_id": subscription_id, "updated": True}
        )
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
        reason: str | None = None
    ) -> BillingResult:
        """Cancel a subscription in Iugu."""
        logger.info(f"[Iugu] Cancelling subscription: {subscription_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="cancel_subscription",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="cancel_subscription",
            data={
                "external_id": subscription_id,
                "status": "cancelled",
                "cancelled_at": datetime.utcnow().isoformat(),
                "at_period_end": at_period_end,
            }
        )
    
    async def reactivate_subscription(self, subscription_id: str) -> BillingResult:
        """Reactivate a cancelled subscription in Iugu."""
        logger.info(f"[Iugu] Reactivating subscription: {subscription_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="reactivate_subscription",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="reactivate_subscription",
            data={"external_id": subscription_id, "status": "active"}
        )
    
    async def get_subscription(self, subscription_id: str) -> BillingResult:
        """Get subscription details from Iugu."""
        logger.info(f"[Iugu] Getting subscription: {subscription_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="get_subscription",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="get_subscription",
            data={"external_id": subscription_id}
        )
    
    async def list_invoices(
        self,
        customer_id: str,
        status: str | None = None,
        limit: int = 100
    ) -> BillingResult:
        """List invoices for a customer in Iugu."""
        logger.info(f"[Iugu] Listing invoices for customer: {customer_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="list_invoices",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="list_invoices",
            data={"invoices": [], "total": 0}
        )
    
    async def get_invoice(self, invoice_id: str) -> BillingResult:
        """Get invoice details from Iugu."""
        logger.info(f"[Iugu] Getting invoice: {invoice_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="get_invoice",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="get_invoice",
            data={"external_id": invoice_id}
        )
    
    @circuit_breaker_decorator(IUGU_CIRCUIT)
    async def create_invoice(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
        due_date: date | None = None,
        payment_method: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """Create an invoice in Iugu."""
        logger.info(f"[Iugu] Creating invoice for customer: {customer_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_invoice",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        external_id = f"iugu_inv_{datetime.utcnow().timestamp()}"
        total_cents = sum(item.get("price_cents", 0) * item.get("quantity", 1) for item in items)
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="create_invoice",
            data={
                "external_id": external_id,
                "customer_id": customer_id,
                "status": "pending",
                "total_cents": total_cents,
                "due_date": due_date.isoformat() if due_date else None,
            }
        )
    
    async def refund_invoice(
        self,
        invoice_id: str,
        amount_cents: int | None = None,
        reason: str | None = None
    ) -> BillingResult:
        """Refund an invoice in Iugu."""
        logger.info(f"[Iugu] Refunding invoice: {invoice_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="refund_invoice",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="refund_invoice",
            data={"external_id": invoice_id, "status": "refunded"}
        )
    
    async def add_payment_method(
        self,
        customer_id: str,
        payment_method: PaymentMethodData
    ) -> BillingResult:
        """Add a payment method to a customer in Iugu."""
        logger.info(f"[Iugu] Adding payment method for customer: {customer_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="add_payment_method",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        external_id = f"iugu_pm_{datetime.utcnow().timestamp()}"
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="add_payment_method",
            data={
                "external_id": external_id,
                "customer_id": customer_id,
                "type": payment_method.type,
            }
        )
    
    async def remove_payment_method(self, payment_method_id: str) -> BillingResult:
        """Remove a payment method from Iugu."""
        logger.info(f"[Iugu] Removing payment method: {payment_method_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="remove_payment_method",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="remove_payment_method",
            data={"external_id": payment_method_id, "removed": True}
        )
    
    async def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> BillingResult:
        """Set default payment method for a customer in Iugu."""
        logger.info(f"[Iugu] Setting default payment method for customer: {customer_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="set_default_payment_method",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="set_default_payment_method",
            data={"customer_id": customer_id, "payment_method_id": payment_method_id}
        )
    
    def parse_webhook(
        self,
        payload: dict[str, Any],
        signature: str | None = None,
        payload_raw: bytes | None = None,
    ) -> dict[str, Any]:
        """Parse Iugu webhook payload after HMAC validation.

        Wave 4 (2026-05-22): mandatory HMAC-SHA256 validation. Pre-Wave-4
        this method accepted the ``signature`` kwarg but never validated it
        — a forgery primitive.

        Raises:
            WebhookSignatureError: signature missing/invalid or
                ``IUGU_API_TOKEN`` unset. Translate to HTTP 403.
        """
        # NEVER log signature value or payload contents (LGPD + secret hygiene).
        # Log only the event type for observability.
        event_type = payload.get("event")

        if not _verify_iugu_signature(payload_raw or b"", signature or ""):
            logger.warning(
                "Iugu webhook rejected: invalid signature",
                extra={
                    "event_type": event_type,
                    "provider": self.provider_name,
                    "payload_present": payload_raw is not None,
                    "signature_present": bool(signature),
                },
            )
            raise WebhookSignatureError("Invalid Iugu webhook signature")

        event_mapping = {
            "invoice.created": "invoice.created",
            "invoice.status_changed": "invoice.updated",
            "invoice.payment_failed": "invoice.payment_failed",
            "invoice.refund": "invoice.refunded",
            "subscription.created": "subscription.created",
            "subscription.activated": "subscription.activated",
            "subscription.renewed": "subscription.renewed",
            "subscription.suspended": "subscription.suspended",
            "subscription.expired": "subscription.cancelled",
        }

        return {
            "provider": self.provider_name,
            "event_type": event_mapping.get(event_type, event_type),
            "original_event": event_type,
            "data": payload.get("data", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_status(self) -> dict[str, Any]:
        """Get Iugu provider status."""
        is_configured = bool(self.api_key)
        
        return {
            "provider": self.provider_name,
            "configured": is_configured,
            "healthy": is_configured,
            "test_mode": self.is_test_mode,
            "details": {
                "api_key_set": bool(self.api_key),
                "account_id_set": bool(self.account_id),
            }
        }
