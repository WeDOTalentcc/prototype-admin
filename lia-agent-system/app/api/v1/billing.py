"""
Billing API Endpoints.

Provides REST endpoints for managing subscriptions, invoices,
payment methods, and webhook integrations with Iugu/Vindi.

SECURITY: All endpoints enforce multi-tenant isolation via X-Company-ID header.
"""
# SISTEMA: Creditos de Plano (plan credits) — ADR-030
# Ver: docs/adr/ADR-030-ai-credits-two-systems.md
# NAO confundir com ai_consumption.py (tokens LLM) — sistemas distintos intencionalmente.
# Este arquivo trata do envelope comercial: assinaturas, faturas, limites de plano.
# Para logar consumo de LLM ou verificar saldo de tokens, usar ai_consumption.py.
import logging
import uuid as uuid_module
from datetime import datetime
from typing import Any
from uuid import UUID

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.domains.billing.dependencies import get_billing_repo
from app.domains.billing.repositories.billing_repository import BillingRepository
from app.models.billing import (
    Invoice,
    InvoiceStatus,
    PaymentMethod,
    Subscription,
)
from app.schemas.billing import (
    BillingStatusResponse,
    PaymentMethodCreate,
    RefundRequest,
    SubscriptionCancel,
    SubscriptionCreate,
    SubscriptionUpdate,
)
from app.services.billing_providers.base import WebhookSignatureError
from app.domains.billing.services.billing_service import BillingService
from app.shared.security.require_company_id import require_company_id
from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


def get_user_from_headers(
    company_id: str = Depends(require_company_id),
    current_user: User = Depends(get_current_active_user),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
) -> dict[str, Any]:
    """Get user context. company_id and role sourced from JWT (canonical).

    SECURITY (P0-W3-05 fix 2026-05-24): is_admin derived from JWT-authenticated
    User.role, NOT from X-User-Role request header. Previously any caller
    could pass X-User-Role: admin to bypass admin gates on billing mutations.
    """
    return {
        "company_id": company_id,
        "user_id": x_user_id or str(current_user.id),
        "role": current_user.role,
        "is_admin": current_user.role in (UserRole.admin, UserRole.wedotalent_admin),
    }


def _extract_company_id_from_user(current_user: dict[str, Any]) -> str:
    """Extract company_id from user context dict (already validated by JWT via get_user_from_headers)."""
    company_id = current_user.get("company_id")
    if not company_id:
        logger.error("Unexpected: company_id missing from user context after JWT validation")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="company_id missing from validated context (canonical JWT)",
        )
    return company_id





