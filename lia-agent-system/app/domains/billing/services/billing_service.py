"""
Billing service for subscription management.

Provides a unified interface for managing subscriptions, invoices,
and payment methods using Iugu or Vindi as the payment gateway.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.billing import (
    Invoice,
    InvoiceStatus,
    PaymentMethod,
    Subscription,
    SubscriptionStatus,
)
from lia_models.client_account import ClientAccount
from app.domains.billing.repositories.billing_repository import BillingRepository
from app.services.billing_providers.base import (
    BillingProviderBase,
    CustomerData,
    PaymentMethodData,
)
from app.services.billing_providers.iugu_provider import IuguProvider
from app.services.billing_providers.vindi_provider import VindiProvider

logger = logging.getLogger(__name__)


class BillingService:
    """
    Main billing service for subscription management.
    
    Handles all billing operations and abstracts away the underlying
    payment gateway (Iugu or Vindi).
    """
    
    def __init__(self, db: AsyncSession, default_provider: str = "iugu"):
        """
        Initialize billing service.
        
        Args:
            db: Database session
            default_provider: Default billing provider ('iugu' or 'vindi')
        """
        self.db = db
        self.default_provider = default_provider
        self._repo = BillingRepository(db)
        self._providers: dict[str, BillingProviderBase] = {
            "iugu": IuguProvider(),
            "vindi": VindiProvider(),
        }
    
    def get_provider(self, provider_name: str | None = None) -> BillingProviderBase:
        """Get a billing provider instance."""
        name = provider_name or self.default_provider
        if name not in self._providers:
            raise ValueError(f"Unknown billing provider: {name}")
        return self._providers[name]
    
    async def get_client(self, client_id: UUID) -> ClientAccount | None:
        """Get client account by ID."""
        return await self._repo.get_client_by_id(client_id)

    async def get_subscription(self, subscription_id: UUID) -> Subscription | None:
        """Get subscription by ID."""
        return await self._repo.get_subscription_by_id(subscription_id)

    async def get_active_subscription(self, client_id: UUID) -> Subscription | None:
        """Get active subscription for a client."""
        return await self._repo.get_active_subscription_for_client(
            client_id,
            active_statuses=[
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.TRIALING.value,
            ],
        )
    
    async def create_subscription(
        self,
        client_id: UUID,
        plan_code: str,
        plan_name: str | None = None,
        price_cents: int = 0,
        provider: str | None = None,
        trial_days: int | None = None,
        billing_cycle: str = "monthly",
        payment_method_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new subscription for a client.
        
        Args:
            client_id: The client account ID
            plan_code: The plan identifier
            plan_name: Optional plan display name
            price_cents: Monthly price in cents
            provider: Payment provider ('iugu' or 'vindi')
            trial_days: Optional trial period in days
            billing_cycle: Billing cycle ('monthly', 'yearly')
            payment_method_id: Optional payment method external ID
        
        Returns:
            Dictionary with subscription data and status
        """
        client = await self.get_client(client_id)
        if not client:
            return {"success": False, "error": "Client not found"}
        
        existing = await self.get_active_subscription(client_id)
        if existing:
            return {
                "success": False,
                "error": "Client already has an active subscription",
                "subscription_id": str(existing.id)
            }
        
        provider_name = provider or self.default_provider
        billing_provider = self.get_provider(provider_name)
        
        customer_data = CustomerData(
            name=client.name,
            email=client.primary_email or "",
            document=client.cnpj,
            phone=client.primary_phone,
        )
        customer_result = await billing_provider.create_customer(customer_data)
        
        if not customer_result.success:
            logger.error(f"Failed to create customer: {customer_result.error}")
            return {
                "success": False,
                "error": f"Failed to create customer in {provider_name}",
                "details": customer_result.error
            }
        
        external_customer_id = customer_result.data.get("external_id")
        
        sub_result = await billing_provider.create_subscription(
            customer_id=external_customer_id,
            plan_code=plan_code,
            payment_method_id=payment_method_id,
            trial_days=trial_days,
        )
        
        if not sub_result.success:
            logger.error(f"Failed to create subscription: {sub_result.error}")
            return {
                "success": False,
                "error": f"Failed to create subscription in {provider_name}",
                "details": sub_result.error
            }
        
        now = datetime.utcnow()
        initial_status = SubscriptionStatus.TRIALING.value if trial_days else SubscriptionStatus.ACTIVE.value
        
        subscription = Subscription(
            client_id=client_id,
            provider=provider_name,
            external_id=sub_result.data.get("external_id"),
            external_customer_id=external_customer_id,
            plan_code=plan_code,
            plan_name=plan_name,
            status=initial_status,
            current_period_start=now,
            current_period_end=now,
            price_cents=price_cents,
            billing_cycle=billing_cycle,
        )
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"Created subscription {subscription.id} for client {client_id}")
        
        return {
            "success": True,
            "subscription": subscription.to_dict(),
            "provider": provider_name,
        }
    
    async def cancel_subscription(
        self,
        subscription_id: UUID,
        at_period_end: bool = True,
        reason: str | None = None
    ) -> dict[str, Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: The subscription ID
            at_period_end: If True, cancel at end of billing period
            reason: Optional cancellation reason
        
        Returns:
            Dictionary with cancellation status
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return {"success": False, "error": "Subscription not found"}
        
        if subscription.status == SubscriptionStatus.CANCELLED.value:
            return {"success": False, "error": "Subscription already cancelled"}
        
        billing_provider = self.get_provider(subscription.provider)
        
        if subscription.external_id:
            result = await billing_provider.cancel_subscription(
                subscription_id=subscription.external_id,
                at_period_end=at_period_end,
                reason=reason
            )
            
            if not result.success:
                logger.warning(f"Failed to cancel in gateway: {result.error}")
        
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.cancelled_at = datetime.utcnow()
        subscription.cancellation_reason = reason
        subscription.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"Cancelled subscription {subscription_id}")
        
        return {
            "success": True,
            "subscription": subscription.to_dict(),
        }
    
    async def reactivate_subscription(self, subscription_id: UUID) -> dict[str, Any]:
        """
        Reactivate a cancelled subscription.
        
        Args:
            subscription_id: The subscription ID
        
        Returns:
            Dictionary with reactivation status
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return {"success": False, "error": "Subscription not found"}
        
        if subscription.status != SubscriptionStatus.CANCELLED.value:
            return {"success": False, "error": "Subscription is not cancelled"}
        
        billing_provider = self.get_provider(subscription.provider)
        
        if subscription.external_id:
            result = await billing_provider.reactivate_subscription(subscription.external_id)
            
            if not result.success:
                logger.warning(f"Failed to reactivate in gateway: {result.error}")
        
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.cancelled_at = None
        subscription.cancellation_reason = None
        subscription.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"Reactivated subscription {subscription_id}")
        
        return {
            "success": True,
            "subscription": subscription.to_dict(),
        }
    
    async def change_plan(
        self,
        subscription_id: UUID,
        new_plan_code: str,
        new_plan_name: str | None = None,
        new_price_cents: int | None = None
    ) -> dict[str, Any]:
        """
        Change the plan of an existing subscription.
        
        Args:
            subscription_id: The subscription ID
            new_plan_code: The new plan identifier
            new_plan_name: Optional new plan display name
            new_price_cents: Optional new price in cents
        
        Returns:
            Dictionary with update status
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return {"success": False, "error": "Subscription not found"}
        
        if not subscription.is_active:
            return {"success": False, "error": "Cannot change plan on inactive subscription"}
        
        billing_provider = self.get_provider(subscription.provider)
        
        if subscription.external_id:
            result = await billing_provider.update_subscription(
                subscription_id=subscription.external_id,
                plan_code=new_plan_code
            )
            
            if not result.success:
                logger.warning(f"Failed to update in gateway: {result.error}")
        
        subscription.plan_code = new_plan_code
        if new_plan_name:
            subscription.plan_name = new_plan_name
        if new_price_cents is not None:
            subscription.price_cents = new_price_cents
        subscription.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Changed plan for subscription {subscription_id} to {new_plan_code}")
        
        return {
            "success": True,
            "subscription": subscription.to_dict(),
        }
    
    async def list_invoices(
        self,
        client_id: UUID,
        status: str | None = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        List invoices for a client.
        
        Args:
            client_id: The client account ID
            status: Optional filter by status
            limit: Maximum number of invoices
        
        Returns:
            List of invoice dictionaries
        """
        invoices = await self._repo.list_invoices_for_client(
            client_id=client_id,
            status=status,
            limit=limit,
        )
        return [inv.to_dict() for inv in invoices]

    async def get_invoice(self, invoice_id: UUID) -> dict[str, Any] | None:
        """Get invoice by ID."""
        invoice = await self._repo.get_invoice_by_id(invoice_id)
        return invoice.to_dict() if invoice else None
    
    async def sync_invoices(self, subscription_id: UUID) -> dict[str, Any]:
        """
        Sync invoices from the payment gateway.
        
        Args:
            subscription_id: The subscription ID
        
        Returns:
            Dictionary with sync status
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return {"success": False, "error": "Subscription not found"}
        
        if not subscription.external_customer_id:
            return {"success": False, "error": "No external customer ID"}
        
        billing_provider = self.get_provider(subscription.provider)
        result = await billing_provider.list_invoices(subscription.external_customer_id)
        
        if not result.success:
            return {"success": False, "error": result.error}
        
        synced_count = 0
        invoices_data = result.data.get("invoices", []) or result.data.get("bills", [])
        
        for inv_data in invoices_data:
            external_id = inv_data.get("id") or inv_data.get("external_id")

            existing_invoice = await self._repo.get_invoice_by_external_and_provider(
                external_id=str(external_id),
                provider=subscription.provider,
            )

            if not existing_invoice:
                invoice = Invoice(
                    subscription_id=subscription.id,
                    client_id=subscription.client_id,
                    provider=subscription.provider,
                    external_id=str(external_id),
                    status=inv_data.get("status", "pending"),
                    amount_cents=int(inv_data.get("total_cents", 0) or inv_data.get("amount", 0) * 100),
                    total_cents=int(inv_data.get("total_cents", 0) or inv_data.get("amount", 0) * 100),
                )
                self.db.add(invoice)
                synced_count += 1
        
        await self.db.commit()
        
        logger.info(f"Synced {synced_count} invoices for subscription {subscription_id}")
        
        return {
            "success": True,
            "synced": synced_count,
            "total": len(invoices_data)
        }
    
    async def add_payment_method(
        self,
        subscription_id: UUID,
        payment_type: str,
        card_token: str | None = None,
        card_data: dict[str, Any] | None = None,
        set_as_default: bool = True
    ) -> dict[str, Any]:
        """
        Add a payment method to a subscription.
        
        Args:
            subscription_id: The subscription ID
            payment_type: Type of payment (credit_card, boleto, pix)
            card_token: Optional tokenized card data
            card_data: Optional card details (for display only)
            set_as_default: Whether to set as default payment method
        
        Returns:
            Dictionary with payment method data
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return {"success": False, "error": "Subscription not found"}
        
        billing_provider = self.get_provider(subscription.provider)
        
        pm_data = PaymentMethodData(
            customer_id=subscription.external_customer_id or "",
            type=payment_type,
            is_default=set_as_default,
            token=card_token,
        )
        
        if card_data:
            pm_data.card_brand = card_data.get("brand")
            pm_data.card_last_digits = card_data.get("last_digits")
            pm_data.card_holder_name = card_data.get("holder_name")
            pm_data.card_expiry_month = card_data.get("expiry_month")
            pm_data.card_expiry_year = card_data.get("expiry_year")
        
        result = await billing_provider.add_payment_method(
            subscription.external_customer_id or "",
            pm_data
        )
        
        if not result.success:
            return {"success": False, "error": result.error}
        
        if set_as_default:
            await self.db.execute(
                PaymentMethod.__table__.update()
                .where(PaymentMethod.subscription_id == subscription_id)
                .values(is_default=False)
            )
        
        payment_method = PaymentMethod(
            subscription_id=subscription_id,
            client_id=subscription.client_id,
            provider=subscription.provider,
            external_id=result.data.get("external_id"),
            type=payment_type,
            is_default=set_as_default,
            card_brand=pm_data.card_brand,
            card_last_digits=pm_data.card_last_digits,
            card_holder_name=pm_data.card_holder_name,
            card_expiry_month=pm_data.card_expiry_month,
            card_expiry_year=pm_data.card_expiry_year,
        )
        
        self.db.add(payment_method)
        await self.db.commit()
        await self.db.refresh(payment_method)
        
        logger.info(f"Added payment method {payment_method.id} to subscription {subscription_id}")
        
        return {
            "success": True,
            "payment_method": payment_method.to_dict(),
        }
    
    async def process_webhook(
        self,
        provider: str,
        payload: dict[str, Any],
        signature: str | None = None,
        payload_raw: bytes | None = None,
    ) -> dict[str, Any]:
        """
        Process a webhook from the payment gateway.

        Args:
            provider: The provider name ('iugu' or 'vindi')
            payload: The webhook payload (parsed JSON).
            signature: HMAC signature header value. Required for canonical
                providers — provider.parse_webhook raises
                WebhookSignatureError if absent/invalid.
            payload_raw: Raw request body bytes. MUST be the bytes the
                provider signed (not a re-serialization of ``payload``).

        Returns:
            Dictionary with processing result.

        Raises:
            WebhookSignatureError: provider signature missing/invalid.
                Caller (API endpoint) must translate to HTTP 403.
        """
        billing_provider = self.get_provider(provider)
        parsed = billing_provider.parse_webhook(
            payload, signature, payload_raw=payload_raw
        )
        
        event_type = parsed.get("event_type", "")
        event_data = parsed.get("data", {})
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Processing {provider} webhook: {event_type}")
        
        if event_type.startswith("subscription."):
            await self._handle_subscription_webhook(provider, event_type, event_data)
        elif event_type.startswith("invoice."):
            await self._handle_invoice_webhook(provider, event_type, event_data)
        
        return {
            "success": True,
            "event_type": event_type,
            "processed": True,
        }
    
    async def _handle_subscription_webhook(
        self,
        provider: str,
        event_type: str,
        data: dict[str, Any]
    ) -> None:
        """Handle subscription-related webhook events."""
        external_id = data.get("id") or data.get("subscription_id")
        if not external_id:
            return

        subscription = await self._repo.get_subscription_by_external_and_provider(
            external_id=str(external_id),
            provider=provider,
        )

        if not subscription:
            logger.warning(f"Subscription not found for external_id: {external_id}")
            return
        
        status_map = {
            "subscription.activated": SubscriptionStatus.ACTIVE.value,
            "subscription.renewed": SubscriptionStatus.ACTIVE.value,
            "subscription.cancelled": SubscriptionStatus.CANCELLED.value,
            "subscription.suspended": SubscriptionStatus.SUSPENDED.value,
        }
        
        if event_type in status_map:
            subscription.status = status_map[event_type]
            subscription.updated_at = datetime.utcnow()
            
            if event_type == "subscription.cancelled":
                subscription.cancelled_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Updated subscription {subscription.id} status to {subscription.status}")
    
    async def _handle_invoice_webhook(
        self,
        provider: str,
        event_type: str,
        data: dict[str, Any]
    ) -> None:
        """Handle invoice-related webhook events."""
        external_id = data.get("id") or data.get("invoice_id") or data.get("bill_id")
        if not external_id:
            return

        invoice = await self._repo.get_invoice_by_external_and_provider(
            external_id=str(external_id),
            provider=provider,
        )

        if not invoice:
            logger.warning(f"Invoice not found for external_id: {external_id}")
            return
        
        status_map = {
            "invoice.paid": InvoiceStatus.PAID.value,
            "invoice.payment_failed": InvoiceStatus.FAILED.value,
            "invoice.refunded": InvoiceStatus.REFUNDED.value,
        }
        
        if event_type in status_map:
            invoice.status = status_map[event_type]
            invoice.updated_at = datetime.utcnow()
            
            if event_type == "invoice.paid":
                invoice.paid_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Updated invoice {invoice.id} status to {invoice.status}")
    
    def get_provider_status(self, provider: str | None = None) -> dict[str, Any]:
        """Get status of billing provider(s)."""
        if provider:
            billing_provider = self.get_provider(provider)
            return billing_provider.get_status()
        
        return {
            name: p.get_status()
            for name, p in self._providers.items()
        }
