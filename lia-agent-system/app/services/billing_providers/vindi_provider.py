"""
Vindi billing provider implementation.

Vindi is a Brazilian payment gateway that supports:
- Credit card payments
- Boleto bancário
- PIX
- Recurring subscriptions
- Multi-gateway processing

Webhook security (Wave 4 audit 2026-05-22)
──────────────────────────────────────────
Vindi webhooks são autenticados via HMAC-SHA256 do raw body usando
``VINDI_WEBHOOK_SECRET`` (preferido) ou ``VINDI_API_KEY`` (fallback)
como secret. Header: ``X-Vindi-Signature``.

Doc: https://vindi.github.io/api-docs/dist/#!/webhooks

Fail-closed obrigatório (REGRA 4):
- Signature ausente -> 403
- Signature inválida -> 403
- Nenhum secret env -> 403 (NUNCA aceitar webhook em prod sem secret)
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
from app.shared.resilience.circuit_breaker import VINDI_CIRCUIT, circuit_breaker_decorator

logger = logging.getLogger(__name__)


def _verify_vindi_signature(payload_raw: bytes, signature: str) -> bool:
    """Verify Vindi webhook signature via HMAC-SHA256.

    Vindi signs the raw request body and sends hex digest in
    ``X-Vindi-Signature``. We accept ``VINDI_WEBHOOK_SECRET`` (canonical)
    or fall back to ``VINDI_API_KEY`` to ease ops migration.

    Constant-time comparison via ``hmac.compare_digest`` to resist
    timing oracles.

    Fail-closed: returns ``False`` on missing payload, missing signature,
    or missing env secret.

    NEVER logs the secret or the signature value (LGPD/secrets at rest).
    """
    if not signature or not payload_raw:
        return False
    secret_str = os.environ.get("VINDI_WEBHOOK_SECRET", "") or os.environ.get(
        "VINDI_API_KEY", ""
    )
    if not secret_str:
        logger.error(
            "VINDI_WEBHOOK_SECRET (or VINDI_API_KEY fallback) not set — "
            "webhook validation cannot proceed (fail-closed). "
            "All Vindi webhooks will be rejected with 403 until configured."
        )
        return False
    secret = secret_str.encode("utf-8")
    expected = hmac.new(secret, payload_raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


class VindiProvider(BillingProviderBase):
    """
    Vindi payment gateway provider.
    
    API Documentation: https://vindi.github.io/api-docs/dist/
    
    Note: This is a placeholder implementation.
    Actual API calls will be implemented when SDK is installed.
    """
    
    provider_name = "vindi"
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize Vindi provider.
        
        Args:
            api_key: Vindi API key (or from VINDI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("VINDI_API_KEY")
        self.base_url = os.environ.get("VINDI_API_URL", "https://app.vindi.com.br/api/v1")
        self.is_test_mode = os.environ.get("VINDI_TEST_MODE", "true").lower() == "true"
        
        if self.is_test_mode:
            self.base_url = "https://sandbox-app.vindi.com.br/api/v1"
    
    @circuit_breaker_decorator(VINDI_CIRCUIT)
    async def create_customer(self, customer: CustomerData) -> BillingResult:
        """Create a customer in Vindi."""
        logger.info(f"[Vindi] Creating customer: {customer.id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_customer",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        try:
            external_id = f"vindi_cust_{datetime.utcnow().timestamp()}"
            
            return BillingResult(
                success=True,
                provider=self.provider_name,
                operation="create_customer",
                data={
                    "external_id": external_id,
                    "name": customer.name,
                    "email": customer.email,
                    "registry_code": customer.document,
                }
            )
        except Exception as e:
            logger.error(f"[Vindi] Error creating customer: {e}")
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_customer",
                error=str(e),
                error_code="UNKNOWN_ERROR"
            )
    
    async def update_customer(self, external_id: str, customer: CustomerData) -> BillingResult:
        """Update a customer in Vindi."""
        logger.info(f"[Vindi] Updating customer: {external_id}")
        
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
        """Get customer details from Vindi."""
        logger.info(f"[Vindi] Getting customer: {external_id}")
        
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
    
    @circuit_breaker_decorator(VINDI_CIRCUIT)
    async def create_subscription(
        self,
        customer_id: str,
        plan_code: str,
        payment_method_id: str | None = None,
        trial_days: int | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """Create a subscription in Vindi."""
        logger.info(f"[Vindi] Creating subscription for customer {customer_id}, plan {plan_code}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_subscription",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        try:
            external_id = f"vindi_sub_{datetime.utcnow().timestamp()}"
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
                    "start_at": now.isoformat(),
                    "next_billing_at": now.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"[Vindi] Error creating subscription: {e}")
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
        """Update a subscription in Vindi."""
        logger.info(f"[Vindi] Updating subscription: {subscription_id}")
        
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
        """Cancel a subscription in Vindi."""
        logger.info(f"[Vindi] Cancelling subscription: {subscription_id}")
        
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
                "status": "canceled",
                "canceled_at": datetime.utcnow().isoformat(),
            }
        )
    
    async def reactivate_subscription(self, subscription_id: str) -> BillingResult:
        """Reactivate a cancelled subscription in Vindi."""
        logger.info(f"[Vindi] Reactivating subscription: {subscription_id}")
        
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
        """Get subscription details from Vindi."""
        logger.info(f"[Vindi] Getting subscription: {subscription_id}")
        
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
        """List invoices (bills) for a customer in Vindi."""
        logger.info(f"[Vindi] Listing invoices for customer: {customer_id}")
        
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
            data={"bills": [], "total": 0}
        )
    
    async def get_invoice(self, invoice_id: str) -> BillingResult:
        """Get invoice (bill) details from Vindi."""
        logger.info(f"[Vindi] Getting invoice: {invoice_id}")
        
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
    
    @circuit_breaker_decorator(VINDI_CIRCUIT)
    async def create_invoice(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
        due_date: date | None = None,
        payment_method: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> BillingResult:
        """Create an invoice (bill) in Vindi."""
        logger.info(f"[Vindi] Creating invoice for customer: {customer_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="create_invoice",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        external_id = f"vindi_bill_{datetime.utcnow().timestamp()}"
        total_cents = sum(item.get("price_cents", 0) * item.get("quantity", 1) for item in items)
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="create_invoice",
            data={
                "external_id": external_id,
                "customer_id": customer_id,
                "status": "pending",
                "amount": total_cents / 100,
                "due_at": due_date.isoformat() if due_date else None,
            }
        )
    
    async def refund_invoice(
        self,
        invoice_id: str,
        amount_cents: int | None = None,
        reason: str | None = None
    ) -> BillingResult:
        """Refund an invoice (bill) in Vindi."""
        logger.info(f"[Vindi] Refunding invoice: {invoice_id}")
        
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
        """Add a payment profile to a customer in Vindi."""
        logger.info(f"[Vindi] Adding payment method for customer: {customer_id}")
        
        if not self.api_key:
            return BillingResult(
                success=False,
                provider=self.provider_name,
                operation="add_payment_method",
                error="API key not configured",
                error_code="NOT_CONFIGURED"
            )
        
        external_id = f"vindi_pm_{datetime.utcnow().timestamp()}"
        
        return BillingResult(
            success=True,
            provider=self.provider_name,
            operation="add_payment_method",
            data={
                "external_id": external_id,
                "customer_id": customer_id,
                "payment_method_code": payment_method.type,
            }
        )
    
    async def remove_payment_method(self, payment_method_id: str) -> BillingResult:
        """Remove a payment profile from Vindi."""
        logger.info(f"[Vindi] Removing payment method: {payment_method_id}")
        
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
        """Set default payment profile for a customer in Vindi."""
        logger.info(f"[Vindi] Setting default payment method for customer: {customer_id}")
        
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
            data={"customer_id": customer_id, "payment_profile_id": payment_method_id}
        )
    
    def parse_webhook(
        self,
        payload: dict[str, Any],
        signature: str | None = None,
        payload_raw: bytes | None = None,
    ) -> dict[str, Any]:
        """Parse Vindi webhook payload after HMAC validation.

        Wave 4 (2026-05-22): mandatory HMAC-SHA256 validation. Pre-Wave-4
        this method accepted the ``signature`` kwarg but never validated it
        — a forgery primitive.

        Raises:
            WebhookSignatureError: signature missing/invalid or
                ``VINDI_WEBHOOK_SECRET`` unset. Translate to HTTP 403.
        """
        event_data = payload.get("event", {})
        event_type = event_data.get("type", "")

        if not _verify_vindi_signature(payload_raw or b"", signature or ""):
            logger.warning(
                "Vindi webhook rejected: invalid signature",
                extra={
                    "event_type": event_type,
                    "provider": self.provider_name,
                    "payload_present": payload_raw is not None,
                    "signature_present": bool(signature),
                },
            )
            raise WebhookSignatureError("Invalid Vindi webhook signature")

        event_mapping = {
            "bill_created": "invoice.created",
            "bill_paid": "invoice.paid",
            "payment_created": "payment.created",
            "payment_confirmed": "payment.confirmed",
            "payment_refunded": "invoice.refunded",
            "subscription_created": "subscription.created",
            "subscription_activated": "subscription.activated",
            "subscription_renewed": "subscription.renewed",
            "subscription_canceled": "subscription.cancelled",
            "charge_rejected": "invoice.payment_failed",
        }

        return {
            "provider": self.provider_name,
            "event_type": event_mapping.get(event_type, event_type),
            "original_event": event_type,
            "data": event_data.get("data", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_status(self) -> dict[str, Any]:
        """Get Vindi provider status."""
        is_configured = bool(self.api_key)
        
        return {
            "provider": self.provider_name,
            "configured": is_configured,
            "healthy": is_configured,
            "test_mode": self.is_test_mode,
            "details": {
                "api_key_set": bool(self.api_key),
                "base_url": self.base_url,
            }
        }