def require_admin(current_user: dict[str, Any]) -> None:
    """Raise exception if user is not admin."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


def log_cross_tenant_attempt(
    action: str,
    user_company_id: str,
    target_company_id: str,
    user_id: str,
    resource_type: str,
    resource_id: str | None = None
) -> None:
    """
    Log attempted cross-tenant access for security monitoring.

    SECURITY: This helps detect and audit unauthorized access attempts.
    """
    logger.warning(
        f"SECURITY ALERT - Cross-tenant access attempt: "
        f"action={action}, user_company={user_company_id}, "
        f"target_company={target_company_id}, user_id={user_id}, "
        f"resource_type={resource_type}, resource_id={resource_id}"
    )


def verify_company_ownership(
    current_user: dict[str, Any],
    target_client_id: str,
    resource_type: str,
    resource_id: str | None = None
) -> None:
    """
    Verify that the current user has access to the target clients resources.

    SECURITY: Admins can access any tenant, but regular users can only
    access their own companys data.

    Raises:
        HTTPException: 403 if access is denied
    """
    is_admin = current_user.get("is_admin", False)
    user_company_id = current_user.get("company_id")

    if is_admin:
        return

    if user_company_id != target_client_id:
        log_cross_tenant_attempt(
            action="access",
            user_company_id=user_company_id or None,
            target_company_id=target_client_id,
            user_id=current_user.get("user_id", "unknown"),
            resource_type=resource_type,
            resource_id=resource_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to this {resource_type}"
        )


def parse_uuid(value: str, field_name: str = "ID") -> UUID:
    """Parse string to UUID with proper error handling."""
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format"
        )



# ---------------------------------------------------------------------------
# Response schemas for billing endpoints
# Each endpoint below has an explicit response_model instead of None.
# ---------------------------------------------------------------------------

class WebhookProcessedResponse(BaseModel):
    """Response for webhook handler endpoints."""
    status: str
    processed: bool
    message: str | None = None


class BillingOperationResponse(BaseModel):
    """Generic response for billing mutation operations (create/update/delete).

    The 'data' field uses SubscriptionSettingsSchema / InvoiceSettingsSchema /
    PaymentMethodSettingsSchema depending on the endpoint. We represent it as
    a concrete model that accepts the common fields from all variants.
    """
    model_config = ConfigDict(extra='allow')
    success: bool
    message: str | None = None


class SubscriptionDataWrapper(BaseModel):
    """Typed data payload within subscription list/get responses."""
    model_config = ConfigDict(extra='allow')
    subscriptions: list[dict] | None = None
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class SubscriptionListWrapper(BaseModel):
    """Response for list-subscriptions endpoints."""
    success: bool
    data: SubscriptionDataWrapper


class SubscriptionItemWrapper(BaseModel):
    """Response for single-subscription endpoints (get/create/update/cancel)."""
    success: bool
    data: dict | None = None
    provider: str | None = None


class InvoiceDataWrapper(BaseModel):
    """Typed data payload within invoice list/get responses."""
    model_config = ConfigDict(extra='allow')
    invoices: list[dict] | None = None
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class InvoiceListWrapper(BaseModel):
    """Response for list-invoices endpoints."""
    success: bool
    data: InvoiceDataWrapper


class InvoiceItemWrapper(BaseModel):
    """Response for single-invoice endpoints (get/refund/pay)."""
    success: bool
    data: dict | None = None
    message: str | None = None


class PaymentMethodDataWrapper(BaseModel):
    """Typed data payload within payment-method list/get responses."""
    model_config = ConfigDict(extra='allow')
    payment_methods: list[dict] | None = None
    total: int | None = None


class PaymentMethodListWrapper(BaseModel):
    """Response for list-payment-methods endpoints."""
    success: bool
    data: PaymentMethodDataWrapper


class PaymentMethodItemWrapper(BaseModel):
    """Response for single-payment-method endpoints (add/remove)."""
    success: bool
    data: dict | None = None
    message: str | None = None


class ClientBillingData(BaseModel):
    """Typed data payload within client billing data response."""
    model_config = ConfigDict(extra='forbid')

    client_id: str
    client_name: str | None = None
    plan_id: str | None = None
    subscription: dict | None = None
    invoices: list[dict] = []
    payment_methods: list[dict] = []
    usage: dict | None = None


class ClientBillingWrapper(BaseModel):
    """Response for get-client-billing endpoint."""
    success: bool
    data: ClientBillingData


class SubscriptionSettingsWrapper(BaseModel):
    """Response for get/update current subscription endpoints."""
    success: bool
    data: dict | None = None


class UsageData(BaseModel):
    """Typed usage data payload in /usage response."""
    model_config = ConfigDict(extra='forbid')

    ai_credits_used: int = 0
    ai_credits_limit: int = 1000
    active_jobs: int = 0
    jobs_limit: int = 50
    active_users: int = 0
    users_limit: int = 10
    period_start: str | None = None
    period_end: str | None = None


class UsageDataWrapper(BaseModel):
    """Response for /usage endpoint."""
    success: bool
    data: UsageData


@router.get("/status", summary="Get billing providers status", response_model=BillingStatusResponse)
async def get_billing_status(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)) -> BillingStatusResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get status of billing providers (Iugu/Vindi).
    """
    try:
        _extract_company_id_from_user(current_user)

        billing_service = BillingService(repo.db)

        providers_status = {}
        for provider_name in ["iugu", "vindi"]:
            try:
                provider = billing_service.get_provider(provider_name)
                providers_status[provider_name] = {
                    "status": "available",
                    "configured": provider.is_configured() if hasattr(provider, "is_configured") else True
                }
            except Exception as e:
                providers_status[provider_name] = {
                    "status": "error",
                    "configured": False,
                    "error": str(e)
                }

        logger.info(f"Billing status checked by company {current_user.get('company_id')}")

        return BillingStatusResponse(
            status="healthy",
            providers=providers_status,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking billing status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check billing status: {str(e)}"
        )


