"""
SaaS Metrics API Endpoints.

Provides endpoints for platform-wide and client-specific SaaS metrics:
- MRR, ARR, churn rate, growth rate
- Active clients and users
- AI consumption overview
- Client health scores
- Usage metrics (AI credits, users, jobs, storage)
- Payment history
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.ai_consumption import AiConsumption, AiCreditsBalance
from app.models.client_account import ClientAccount, ClientStatus
from app.models.client_user import ClientUser, ClientUserStatus
from app.models.saas_metrics import (
    ChurnRisk,
    ClientHealthMetrics,
    ClientSaasMetrics,
    ClientUsageMetrics,
    PaymentHistory,
    PaymentStatus,
)
from app.schemas.saas_metrics import (
    ChurnAnalysis,
    ClientAllMetricsResponse,
    ClientHealthMetricsResponse,
    ClientMetrics,
    ClientMetricsList,
    ClientSaasMetricsResponse,
    ClientUsageMetricsResponse,
    PaymentHistoryCreate,
    PaymentHistoryListResponse,
    PaymentHistoryResponse,
    PlatformAggregateMetrics,
    PlatformMetricsSummary,
    RevenueAnalysis,
    RevenueBreakdown,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/saas-metrics", tags=["saas-metrics"])

PLAN_PRICES = {
    "starter": 990.00,
    "professional": 2990.00,
    "enterprise": 9990.00,
    "custom": 0.00,
}


def get_user_from_headers(
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role")
) -> dict[str, Any]:
    """Get user context from request headers."""
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Company-ID header required"
        )
    
    try:
        UUID(x_company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Company-ID format"
        )
    
    return {
        "company_id": x_company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }


def require_admin(current_user: dict[str, Any]) -> None:
    """Raise exception if user is not admin."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for SaaS metrics"
        )


