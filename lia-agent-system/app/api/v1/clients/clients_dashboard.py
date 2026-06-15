"""
Dashboard and platform statistics endpoints.
"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ._shared import (
    ClientAccountRepository,
    ClientStatus,
    get_client_repo,
    get_user_from_headers,
    logger,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter()

PLAN_PRICES = {
    "starter": 299.0,
    "professional": 599.0,
    "enterprise": 1499.0,
    "custom": 2999.0,
}


@router.get("/dashboard-summary", summary="Dashboard summary with KPIs and client lists", response_model=None)
async def get_dashboard_summary(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get unified dashboard summary with KPIs and client lists. Admin only."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin users can access dashboard summary")

        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        total_clients = await repo.count_total()
        active_clients = await repo.count_by_status(ClientStatus.ACTIVE.value)
        trial_clients_count = await repo.count_by_status(ClientStatus.TRIAL.value)
        churned_clients_count = await repo.count_by_status(ClientStatus.CHURNED.value)

        new_clients_list = await repo.list_created_between(start_date, end_date)
        new_clients_period = len(new_clients_list)

        active_clients_list = await repo.list_by_status(ClientStatus.ACTIVE.value)
        mrr = sum(PLAN_PRICES.get((c.plan_id or "starter").lower(), 299.0) for c in active_clients_list)
        arr = mrr * 12

        denominator = active_clients + churned_clients_count
        churn_rate = (churned_clients_count / denominator * 100) if denominator > 0 else 0.0

        trial_clients_list = await repo.list_by_status(ClientStatus.TRIAL.value)
        churned_clients_list = await repo.list_churned_between(start_date, end_date)

        def _new_client_dict(client):
            return {"id": str(client.id), "name": client.name, "plan": client.plan_id,
                    "created_at": client.created_at.isoformat() if client.created_at else None}

        def _trial_client_dict(client):
            trial_end_date = None
            days_remaining = 0
            if client.contract_end_date:
                trial_end_date = client.contract_end_date.isoformat()
                days_remaining = max(0, (client.contract_end_date - datetime.utcnow()).days)
            elif client.created_at:
                trial_end = client.created_at + timedelta(days=14)
                trial_end_date = trial_end.isoformat()
                days_remaining = max(0, (trial_end - datetime.utcnow()).days)
            return {"id": str(client.id), "name": client.name, "plan": client.plan_id,
                    "trial_end_date": trial_end_date, "days_remaining": days_remaining}

        def _churned_client_dict(client):
            settings = client.settings or {}
            return {"id": str(client.id), "name": client.name, "plan": client.plan_id,
                    "churned_at": client.updated_at.isoformat() if client.updated_at else None,
                    "reason": settings.get("churn_reason", "Não informado")}

        logger.info(f"Dashboard summary: {total_clients} total, {active_clients} active, {trial_clients_count} trial, {churned_clients_count} churned")

        return {
            "success": True,
            "data": {
                "kpis": {
                    "total_clients": total_clients, "active_clients": active_clients,
                    "trial_clients": trial_clients_count, "churned_clients": churned_clients_count,
                    "new_clients_period": new_clients_period,
                    "mrr": round(mrr, 2), "arr": round(arr, 2), "churn_rate": round(churn_rate, 2),
                },
                "new_clients": [_new_client_dict(c) for c in new_clients_list],
                "trial_clients": [_trial_client_dict(c) for c in trial_clients_list],
                "churned_clients": [_churned_client_dict(c) for c in churned_clients_list],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/overview", summary="Platform statistics overview", response_model=None)
async def get_platform_stats(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (platform_) — role-based access required
    """Get platform-wide statistics for all clients. Admin only."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin users can access platform statistics")
        total_clients = await repo.count_total()
        status_stats = await repo.get_status_distribution()
        plan_stats = await repo.get_plan_distribution()
        size_stats = await repo.get_company_size_distribution()
        return {
            "success": True,
            "data": {
                "total_clients": total_clients,
                "by_status": status_stats, "by_plan": plan_stats, "by_size": size_stats,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting platform stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