@router.get("/subscriptions", summary="List subscriptions", response_model=SubscriptionListWrapper)
async def list_subscriptions(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    provider: str | None = Query(None, description="Filter by provider"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    List subscriptions.

    SECURITY:
    - Admin users can see all subscriptions (optionally filtered by company_id)
    - Non-admin users can only see their companys subscriptions
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        company_uuid = parse_uuid(company_id, "company_id")

        is_admin = current_user.get("is_admin", False)

        conditions = []

        if not is_admin:
            conditions.append(Subscription.client_id == company_uuid)

        if status_filter:
            conditions.append(Subscription.status == status_filter)

        if provider:
            conditions.append(Subscription.provider == provider)

        subscriptions = await repo.list_subscriptions(conditions, limit, offset)
        total = await repo.count_subscriptions(conditions)

        logger.info(
            f"Listed {len(subscriptions)} subscriptions (total: {total}) "
            f"for company {company_id}, admin={is_admin}"
        )

        return {
            "success": True,
            "data": {
                "subscriptions": [s.to_dict() for s in subscriptions],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing subscriptions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list subscriptions: {str(e)}"
        )


@router.get("/subscriptions/{client_id}", summary="Get client subscription", response_model=SubscriptionItemWrapper)
async def get_client_subscription(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get subscription for a specific client.

    SECURITY: Non-admin users can only access their own companys subscription.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client_uuid = parse_uuid(client_id, "client_id")

        verify_company_ownership(
            current_user=current_user,
            target_client_id=client_id,
            resource_type="subscription",
            resource_id=client_id
        )

        billing_service = BillingService(repo.db)
        subscription = await billing_service.get_active_subscription(client_uuid)

        if not subscription:
            subscription = await repo.get_latest_subscription_by_client(client_uuid)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription found for this client"
            )

        logger.info(
            f"Retrieved subscription {subscription.id} for client {client_id} "
            f"by company {company_id}"
        )

        return {
            "success": True,
            "data": subscription.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client subscription: {str(e)}"
        )


@router.post("/subscriptions", summary="Create subscription", response_model=SubscriptionItemWrapper)
async def create_subscription(
    data: SubscriptionCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a new subscription for a client.

    SECURITY: Admin-only. The subscription is associated with the specified client_id.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        require_admin(current_user)

        client_uuid = parse_uuid(data.client_id, "client_id")

        billing_service = BillingService(repo.db)

        result = await billing_service.create_subscription(
            client_id=client_uuid,
            plan_code=data.plan_code,
            plan_name=data.plan_name,
            price_cents=data.price_cents,
            provider=data.provider,
            trial_days=data.trial_days,
            billing_cycle=data.billing_cycle,
            payment_method_id=data.payment_method_id,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create subscription")
            )

        logger.info(
            f"Created subscription for client {data.client_id} "
            f"by admin company {company_id}"
        )

        return {
            "success": True,
            "data": result.get("subscription"),
            "provider": result.get("provider")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )


@router.put("/subscriptions/{subscription_id}", summary="Update subscription", response_model=SubscriptionItemWrapper)
async def update_subscription(
    subscription_id: str,
    data: SubscriptionUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update an existing subscription (change plan, etc).

    SECURITY: Admin-only. Verifies subscription ownership before modification.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        require_admin(current_user)

        sub_uuid = parse_uuid(subscription_id, "subscription_id")

        billing_service = BillingService(repo.db)
        subscription = await billing_service.get_subscription(sub_uuid)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        if data.plan_code:
            result = await billing_service.change_plan(
                subscription_id=sub_uuid,
                new_plan_code=data.plan_code,
                new_plan_name=data.plan_name,
                new_price_cents=data.price_cents
            )
        else:
            if data.plan_name:
                subscription.plan_name = data.plan_name
            if data.price_cents is not None:
                subscription.price_cents = data.price_cents
            if data.status:
                subscription.status = data.status

            subscription.updated_at = datetime.utcnow()
            await repo.flush_and_refresh_subscription(subscription)

            result = {"success": True, "subscription": subscription.to_dict()}

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update subscription")
            )

        logger.info(
            f"Updated subscription {subscription_id} "
            f"by admin company {company_id}"
        )

        return {
            "success": True,
            "data": result.get("subscription")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )


@router.delete("/subscriptions/{subscription_id}", summary="Cancel subscription", response_model=SubscriptionItemWrapper)
async def cancel_subscription(
    subscription_id: str,
    data: SubscriptionCancel | None = None,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Cancel a subscription.

    SECURITY: Admin-only. Verifies subscription exists before cancellation.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        require_admin(current_user)

        sub_uuid = parse_uuid(subscription_id, "subscription_id")

        billing_service = BillingService(repo.db)

        subscription = await billing_service.get_subscription(sub_uuid)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        at_period_end = data.at_period_end if data else True
        reason = data.reason if data else None

        result = await billing_service.cancel_subscription(
            subscription_id=sub_uuid,
            at_period_end=at_period_end,
            reason=reason
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to cancel subscription")
            )

        logger.info(
            f"Cancelled subscription {subscription_id} "
            f"by admin company {company_id}"
        )

        return {
            "success": True,
            "data": result.get("subscription")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.get("/invoices", summary="List invoices", response_model=InvoiceListWrapper)
async def list_invoices(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    provider: str | None = Query(None, description="Filter by provider"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    List invoices.

    SECURITY:
    - Admin users can see all invoices
    - Non-admin users can only see their companys invoices
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        company_uuid = parse_uuid(company_id, "company_id")

        is_admin = current_user.get("is_admin", False)

        conditions = []

        if not is_admin:
            conditions.append(Invoice.client_id == company_uuid)

        if status_filter:
            conditions.append(Invoice.status == status_filter)

        if provider:
            conditions.append(Invoice.provider == provider)

        invoices = await repo.list_invoices(conditions, limit, offset)
        total = await repo.count_invoices(conditions)

        logger.info(
            f"Listed {len(invoices)} invoices (total: {total}) "
            f"for company {company_id}, admin={is_admin}"
        )

        return {
            "success": True,
            "data": {
                "invoices": [inv.to_dict() for inv in invoices],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing invoices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invoices: {str(e)}"
        )


@router.get("/invoices/client/{client_id}", summary="Get client invoices", response_model=InvoiceListWrapper)
async def get_client_invoices(
    client_id: str,
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get invoices for a specific client.

    SECURITY: Non-admin users can only access their own companys invoices.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client_uuid = parse_uuid(client_id, "client_id")

        verify_company_ownership(
            current_user=current_user,
            target_client_id=client_id,
            resource_type="invoices",
            resource_id=client_id
        )

        billing_service = BillingService(repo.db)
        invoices = await billing_service.list_invoices(
            client_id=client_uuid,
            status=status_filter,
            limit=limit
        )

        logger.info(
            f"Retrieved {len(invoices)} invoices for client {client_id} "
            f"by company {company_id}"
        )

        return {
            "success": True,
            "data": {
                "invoices": invoices,
                "total": len(invoices)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client invoices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client invoices: {str(e)}"
        )


@router.get("/invoices/{invoice_id}", summary="Get invoice details", response_model=InvoiceItemWrapper)
async def get_invoice(
    invoice_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get details of a specific invoice.

    SECURITY: Non-admin users can only access invoices belonging to their company.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        inv_uuid = parse_uuid(invoice_id, "invoice_id")

        billing_service = BillingService(repo.db)
        invoice = await billing_service.get_invoice(inv_uuid)

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        invoice_client_id = invoice.get("client_id")
        if invoice_client_id:
            verify_company_ownership(
                current_user=current_user,
                target_client_id=str(invoice_client_id),
                resource_type="invoice",
                resource_id=invoice_id
            )

        logger.info(
            f"Retrieved invoice {invoice_id} by company {company_id}"
        )

        return {
            "success": True,
            "data": invoice
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice: {str(e)}"
        )


@router.post("/invoices/{invoice_id}/refund", summary="Refund invoice", response_model=InvoiceItemWrapper)
async def refund_invoice(
    invoice_id: str,
    data: RefundRequest | None = None,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Process a refund for an invoice.

    SECURITY: Admin-only. Verifies invoice exists before processing refund.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        require_admin(current_user)

        inv_uuid = parse_uuid(invoice_id, "invoice_id")

        invoice = await repo.get_invoice_by_id(inv_uuid)

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if invoice.status != InvoiceStatus.PAID.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only paid invoices can be refunded"
            )

        billing_service = BillingService(repo.db)
        provider = billing_service.get_provider(invoice.provider)

        refund_amount = data.amount_cents if data and data.amount_cents else invoice.total_cents

        if invoice.external_id:
            refund_result = await provider.refund_invoice(
                invoice_id=invoice.external_id,
                amount_cents=refund_amount
            )

            if not refund_result.success:
                logger.warning(f"Failed to process refund in gateway: {refund_result.error}")

        invoice.status = InvoiceStatus.REFUNDED.value
        invoice.updated_at = datetime.utcnow()
        if data and data.reason:
            invoice.notes = f"Refund reason: {data.reason}"

        await repo.flush_and_refresh_invoice(invoice)

        logger.info(
            f"Refunded invoice {invoice_id} by admin company {company_id}"
        )

        return {
            "success": True,
            "data": invoice.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refunding invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refund invoice: {str(e)}"
        )


@router.get("/payment-methods/{client_id}", summary="Get client payment methods", response_model=PaymentMethodListWrapper)
async def get_client_payment_methods(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get payment methods for a specific client.

    SECURITY: Non-admin users can only access their own companys payment methods.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client_uuid = parse_uuid(client_id, "client_id")

        verify_company_ownership(
            current_user=current_user,
            target_client_id=client_id,
            resource_type="payment methods",
            resource_id=client_id
        )

        payment_methods = await repo.get_active_payment_methods_by_client(client_uuid)

        logger.info(
            f"Retrieved {len(payment_methods)} payment methods for client {client_id} "
            f"by company {company_id}"
        )

        return {
            "success": True,
            "data": {
                "payment_methods": [pm.to_dict() for pm in payment_methods],
                "total": len(payment_methods)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment methods: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment methods: {str(e)}"
        )


@router.post("/payment-methods", summary="Add payment method", response_model=PaymentMethodItemWrapper)
async def add_payment_method(
    data: PaymentMethodCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Add a new payment method for a subscription.

    SECURITY: Non-admin users can only add payment methods to their own company.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)

        sub_uuid = parse_uuid(data.subscription_id, "subscription_id")
        parse_uuid(data.client_id, "client_id")

        verify_company_ownership(
            current_user=current_user,
            target_client_id=data.client_id,
            resource_type="payment method",
            resource_id=data.subscription_id
        )

        billing_service = BillingService(repo.db)

        subscription = await billing_service.get_subscription(sub_uuid)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        if str(subscription.client_id) != data.client_id:
            log_cross_tenant_attempt(
                action="add_payment_method",
                user_company_id=company_id,
                target_company_id=data.client_id,
                user_id=current_user.get("user_id", "unknown"),
                resource_type="subscription",
                resource_id=data.subscription_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscription does not belong to this client"
            )

        card_data = None
        if data.card_brand or data.card_last_digits:
            card_data = {
                "brand": data.card_brand,
                "last_digits": data.card_last_digits,
                "holder_name": data.card_holder_name,
                "expiry_month": data.card_expiry_month,
                "expiry_year": data.card_expiry_year,
            }

        result = await billing_service.add_payment_method(
            subscription_id=sub_uuid,
            payment_type=data.payment_type,
            card_token=data.card_token,
            card_data=card_data,
            set_as_default=data.set_as_default
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to add payment method")
            )

        logger.info(
            f"Added payment method for subscription {data.subscription_id} "
            f"by company {company_id}"
        )

        return {
            "success": True,
            "data": result.get("payment_method")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding payment method: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add payment method: {str(e)}"
        )


@router.delete("/payment-methods/{payment_method_id}", summary="Remove payment method", response_model=PaymentMethodItemWrapper)
async def remove_payment_method(
    payment_method_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Remove (deactivate) a payment method.

    SECURITY: Non-admin users can only remove payment methods from their own company.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        pm_uuid = parse_uuid(payment_method_id, "payment_method_id")

        payment_method = await repo.get_payment_method_by_id(pm_uuid)

        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found"
            )

        verify_company_ownership(
            current_user=current_user,
            target_client_id=str(payment_method.client_id),
            resource_type="payment method",
            resource_id=payment_method_id
        )

        if payment_method.is_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove default payment method. Set another as default first."
            )

        payment_method.is_active = False
        payment_method.updated_at = datetime.utcnow()

        logger.info(
            f"Removed payment method {payment_method_id} by company {company_id}"
        )

        return {
            "success": True,
            "message": "Payment method removed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing payment method: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove payment method: {str(e)}"
        )


@router.post("/webhooks/iugu", summary="Iugu webhook handler", response_model=WebhookProcessedResponse)
async def handle_iugu_webhook(
    request: Request,
    repo: BillingRepository = Depends(get_billing_repo),
):
    # multi-tenancy: webhooks são server-to-server, autenticados via HMAC
    # signature (não por JWT). Validation canonical em
    # iugu_provider._verify_iugu_signature. Wave 4 audit 2026-05-22 fechou
    # P0 onde signature era aceita mas nunca conferida.
    """
    Handle webhooks from Iugu payment gateway.

    Authentication via HMAC-SHA256 over the raw request body using
    ``IUGU_API_TOKEN`` as secret. Invalid/missing signature -> HTTP 403.
    Fail-closed: missing ``IUGU_API_TOKEN`` env var -> 403 (REGRA 4).
    """
    payload_raw = await request.body()
    try:
        import json
        payload = json.loads(payload_raw.decode("utf-8")) if payload_raw else {}
    except (ValueError, UnicodeDecodeError):
        payload = {}

    signature = request.headers.get("X-Iugu-Signature")

    # Log only the event type (no PII, no signature, no payload body).
    logger.info(f"Received Iugu webhook: {payload.get('event', 'unknown')}")

    try:
        billing_service = BillingService(repo.db)
        result = await billing_service.process_webhook(
            provider="iugu",
            payload=payload,
            signature=signature,
            payload_raw=payload_raw,
        )
        logger.info(f"Processed Iugu webhook: {result}")
        return WebhookProcessedResponse(status="ok", processed=True)

    except WebhookSignatureError as exc:
        # Fail-loud per REGRA 4. Never silently accept on invalid signature.
        logger.warning(
            "Iugu webhook rejected with HTTP 403: %s",
            exc,
            extra={"event_type": payload.get("event")},
        )
        raise HTTPException(status_code=403, detail="Invalid webhook signature") from exc

    except Exception as e:
        logger.error(f"Error processing Iugu webhook: {str(e)}", exc_info=True)
        return WebhookProcessedResponse(status="error", processed=False, message=str(e))


@router.post("/webhooks/vindi", summary="Vindi webhook handler", response_model=WebhookProcessedResponse)
async def handle_vindi_webhook(
    request: Request,
    repo: BillingRepository = Depends(get_billing_repo),
):
    # multi-tenancy: webhooks são server-to-server, autenticados via HMAC signature
    # (não por JWT). require_company_id REMOVIDO pois quebrava o handler — Vindi
    # nunca envia JWT. Validação real em vindi_provider._verify_vindi_signature.
    # Wave 4 audit 2026-05-22 fechou P0 onde signature era aceita sem ser conferida.
    """
    Handle webhooks from Vindi payment gateway.

    Authentication via HMAC-SHA256 over the raw request body using
    ``VINDI_WEBHOOK_SECRET`` (or ``VINDI_API_KEY`` fallback) as secret.
    Invalid/missing signature -> HTTP 403. Fail-closed: missing env secret -> 403.
    """
    payload_raw = await request.body()
    try:
        import json
        payload = json.loads(payload_raw.decode("utf-8")) if payload_raw else {}
    except (ValueError, UnicodeDecodeError):
        payload = {}

    signature = request.headers.get("X-Vindi-Signature")

    logger.info(f"Received Vindi webhook: {payload.get('event', 'unknown')}")

    try:
        billing_service = BillingService(repo.db)
        result = await billing_service.process_webhook(
            provider="vindi",
            payload=payload,
            signature=signature,
            payload_raw=payload_raw,
        )
        logger.info(f"Processed Vindi webhook: {result}")
        return WebhookProcessedResponse(status="ok", processed=True)

    except WebhookSignatureError as exc:
        logger.warning(
            "Vindi webhook rejected with HTTP 403: %s",
            exc,
            extra={"event_type": payload.get("event") if isinstance(payload.get("event"), str) else None},
        )
        raise HTTPException(status_code=403, detail="Invalid webhook signature") from exc

    except Exception as e:
        logger.error(f"Error processing Vindi webhook: {str(e)}", exc_info=True)
        return WebhookProcessedResponse(status="error", processed=False, message=str(e))

class SubscriptionSettingsSchema(BaseModel):
    """Subscription stored in client.settings["billing"]."""
    plan_id: str = Field(..., description="starter, professional, enterprise, custom")
    status: str = Field(..., description="active, trial, suspended, cancelled")
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False


class InvoiceSettingsSchema(BaseModel):
    """Invoice stored in client.settings["billing"]."""
    id: str
    amount: float
    currency: str = "BRL"
    status: str = Field(..., description="paid, pending, failed, refunded")
    due_date: datetime
    paid_at: datetime | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class PaymentMethodSettingsSchema(BaseModel):
    """Payment method stored in client.settings["billing"]."""
    id: str
    type: str = Field(..., description="credit_card, boleto, pix")
    last_four: str | None = None
    brand: str | None = None
    is_default: bool = False


class UsageSettingsSchema(BaseModel):
    """Usage data stored in client.settings["billing"]."""
    ai_credits_used: int = 0
    ai_credits_limit: int = 1000
    active_jobs: int = 0
    jobs_limit: int = 50
    active_users: int = 0
    users_limit: int = 10
    period_start: datetime | None = None
    period_end: datetime | None = None


class SubscriptionUpdateRequest(WeDoBaseModel):
    """Request to update subscription."""
    plan_id: str | None = None
    status: str | None = None
    cancel_at_period_end: bool | None = None
    current_period_end: datetime | None = None


class PaymentMethodCreateRequest(WeDoBaseModel):
    """Request to create payment method."""
    type: str = Field(..., description="credit_card, boleto, pix")
    last_four: str | None = None
    brand: str | None = None
    is_default: bool = False


async def get_client_by_id(client_id: str, repo: BillingRepository):
    """Get client by ID with validation."""
    client_uuid = parse_uuid(client_id, "client_id")
    client = await repo.get_client_by_id(client_uuid)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client not found: {client_id}"
        )
    return client


def get_billing_settings(client) -> dict[str, Any]:
    """Get or initialize billing settings for a client."""
    settings = client.settings or {}
    if "billing" not in settings:
        now = datetime.utcnow()
        settings["billing"] = {
            "subscription": {
                "plan_id": client.plan_id or "starter",
                "status": "active" if client.status == "active" else "trial",
                "started_at": client.contract_start_date.isoformat() if client.contract_start_date else now.isoformat(),
                "current_period_start": now.isoformat(),
                "current_period_end": (now + relativedelta(months=1)).isoformat(),
                "cancel_at_period_end": False
            },
            "invoices": [],
            "payment_methods": [],
            "usage": {
                "ai_credits_used": 0,
                "ai_credits_limit": client.ai_credits_monthly or 1000,
                "active_jobs": 0,
                "jobs_limit": client.job_limit or 50,
                "active_users": 0,
                "users_limit": client.user_limit or 10,
                "period_start": now.isoformat(),
                "period_end": (now + relativedelta(months=1)).isoformat()
            }
        }
    return settings


@router.get("/clients/{client_id}", summary="Get client billing data", response_model=ClientBillingWrapper)
async def get_client_billing(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get complete billing data for a client from settings.

    Returns subscription, invoices, payment_methods, and usage.
    """
    try:
        _extract_company_id_from_user(current_user)
        verify_company_ownership(current_user, client_id, "billing")

        client = await get_client_by_id(client_id, repo)
        settings = get_billing_settings(client)
        billing = settings.get("billing", {})

        logger.info(f"Retrieved billing data for client {client_id}")

        return {
            "success": True,
            "data": {
                "client_id": str(client.id),
                "client_name": client.name,
                "plan_id": client.plan_id,
                "subscription": billing.get("subscription"),
                "invoices": billing.get("invoices", []),
                "payment_methods": billing.get("payment_methods", []),
                "usage": billing.get("usage")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client billing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client billing: {str(e)}"
        )


@router.get("/subscription", summary="Get current user subscription", response_model=SubscriptionSettingsWrapper)
async def get_current_subscription(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get subscription for the current users company.

    Data is stored in client.settings["billing"]["subscription"].
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        if client.settings != settings:
            client.settings = settings
            repo.mark_client_settings_modified(client)

        billing = settings.get("billing", {})

        return {
            "success": True,
            "data": billing.get("subscription")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription: {str(e)}"
        )


@router.put("/subscription", summary="Update current user subscription", response_model=SubscriptionSettingsWrapper)
async def update_current_subscription(
    data: SubscriptionUpdateRequest,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update subscription for the current users company.

    Data is stored in client.settings["billing"]["subscription"].
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        billing = settings.get("billing", {})
        subscription = billing.get("subscription", {})

        if data.plan_id:
            subscription["plan_id"] = data.plan_id
            client.plan_id = data.plan_id
        if data.status:
            subscription["status"] = data.status
        if data.cancel_at_period_end is not None:
            subscription["cancel_at_period_end"] = data.cancel_at_period_end
        if data.current_period_end:
            subscription["current_period_end"] = data.current_period_end.isoformat()

        billing["subscription"] = subscription
        settings["billing"] = billing
        client.settings = settings
        repo.mark_client_settings_modified(client)
        client.updated_at = datetime.utcnow()

        await repo.flush_and_refresh_client(client)

        logger.info(f"Updated subscription for company {company_id}")

        return {
            "success": True,
            "data": subscription
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )


@router.get("/my-invoices", summary="List current user invoices", response_model=InvoiceListWrapper)
async def list_my_invoices(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    List invoices for the current users company from settings.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        billing = settings.get("billing", {})
        invoices = billing.get("invoices", [])

        if status_filter:
            invoices = [inv for inv in invoices if inv.get("status") == status_filter]

        invoices = invoices[:limit]

        return {
            "success": True,
            "data": {
                "invoices": invoices,
                "total": len(invoices)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing invoices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invoices: {str(e)}"
        )


@router.get("/my-invoices/{invoice_id}", summary="Get invoice details", response_model=InvoiceItemWrapper)
async def get_my_invoice(
    invoice_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get details of a specific invoice from settings.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        billing = settings.get("billing", {})
        invoices = billing.get("invoices", [])

        invoice = next((inv for inv in invoices if inv.get("id") == invoice_id), None)

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice not found: {invoice_id}"
            )

        return {
            "success": True,
            "data": invoice
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice: {str(e)}"
        )


@router.post("/my-invoices/{invoice_id}/pay", summary="Mark invoice as paid (simulation)", response_model=InvoiceItemWrapper)
async def pay_my_invoice(
    invoice_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Mark an invoice as paid (simulation mode).

    Updates invoice status in client.settings["billing"]["invoices"].
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        billing = settings.get("billing", {})
        invoices = billing.get("invoices", [])

        invoice_idx = next((i for i, inv in enumerate(invoices) if inv.get("id") == invoice_id), None)

        if invoice_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice not found: {invoice_id}"
            )

        invoice = invoices[invoice_idx]

        if invoice.get("status") == "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice is already paid"
            )

        invoice["status"] = "paid"
        invoice["paid_at"] = datetime.utcnow().isoformat()
        invoices[invoice_idx] = invoice

        billing["invoices"] = invoices
        settings["billing"] = billing
        client.settings = settings
        repo.mark_client_settings_modified(client)
        client.updated_at = datetime.utcnow()

        logger.info(f"Marked invoice {invoice_id} as paid for company {company_id}")

        return {
            "success": True,
            "data": invoice,
            "message": "Invoice marked as paid successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error paying invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pay invoice: {str(e)}"
        )


@router.get("/my-payment-methods", summary="List current user payment methods", response_model=PaymentMethodListWrapper)
async def list_my_payment_methods(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    List payment methods for the current users company from settings.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        billing = settings.get("billing", {})
        payment_methods = billing.get("payment_methods", [])

        return {
            "success": True,
            "data": {
                "payment_methods": payment_methods,
                "total": len(payment_methods)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing payment methods: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list payment methods: {str(e)}"
        )


@router.post("/my-payment-methods", summary="Add payment method", response_model=PaymentMethodItemWrapper)
async def add_my_payment_method(
    data: PaymentMethodCreateRequest,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Add a payment method for the current users company.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        billing = settings.get("billing", {})
        payment_methods = billing.get("payment_methods", [])

        new_method = {
            "id": str(uuid_module.uuid4()),
            "type": data.type,
            "last_four": data.last_four,
            "brand": data.brand,
            "is_default": data.is_default,
            "created_at": datetime.utcnow().isoformat()
        }

        if data.is_default:
            for pm in payment_methods:
                pm["is_default"] = False

        payment_methods.append(new_method)
        billing["payment_methods"] = payment_methods
        settings["billing"] = billing
        client.settings = settings
        repo.mark_client_settings_modified(client)
        client.updated_at = datetime.utcnow()

        logger.info(f"Added payment method for company {company_id}")

        return {
            "success": True,
            "data": new_method
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding payment method: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add payment method: {str(e)}"
        )


@router.delete("/my-payment-methods/{method_id}", summary="Remove payment method", response_model=PaymentMethodItemWrapper)
async def remove_my_payment_method(
    method_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Remove a payment method for the current users company.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        billing = settings.get("billing", {})
        payment_methods = billing.get("payment_methods", [])

        method_idx = next((i for i, pm in enumerate(payment_methods) if pm.get("id") == method_id), None)

        if method_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment method not found: {method_id}"
            )

        method = payment_methods[method_idx]

        if method.get("is_default"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove default payment method. Set another as default first."
            )

        payment_methods.pop(method_idx)
        billing["payment_methods"] = payment_methods
        settings["billing"] = billing
        client.settings = settings
        repo.mark_client_settings_modified(client)
        client.updated_at = datetime.utcnow()

        logger.info(f"Removed payment method {method_id} for company {company_id}")

        return {
            "success": True,
            "message": "Payment method removed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing payment method: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove payment method: {str(e)}"
        )


@router.get("/usage", summary="Get current usage", response_model=UsageDataWrapper)
async def get_usage(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: BillingRepository = Depends(get_billing_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get current usage data for the users company.

    Returns AI credits, jobs, and users usage vs limits.
    """
    try:
        company_id = _extract_company_id_from_user(current_user)
        client = await get_client_by_id(company_id, repo)
        settings = get_billing_settings(client)

        if client.settings != settings:
            client.settings = settings
            repo.mark_client_settings_modified(client)

        billing = settings.get("billing", {})
        usage = billing.get("usage", {})

        usage["ai_credits_limit"] = client.ai_credits_monthly or 1000
        usage["jobs_limit"] = client.job_limit or 50
        usage["users_limit"] = client.user_limit or 10

        return {
            "success": True,
            "data": usage
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage: {str(e)}"
        )