def verify_company_ownership(
    current_user: dict[str, Any],
    target_client_id: str,
    resource_type: str = "metrics"
) -> None:
    """
    Verify that the current user has access to the target client's resources.
    
    SECURITY: Admins can access any tenant, regular users only their company.
    """
    is_admin = current_user.get("is_admin", False)
    user_company_id = current_user.get("company_id")
    
    if is_admin:
        return
    
    if user_company_id != target_client_id:
        logger.warning(
            f"SECURITY ALERT - Cross-tenant access attempt: "
            f"user_company={user_company_id}, target_company={target_client_id}"
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


def _build_usage_response(usage: ClientUsageMetrics) -> ClientUsageMetricsResponse:
    """Build usage response with computed percentages."""
    data = usage.to_dict()
    data["aiCreditsUsagePercent"] = usage.ai_credits_usage_percent
    data["storageUsagePercent"] = usage.storage_usage_percent
    return ClientUsageMetricsResponse(**data)


@router.get("/aggregate", response_model=PlatformAggregateMetrics, summary="Get platform-wide aggregated metrics")
async def get_aggregate_metrics(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> PlatformAggregateMetrics:
    """
    Get platform-wide aggregated SaaS metrics.
    
    SECURITY: Only admins can access platform-wide metrics.
    """
    try:
        require_admin(current_user)
        
        total_mrr = 0.0
        total_arr = 0.0
        total_clients = 0
        active_clients = 0
        churned_clients = 0
        avg_health_score = 0.0
        low_risk = 0
        medium_risk = 0
        high_risk = 0
        pending_payments = 0
        failed_payments = 0
        total_revenue_30_days = 0.0
        ltv_sum = 0.0
        ltv_count = 0
        cac_sum = 0.0
        cac_count = 0
        
        clients_query = select(ClientAccount).where(ClientAccount.is_deleted == False)
        result = await db.execute(clients_query)
        clients = result.scalars().all()
        total_clients = len(clients)
        
        for client in clients:
            if client.status == ClientStatus.ACTIVE.value:
                active_clients += 1
            elif client.status == ClientStatus.CHURNED.value:
                churned_clients += 1
        
        saas_query = select(ClientSaasMetrics)
        result = await db.execute(saas_query)
        saas_metrics = result.scalars().all()
        
        for metrics in saas_metrics:
            total_mrr += float(metrics.mrr) if metrics.mrr else 0
            total_arr += float(metrics.arr) if metrics.arr else 0
            if metrics.ltv:
                ltv_sum += float(metrics.ltv)
                ltv_count += 1
            if metrics.cac:
                cac_sum += float(metrics.cac)
                cac_count += 1
        
        health_query = select(ClientHealthMetrics)
        result = await db.execute(health_query)
        health_metrics = result.scalars().all()
        
        health_sum = 0
        for metrics in health_metrics:
            health_sum += metrics.health_score if metrics.health_score else 0
            if metrics.churn_risk == ChurnRisk.LOW.value:
                low_risk += 1
            elif metrics.churn_risk == ChurnRisk.MEDIUM.value:
                medium_risk += 1
            elif metrics.churn_risk == ChurnRisk.HIGH.value:
                high_risk += 1
        
        if health_metrics:
            avg_health_score = health_sum / len(health_metrics)
        
        thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
        payments_query = select(PaymentHistory).where(
            PaymentHistory.date >= thirty_days_ago
        )
        result = await db.execute(payments_query)
        recent_payments = result.scalars().all()
        
        for payment in recent_payments:
            if payment.status == PaymentStatus.PAID.value:
                total_revenue_30_days += float(payment.amount) if payment.amount else 0
            elif payment.status == PaymentStatus.PENDING.value:
                pending_payments += 1
            elif payment.status == PaymentStatus.FAILED.value:
                failed_payments += 1
        
        churn_rate = 0.0
        if total_clients > 0:
            churn_rate = (churned_clients / total_clients) * 100
        
        avg_mrr = total_mrr / active_clients if active_clients > 0 else 0
        avg_ltv = ltv_sum / ltv_count if ltv_count > 0 else None
        avg_cac = cac_sum / cac_count if cac_count > 0 else None
        
        avg_risk = "low"
        if high_risk > medium_risk and high_risk > low_risk:
            avg_risk = "high"
        elif medium_risk > low_risk:
            avg_risk = "medium"
        
        logger.info(f"Aggregate metrics calculated by admin {current_user.get('user_id')}")
        
        return PlatformAggregateMetrics(
            total_mrr=total_mrr,
            total_arr=total_arr,
            total_clients=total_clients,
            active_clients=active_clients,
            churned_clients=churned_clients,
            avg_mrr=avg_mrr,
            avg_ltv=avg_ltv,
            avg_cac=avg_cac,
            avg_health_score=avg_health_score,
            avg_churn_risk=avg_risk,
            churn_rate=churn_rate,
            low_risk_count=low_risk,
            medium_risk_count=medium_risk,
            high_risk_count=high_risk,
            total_revenue_last_30_days=total_revenue_30_days,
            pending_payments=pending_payments,
            failed_payments=failed_payments,
            currency="BRL",
            calculated_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating aggregate metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate aggregate metrics: {str(e)}"
        )


@router.get("/summary", response_model=PlatformMetricsSummary, summary="Get platform metrics summary")
async def get_platform_summary(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get platform-wide SaaS metrics summary.
    
    Admin only endpoint that returns:
    - MRR, ARR
    - Total/active/trial/churned clients
    - Total/active users
    - Churn and growth rates
    - AI usage overview
    """
    try:
        require_admin(current_user)
        
        total_query = select(func.count(ClientAccount.id)).where(
            ClientAccount.is_deleted == False
        )
        total_result = await db.execute(total_query)
        total_clients = total_result.scalar() or 0
        
        active_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.status == ClientStatus.ACTIVE.value
            )
        )
        active_result = await db.execute(active_query)
        active_clients = active_result.scalar() or 0
        
        trial_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.status == ClientStatus.TRIAL.value
            )
        )
        trial_result = await db.execute(trial_query)
        trial_clients = trial_result.scalar() or 0
        
        churned_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.status == ClientStatus.CHURNED.value
            )
        )
        churned_result = await db.execute(churned_query)
        churned_clients = churned_result.scalar() or 0
        
        total_users_query = select(func.count(ClientUser.id)).where(
            ClientUser.is_deleted == False
        )
        total_users_result = await db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users_query = select(func.count(ClientUser.id)).where(
            and_(
                ClientUser.is_deleted == False,
                ClientUser.status == ClientUserStatus.ACTIVE.value,
                or_(
                    ClientUser.last_login_at >= thirty_days_ago,
                    ClientUser.last_login_at.is_(None)
                )
            )
        )
        active_users_result = await db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0
        
        mrr = 0.0
        plan_query = select(
            ClientAccount.plan_id,
            func.count(ClientAccount.id).label('count')
        ).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.status == ClientStatus.ACTIVE.value,
                ClientAccount.plan_id.isnot(None)
            )
        ).group_by(ClientAccount.plan_id)
        plan_result = await db.execute(plan_query)
        
        for row in plan_result:
            plan_price = PLAN_PRICES.get(row.plan_id, 0)
            mrr += plan_price * row.count
        
        arr = mrr * 12
        
        churn_rate = 0.0
        if total_clients > 0:
            churn_rate = round((churned_clients / total_clients) * 100, 2)
        
        growth_rate = 0.0
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)
        old_clients_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.created_at <= sixty_days_ago
            )
        )
        old_clients_result = await db.execute(old_clients_query)
        old_clients = old_clients_result.scalar() or 0
        
        if old_clients > 0:
            new_clients = total_clients - old_clients
            growth_rate = round((new_clients / old_clients) * 100, 2)
        
        avg_revenue = mrr / active_clients if active_clients > 0 else 0
        
        ai_query = select(
            func.sum(AiConsumption.total_tokens).label('total_tokens'),
            func.sum(AiConsumption.cost_cents).label('total_cost')
        )
        ai_result = await db.execute(ai_query)
        ai_stats = ai_result.one()
        
        logger.info(f"Platform metrics requested by admin {current_user.get('user_id')}")
        
        return PlatformMetricsSummary(
            mrr=round(mrr, 2),
            arr=round(arr, 2),
            total_clients=total_clients,
            active_clients=active_clients,
            trial_clients=trial_clients,
            churned_clients=churned_clients,
            total_users=total_users,
            active_users=active_users,
            churn_rate=churn_rate,
            growth_rate=growth_rate,
            average_revenue_per_client=round(avg_revenue, 2),
            total_ai_tokens_used=int(ai_stats.total_tokens or 0),
            total_ai_cost_cents=int(ai_stats.total_cost or 0),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting platform metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform metrics: {str(e)}"
        )


@router.get("/{client_id}", response_model=ClientAllMetricsResponse, summary="Get all metrics for a client")
async def get_all_client_metrics(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> ClientAllMetricsResponse:
    """
    Get all metrics (revenue, usage, health) for a specific client.
    """
    try:
        verify_company_ownership(current_user, client_id)
        
        client_uuid = parse_uuid(client_id, "client_id")
        
        revenue_query = select(ClientSaasMetrics).where(
            ClientSaasMetrics.client_id == client_uuid
        )
        result = await db.execute(revenue_query)
        revenue = result.scalar_one_or_none()
        
        usage_query = select(ClientUsageMetrics).where(
            ClientUsageMetrics.client_id == client_uuid
        )
        result = await db.execute(usage_query)
        usage = result.scalar_one_or_none()
        
        health_query = select(ClientHealthMetrics).where(
            ClientHealthMetrics.client_id == client_uuid
        )
        result = await db.execute(health_query)
        health = result.scalar_one_or_none()
        
        payments_query = select(PaymentHistory).where(
            PaymentHistory.client_id == client_uuid
        ).order_by(PaymentHistory.date.desc()).limit(5)
        result = await db.execute(payments_query)
        recent_payments = result.scalars().all()
        
        logger.info(f"All metrics retrieved for client {client_id}")
        
        return ClientAllMetricsResponse(
            revenue=ClientSaasMetricsResponse(**revenue.to_dict()) if revenue else None,
            usage=_build_usage_response(usage) if usage else None,
            health=ClientHealthMetricsResponse(**health.to_dict()) if health else None,
            recent_payments=[
                PaymentHistoryResponse(**p.to_dict()) for p in recent_payments
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for client {client_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client metrics: {str(e)}"
        )


@router.get("/{client_id}/revenue", response_model=ClientSaasMetricsResponse, summary="Get revenue metrics for a client")
async def get_revenue_metrics(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> ClientSaasMetricsResponse:
    """
    Get revenue metrics (MRR, ARR, LTV, CAC) for a specific client.
    """
    try:
        verify_company_ownership(current_user, client_id)
        
        client_uuid = parse_uuid(client_id, "client_id")
        
        query = select(ClientSaasMetrics).where(
            ClientSaasMetrics.client_id == client_uuid
        )
        result = await db.execute(query)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Revenue metrics not found for client {client_id}"
            )
        
        logger.info(f"Revenue metrics retrieved for client {client_id}")
        
        return ClientSaasMetricsResponse(**metrics.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revenue metrics for client {client_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get revenue metrics: {str(e)}"
        )


@router.get("/{client_id}/usage", response_model=ClientUsageMetricsResponse, summary="Get usage metrics for a client")
async def get_usage_metrics(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> ClientUsageMetricsResponse:
    """
    Get usage metrics (AI credits, users, jobs, storage) for a specific client.
    """
    try:
        verify_company_ownership(current_user, client_id)
        
        client_uuid = parse_uuid(client_id, "client_id")
        
        query = select(ClientUsageMetrics).where(
            ClientUsageMetrics.client_id == client_uuid
        )
        result = await db.execute(query)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usage metrics not found for client {client_id}"
            )
        
        logger.info(f"Usage metrics retrieved for client {client_id}")
        
        return _build_usage_response(metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage metrics for client {client_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage metrics: {str(e)}"
        )


@router.get("/{client_id}/health", response_model=ClientHealthMetricsResponse, summary="Get health metrics for a client")
async def get_health_metrics(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> ClientHealthMetricsResponse:
    """
    Get health metrics (churn risk, health score, NPS, engagement) for a specific client.
    """
    try:
        verify_company_ownership(current_user, client_id)
        
        client_uuid = parse_uuid(client_id, "client_id")
        
        query = select(ClientHealthMetrics).where(
            ClientHealthMetrics.client_id == client_uuid
        )
        result = await db.execute(query)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health metrics not found for client {client_id}"
            )
        
        logger.info(f"Health metrics retrieved for client {client_id}")
        
        return ClientHealthMetricsResponse(**metrics.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health metrics for client {client_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health metrics: {str(e)}"
        )


@router.get("/{client_id}/payments", response_model=PaymentHistoryListResponse, summary="Get payment history for a client")
async def get_payment_history(
    client_id: str,
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> PaymentHistoryListResponse:
    """
    Get payment history for a specific client.
    """
    try:
        verify_company_ownership(current_user, client_id)
        
        client_uuid = parse_uuid(client_id, "client_id")
        
        conditions = [PaymentHistory.client_id == client_uuid]
        if status_filter:
            conditions.append(PaymentHistory.status == status_filter)
        
        query = select(PaymentHistory).where(
            and_(*conditions)
        ).order_by(PaymentHistory.date.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        payments = result.scalars().all()
        
        count_query = select(func.count(PaymentHistory.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        logger.info(f"Payment history retrieved for client {client_id}: {len(payments)} payments")
        
        return PaymentHistoryListResponse(
            payments=[PaymentHistoryResponse(**p.to_dict()) for p in payments],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment history for client {client_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment history: {str(e)}"
        )


@router.post("/{client_id}/payments", response_model=PaymentHistoryResponse, summary="Record a payment")
async def create_payment(
    client_id: str,
    payment_data: PaymentHistoryCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> PaymentHistoryResponse:
    """
    Record a new payment for a specific client.
    """
    try:
        verify_company_ownership(current_user, client_id)
        
        client_uuid = parse_uuid(client_id, "client_id")
        
        client_query = select(ClientAccount).where(
            and_(
                ClientAccount.id == client_uuid,
                ClientAccount.is_deleted == False
            )
        )
        result = await db.execute(client_query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client {client_id} not found"
            )
        
        payment = PaymentHistory(
            client_id=client_uuid,
            date=payment_data.payment_date,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status=payment_data.status,
            method=payment_data.method,
            invoice_id=payment_data.invoice_id,
            external_transaction_id=payment_data.external_transaction_id,
            description=payment_data.description,
            notes=payment_data.notes,
            paid_at=datetime.utcnow() if payment_data.status == PaymentStatus.PAID.value else None
        )
        
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        
        logger.info(
            f"Payment recorded for client {client_id}: "
            f"{payment_data.amount} {payment_data.currency} ({payment_data.status})"
        )
        
        return PaymentHistoryResponse(**payment.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment for client {client_id}: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.get("/client/{client_id}", response_model=ClientMetrics, summary="Get client-specific metrics")
async def get_client_metrics(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get metrics for a specific client.
    
    Admin can access any client. Non-admin can only access their own company.
    """
    try:
        is_admin = current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
        if not is_admin and client_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own company metrics."
            )
        
        try:
            client_uuid = UUID(client_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID format"
            )
        
        query = select(ClientAccount).where(
            and_(
                ClientAccount.id == client_uuid,
                ClientAccount.is_deleted == False
            )
        )
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client not found: {client_id}"
            )
        
        users_query = select(func.count(ClientUser.id)).where(
            and_(
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False
            )
        )
        users_result = await db.execute(users_query)
        total_users = users_result.scalar() or 0
        
        datetime.utcnow() - timedelta(days=30)
        active_users_query = select(func.count(ClientUser.id)).where(
            and_(
                ClientUser.company_id == client_uuid,
                ClientUser.is_deleted == False,
                ClientUser.status == ClientUserStatus.ACTIVE.value
            )
        )
        active_users_result = await db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0
        
        balance_query = select(AiCreditsBalance).where(
            AiCreditsBalance.company_id == client_uuid
        )
        balance_result = await db.execute(balance_query)
        balance = balance_result.scalar_one_or_none()
        
        ai_tokens_used = 0
        ai_tokens_limit = client.ai_credits_monthly or 0
        if balance:
            ai_tokens_used = balance.current_usage or 0
            ai_tokens_limit = balance.monthly_limit or ai_tokens_limit
        
        ai_usage_pct = 0.0
        if ai_tokens_limit > 0:
            ai_usage_pct = round((ai_tokens_used / ai_tokens_limit) * 100, 2)
        
        days_since_signup = 0
        if client.created_at:
            days_since_signup = (datetime.utcnow() - client.created_at).days
        
        mrr = PLAN_PRICES.get(client.plan_id, 0) if client.plan_id else 0
        
        health_score = 100.0
        if client.status == ClientStatus.CHURNED.value:
            health_score = 0
        elif client.status == ClientStatus.SUSPENDED.value:
            health_score = 20
        elif client.status == ClientStatus.TRIAL.value:
            health_score = 60
        else:
            if active_users == 0:
                health_score -= 30
            if ai_usage_pct < 10:
                health_score -= 20
            elif ai_usage_pct > 90:
                health_score -= 10
        
        logger.info(f"Client metrics for {client_id} requested by {current_user.get('user_id')}")
        
        return ClientMetrics(
            client_id=str(client.id),
            client_name=client.name,
            status=client.status,
            plan_id=client.plan_id,
            mrr=mrr,
            total_users=total_users,
            active_users=active_users,
            total_jobs=0,
            active_jobs=0,
            ai_tokens_used=ai_tokens_used,
            ai_tokens_limit=ai_tokens_limit,
            ai_usage_percentage=ai_usage_pct,
            days_since_signup=days_since_signup,
            contract_start=client.contract_start_date.isoformat() if client.contract_start_date else None,
            contract_end=client.contract_end_date.isoformat() if client.contract_end_date else None,
            health_score=max(0, min(100, health_score)),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client metrics: {str(e)}"
        )


@router.get("/clients", response_model=ClientMetricsList, summary="List all client metrics")
async def list_client_metrics(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    plan: str | None = Query(None, description="Filter by plan"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    List metrics for all clients.
    
    Admin only endpoint.
    """
    try:
        require_admin(current_user)
        
        conditions = [ClientAccount.is_deleted == False]
        
        if status_filter:
            conditions.append(ClientAccount.status == status_filter)
        
        if plan:
            conditions.append(ClientAccount.plan_id == plan)
        
        query = select(ClientAccount).where(and_(*conditions))
        query = query.order_by(ClientAccount.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        count_query = select(func.count(ClientAccount.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        client_metrics = []
        for client in clients:
            users_query = select(func.count(ClientUser.id)).where(
                and_(
                    ClientUser.company_id == client.id,
                    ClientUser.is_deleted == False
                )
            )
            users_result = await db.execute(users_query)
            total_users = users_result.scalar() or 0
            
            mrr = PLAN_PRICES.get(client.plan_id, 0) if client.plan_id else 0
            
            days_since_signup = 0
            if client.created_at:
                days_since_signup = (datetime.utcnow() - client.created_at).days
            
            client_metrics.append(ClientMetrics(
                client_id=str(client.id),
                client_name=client.name,
                status=client.status,
                plan_id=client.plan_id,
                mrr=mrr,
                total_users=total_users,
                active_users=0,
                total_jobs=0,
                active_jobs=0,
                ai_tokens_used=0,
                ai_tokens_limit=client.ai_credits_monthly or 0,
                ai_usage_percentage=0,
                days_since_signup=days_since_signup,
                contract_start=client.contract_start_date.isoformat() if client.contract_start_date else None,
                contract_end=client.contract_end_date.isoformat() if client.contract_end_date else None,
                health_score=100 if client.status == ClientStatus.ACTIVE.value else 50,
                timestamp=datetime.utcnow().isoformat()
            ))
        
        logger.info(f"Listed {len(client_metrics)} client metrics (admin: {current_user.get('user_id')})")
        
        return ClientMetricsList(
            clients=client_metrics,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing client metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list client metrics: {str(e)}"
        )


@router.get("/churn-analysis", response_model=ChurnAnalysis, summary="Get churn analysis")
async def get_churn_analysis(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get churn analysis data.
    
    Admin only endpoint.
    """
    try:
        require_admin(current_user)
        
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_churned_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.status == ClientStatus.CHURNED.value,
                ClientAccount.updated_at >= current_month_start
            )
        )
        current_churned_result = await db.execute(current_churned_query)
        current_churned = current_churned_result.scalar() or 0
        
        previous_churned_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.status == ClientStatus.CHURNED.value,
                ClientAccount.updated_at >= previous_month_start,
                ClientAccount.updated_at < current_month_start
            )
        )
        previous_churned_result = await db.execute(previous_churned_query)
        previous_churned = previous_churned_result.scalar() or 0
        
        total_query = select(func.count(ClientAccount.id)).where(
            ClientAccount.is_deleted == False
        )
        total_result = await db.execute(total_query)
        total_clients = total_result.scalar() or 1
        
        churn_rate = round((current_churned / total_clients) * 100, 2)
        
        at_risk_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.status == ClientStatus.SUSPENDED.value
            )
        )
        at_risk_result = await db.execute(at_risk_query)
        at_risk = at_risk_result.scalar() or 0
        
        logger.info(f"Churn analysis requested by admin {current_user.get('user_id')}")
        
        return ChurnAnalysis(
            current_month_churned=current_churned,
            previous_month_churned=previous_churned,
            churn_rate=churn_rate,
            at_risk_clients=at_risk,
            reasons={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting churn analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get churn analysis: {str(e)}"
        )


@router.get("/revenue", response_model=RevenueAnalysis, summary="Get revenue analysis")
async def get_revenue_analysis(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get revenue breakdown analysis.
    
    Admin only endpoint.
    """
    try:
        require_admin(current_user)
        
        plan_query = select(
            ClientAccount.plan_id,
            func.count(ClientAccount.id).label('count')
        ).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.status == ClientStatus.ACTIVE.value,
                ClientAccount.plan_id.isnot(None)
            )
        ).group_by(ClientAccount.plan_id)
        
        plan_result = await db.execute(plan_query)
        
        total_mrr = 0.0
        by_plan = []
        
        for row in plan_result:
            plan_price = PLAN_PRICES.get(row.plan_id, 0)
            plan_mrr = plan_price * row.count
            total_mrr += plan_mrr
            
            by_plan.append({
                "category": row.plan_id,
                "revenue": plan_mrr,
                "client_count": row.count
            })
        
        for item in by_plan:
            item["percentage"] = round((item["revenue"] / total_mrr) * 100, 2) if total_mrr > 0 else 0
        
        by_plan_models = [RevenueBreakdown(**item) for item in by_plan]
        
        size_query = select(
            ClientAccount.company_size,
            func.count(ClientAccount.id).label('count')
        ).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.status == ClientStatus.ACTIVE.value,
                ClientAccount.company_size.isnot(None)
            )
        ).group_by(ClientAccount.company_size)
        
        size_result = await db.execute(size_query)
        by_size = []
        
        for row in size_result:
            by_size.append(RevenueBreakdown(
                category=row.company_size or "unknown",
                revenue=0,
                percentage=0,
                client_count=row.count
            ))
        
        growth_rate = 0.0
        
        logger.info(f"Revenue analysis requested by admin {current_user.get('user_id')}")
        
        return RevenueAnalysis(
            total_mrr=round(total_mrr, 2),
            total_arr=round(total_mrr * 12, 2),
            by_plan=by_plan_models,
            by_company_size=by_size,
            growth_rate=growth_rate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revenue analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get revenue analysis: {str(e)}"
        )
