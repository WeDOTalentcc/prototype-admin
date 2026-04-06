"""
Clients API Endpoints.

Provides CRUD operations for client account management.
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.auth.workos_models import CompanyWorkOSConfig
from app.core.database import get_db
from app.domains.communication.services.email_service import EmailService
from app.domains.job_management.services.template_seeder import clone_templates_for_client
from app.models.client_account import CLIENT_STATUS_OPTIONS, COMPANY_SIZE_OPTIONS, ClientAccount, ClientStatus
from app.services.hubspot_service import hubspot_service, sync_client_to_hubspot
from app.services.workos_provisioning_service import provision_workos_organization

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["clients"])


def get_user_from_headers(
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role")
) -> dict[str, Any]:
    """
    Get user context from request headers.
    Used for development and internal API calls.
    """
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company ID required. Please provide X-Company-ID header."
        )
    
    return {
        "company_id": x_company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }


class AddressSchema(BaseModel):
    """Address schema."""
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = "Brasil"


class ClientCreate(BaseModel):
    """Request model for creating a client."""
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    trade_name: str | None = Field(None, max_length=255, description="Trade name")
    cnpj: str | None = Field(None, max_length=20, description="CNPJ")
    primary_email: str | None = Field(None, max_length=255)
    primary_phone: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=500)
    address: AddressSchema | None = None
    status: str = Field(default="pending_setup")
    plan_id: str | None = Field(None, max_length=100)
    contract_start_date: datetime | None = None
    contract_end_date: datetime | None = None
    user_limit: int = Field(default=10, ge=1)
    job_limit: int = Field(default=50, ge=1)
    ai_credits_monthly: int = Field(default=1000, ge=0)
    settings: dict[str, Any] | None = None
    features_enabled: list[str] | None = None
    account_manager_id: str | None = None
    implementation_manager_id: str | None = None
    logo_url: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    company_size: str | None = Field(None, max_length=50)


class ClientUpdate(BaseModel):
    """Request model for updating a client."""
    name: str | None = Field(None, min_length=1, max_length=255)
    trade_name: str | None = Field(None, max_length=255)
    cnpj: str | None = Field(None, max_length=20)
    primary_email: str | None = Field(None, max_length=255)
    primary_phone: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=500)
    address: AddressSchema | None = None
    plan_id: str | None = Field(None, max_length=100)
    contract_start_date: datetime | None = None
    contract_end_date: datetime | None = None
    user_limit: int | None = Field(None, ge=1)
    job_limit: int | None = Field(None, ge=1)
    ai_credits_monthly: int | None = Field(None, ge=0)
    settings: dict[str, Any] | None = None
    features_enabled: list[str] | None = None
    account_manager_id: str | None = None
    implementation_manager_id: str | None = None
    logo_url: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    company_size: str | None = Field(None, max_length=50)
    onboarding_completed_at: datetime | None = None


class StatusUpdate(BaseModel):
    """Request model for updating client status."""
    status: str = Field(..., description="New status")
    reason: str | None = Field(None, description="Reason for status change")


@router.get("/status-options", summary="List available status options")
async def list_status_options():
    """List all available client status options."""
    return {
        "success": True,
        "data": {
            "statuses": CLIENT_STATUS_OPTIONS,
            "company_sizes": COMPANY_SIZE_OPTIONS
        }
    }


PLAN_PRICES = {
    "starter": 299.0,
    "professional": 599.0,
    "enterprise": 1499.0,
    "custom": 2999.0,
}


@router.get("/dashboard-summary", summary="Dashboard summary with KPIs and client lists")
async def get_dashboard_summary(
    start_date: datetime | None = Query(None, description="Start date for period filter"),
    end_date: datetime | None = Query(None, description="End date for period filter"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get unified dashboard summary with KPIs and client lists.
    
    Returns:
    - KPIs: total clients, active, trial, churned, new in period, MRR, ARR, churn rate
    - Lists: new clients, trial clients, churned clients in period
    
    Only admin users can access this endpoint.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can access dashboard summary"
            )
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        total_query = select(func.count(ClientAccount.id)).where(ClientAccount.is_deleted == False)
        total_result = await db.execute(total_query)
        total_clients = total_result.scalar() or 0
        
        active_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.status == ClientStatus.ACTIVE.value,
                ClientAccount.is_deleted == False
            )
        )
        active_result = await db.execute(active_query)
        active_clients = active_result.scalar() or 0
        
        trial_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.status == ClientStatus.TRIAL.value,
                ClientAccount.is_deleted == False
            )
        )
        trial_result = await db.execute(trial_query)
        trial_clients_count = trial_result.scalar() or 0
        
        churned_query = select(func.count(ClientAccount.id)).where(
            and_(
                ClientAccount.status == ClientStatus.CHURNED.value,
                ClientAccount.is_deleted == False
            )
        )
        churned_result = await db.execute(churned_query)
        churned_clients_count = churned_result.scalar() or 0
        
        new_clients_query = select(ClientAccount).where(
            and_(
                ClientAccount.created_at >= start_date,
                ClientAccount.created_at <= end_date,
                ClientAccount.is_deleted == False
            )
        ).order_by(ClientAccount.created_at.desc())
        new_clients_result = await db.execute(new_clients_query)
        new_clients_list = new_clients_result.scalars().all()
        new_clients_period = len(new_clients_list)
        
        mrr = 0.0
        active_clients_query = select(ClientAccount).where(
            and_(
                ClientAccount.status == ClientStatus.ACTIVE.value,
                ClientAccount.is_deleted == False
            )
        )
        active_clients_result = await db.execute(active_clients_query)
        active_clients_list = active_clients_result.scalars().all()
        
        for client in active_clients_list:
            plan_id = client.plan_id or "starter"
            mrr += PLAN_PRICES.get(plan_id.lower(), 299.0)
        
        arr = mrr * 12
        
        denominator = active_clients + churned_clients_count
        churn_rate = (churned_clients_count / denominator * 100) if denominator > 0 else 0.0
        
        trial_clients_list_query = select(ClientAccount).where(
            and_(
                ClientAccount.status == ClientStatus.TRIAL.value,
                ClientAccount.is_deleted == False
            )
        ).order_by(ClientAccount.created_at.desc())
        trial_clients_result = await db.execute(trial_clients_list_query)
        trial_clients_list = trial_clients_result.scalars().all()
        
        churned_clients_query = select(ClientAccount).where(
            and_(
                ClientAccount.status == ClientStatus.CHURNED.value,
                ClientAccount.updated_at >= start_date,
                ClientAccount.updated_at <= end_date,
                ClientAccount.is_deleted == False
            )
        ).order_by(ClientAccount.updated_at.desc())
        churned_clients_result = await db.execute(churned_clients_query)
        churned_clients_list = churned_clients_result.scalars().all()
        
        new_clients_data = []
        for client in new_clients_list:
            new_clients_data.append({
                "id": str(client.id),
                "name": client.name,
                "plan": client.plan_id,
                "created_at": client.created_at.isoformat() if client.created_at else None
            })
        
        trial_clients_data = []
        for client in trial_clients_list:
            trial_end_date = None
            days_remaining = 0
            if client.contract_end_date:
                trial_end_date = client.contract_end_date.isoformat()
                remaining = (client.contract_end_date - datetime.utcnow()).days
                days_remaining = max(0, remaining)
            elif client.created_at:
                trial_end = client.created_at + timedelta(days=14)
                trial_end_date = trial_end.isoformat()
                remaining = (trial_end - datetime.utcnow()).days
                days_remaining = max(0, remaining)
            
            trial_clients_data.append({
                "id": str(client.id),
                "name": client.name,
                "plan": client.plan_id,
                "trial_end_date": trial_end_date,
                "days_remaining": days_remaining
            })
        
        churned_clients_data = []
        for client in churned_clients_list:
            settings = client.settings or {}
            reason = settings.get("churn_reason", "Não informado")
            
            churned_clients_data.append({
                "id": str(client.id),
                "name": client.name,
                "plan": client.plan_id,
                "churned_at": client.updated_at.isoformat() if client.updated_at else None,
                "reason": reason
            })
        
        logger.info(f"📊 Dashboard summary: {total_clients} total, {active_clients} active, {trial_clients_count} trial, {churned_clients_count} churned")
        
        return {
            "success": True,
            "data": {
                "kpis": {
                    "total_clients": total_clients,
                    "active_clients": active_clients,
                    "trial_clients": trial_clients_count,
                    "churned_clients": churned_clients_count,
                    "new_clients_period": new_clients_period,
                    "mrr": round(mrr, 2),
                    "arr": round(arr, 2),
                    "churn_rate": round(churn_rate, 2)
                },
                "new_clients": new_clients_data,
                "trial_clients": trial_clients_data,
                "churned_clients": churned_clients_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting dashboard summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard summary: {str(e)}"
        )


@router.get("/stats/overview", summary="Platform statistics overview")
async def get_platform_stats(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get platform-wide statistics for all clients.
    
    Only admin users can access this endpoint.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can access platform statistics"
            )
        
        total_query = select(func.count(ClientAccount.id)).where(ClientAccount.is_deleted == False)
        total_result = await db.execute(total_query)
        total_clients = total_result.scalar() or 0
        
        status_stats = {}
        for status_opt in ClientStatus:
            status_query = select(func.count(ClientAccount.id)).where(
                and_(
                    ClientAccount.status == status_opt.value,
                    ClientAccount.is_deleted == False
                )
            )
            status_result = await db.execute(status_query)
            status_stats[status_opt.value] = status_result.scalar() or 0
        
        plan_query = select(
            ClientAccount.plan_id,
            func.count(ClientAccount.id).label('count')
        ).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.plan_id.isnot(None)
            )
        ).group_by(ClientAccount.plan_id)
        plan_result = await db.execute(plan_query)
        plan_stats = {row.plan_id: row.count for row in plan_result}
        
        size_query = select(
            ClientAccount.company_size,
            func.count(ClientAccount.id).label('count')
        ).where(
            and_(
                ClientAccount.is_deleted == False,
                ClientAccount.company_size.isnot(None)
            )
        ).group_by(ClientAccount.company_size)
        size_result = await db.execute(size_query)
        size_stats = {row.company_size: row.count for row in size_result}
        
        return {
            "success": True,
            "data": {
                "total_clients": total_clients,
                "by_status": status_stats,
                "by_plan": plan_stats,
                "by_size": size_stats
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting platform stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform statistics: {str(e)}"
        )


@router.get("", summary="List clients")
async def list_clients(
    status: str | None = Query(None, description="Filter by status"),
    plan_id: str | None = Query(None, description="Filter by plan ID"),
    search: str | None = Query(None, description="Search by name, trade_name or CNPJ"),
    industry: str | None = Query(None, description="Filter by industry"),
    company_size: str | None = Query(None, description="Filter by company size"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    List all clients with optional filters.
    
    Admin users can see all clients, other users only see their own company.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        conditions = [ClientAccount.is_deleted == False]
        
        if status:
            conditions.append(ClientAccount.status == status)
        
        if plan_id:
            conditions.append(ClientAccount.plan_id == plan_id)
        
        if industry:
            conditions.append(ClientAccount.industry == industry)
        
        if company_size:
            conditions.append(ClientAccount.company_size == company_size)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    ClientAccount.name.ilike(search_term),
                    ClientAccount.trade_name.ilike(search_term),
                    ClientAccount.cnpj.ilike(search_term)
                )
            )
        
        if not is_admin:
            user_company_id = current_user.get("company_id")
            conditions.append(ClientAccount.id == user_company_id)
        
        query = select(ClientAccount).where(and_(*conditions))
        query = query.order_by(ClientAccount.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        count_query = select(func.count(ClientAccount.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        logger.info(f"📋 Listed {len(clients)} clients (total: {total})")
        
        return {
            "success": True,
            "data": {
                "clients": [c.to_dict() for c in clients],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing clients: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list clients: {str(e)}"
        )


@router.get("/{client_id}", summary="Get client by ID")
async def get_client(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific client by ID.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
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
        
        if not is_admin and str(client.id) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client"
            )
        
        return {
            "success": True,
            "data": client.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting client: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client: {str(e)}"
        )


@router.get("/{client_id}/stats", summary="Get client statistics")
async def get_client_stats(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for a specific client.
    
    Returns user count, job count, and usage metrics.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
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
        
        if not is_admin and str(client.id) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client"
            )
        
        stats = {
            "client_id": str(client.id),
            "name": client.name,
            "status": client.status,
            "limits": {
                "user_limit": client.user_limit,
                "job_limit": client.job_limit,
                "ai_credits_monthly": client.ai_credits_monthly,
            },
            "usage": {
                "users_count": 0,
                "active_jobs_count": 0,
                "total_jobs_count": 0,
                "candidates_count": 0,
                "ai_credits_used": 0,
            },
            "utilization": {
                "users_percentage": 0,
                "jobs_percentage": 0,
                "ai_credits_percentage": 0,
            }
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting client stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client statistics: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create client")
async def create_client(
    data: ClientCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new client.
    
    Only admin users can create new clients.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create clients"
            )
        
        valid_statuses = [s.value for s in ClientStatus]
        if data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        if data.cnpj:
            existing_query = select(ClientAccount).where(
                and_(
                    ClientAccount.cnpj == data.cnpj,
                    ClientAccount.is_deleted == False
                )
            )
            existing_result = await db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Client with CNPJ {data.cnpj} already exists"
                )
        
        client = ClientAccount(
            name=data.name,
            trade_name=data.trade_name,
            cnpj=data.cnpj,
            primary_email=data.primary_email,
            primary_phone=data.primary_phone,
            website=data.website,
            address=data.address.model_dump() if data.address else None,
            status=data.status,
            plan_id=data.plan_id,
            contract_start_date=data.contract_start_date,
            contract_end_date=data.contract_end_date,
            user_limit=data.user_limit,
            job_limit=data.job_limit,
            ai_credits_monthly=data.ai_credits_monthly,
            settings=data.settings or {},
            features_enabled=data.features_enabled or [],
            account_manager_id=data.account_manager_id,
            implementation_manager_id=data.implementation_manager_id,
            logo_url=data.logo_url,
            industry=data.industry,
            company_size=data.company_size,
        )
        
        db.add(client)
        await db.flush()
        
        await db.execute(
            text("""
                INSERT INTO company_workos_config (company_id, sso_enabled, scim_enabled)
                VALUES (:company_id, false, false)
                ON CONFLICT (company_id) DO NOTHING
            """),
            {"company_id": str(client.id)}
        )
        
        config_check = await db.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.company_id == str(client.id)
            )
        )
        if not config_check.scalar_one_or_none():
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to provision WorkOS config for client"
            )
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Created client: {client.name} (ID: {client.id}) with WorkOS config")
        
        organization_id = await provision_workos_organization(client, db)
        
        try:
            cloned_count = await clone_templates_for_client(db, str(client.id))
            logger.info(f"✅ Cloned {cloned_count} system templates for client {client.id}")
        except Exception as template_error:
            logger.warning(f"⚠️ Failed to clone templates for client {client.id}: {template_error}")
        
        email_sent = False
        if client.primary_email:
            try:
                import os
                base_url = os.getenv("FRONTEND_URL", "https://app.wedotalent.com")
                admin_portal_url = f"{base_url}/login"
                
                email_service = EmailService()
                email_sent = await email_service.send_welcome_email(
                    client=client,
                    admin_portal_url=admin_portal_url,
                    db=db
                )
                if email_sent:
                    logger.info(f"✅ Welcome email sent to {client.primary_email}")
                else:
                    logger.warning(f"⚠️ Failed to send welcome email to {client.primary_email}")
            except Exception as email_error:
                logger.warning(f"⚠️ Error sending welcome email: {email_error}")
        
        hubspot_result = None
        try:
            hubspot_result = await sync_client_to_hubspot(client, db)
            if hubspot_result.get("success"):
                logger.info(f"✅ Synced client {client.id} to HubSpot")
            else:
                logger.warning(f"⚠️ HubSpot sync skipped or failed: {hubspot_result.get('error')}")
        except Exception as hubspot_error:
            logger.warning(f"⚠️ Error syncing to HubSpot: {hubspot_error}")
        
        response_data = client.to_dict()
        response_data["organization_id"] = organization_id
        response_data["email_sent"] = email_sent
        response_data["hubspot_synced"] = hubspot_result.get("success") if hubspot_result else False
        
        return {
            "success": True,
            "message": "Client created successfully",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating client: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )


@router.put("/{client_id}", summary="Update client")
async def update_client(
    client_id: str,
    data: ClientUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing client.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
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
        
        if not is_admin and str(client.id) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update this client"
            )
        
        update_data = data.model_dump(exclude_unset=True)
        
        if 'address' in update_data and update_data['address']:
            update_data['address'] = update_data['address'].model_dump() if hasattr(update_data['address'], 'model_dump') else update_data['address']
        
        for field, value in update_data.items():
            setattr(client, field, value)
        
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Updated client: {client.name} (ID: {client.id})")
        
        return {
            "success": True,
            "message": "Client updated successfully",
            "data": client.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating client: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {str(e)}"
        )


@router.put("/{client_id}/status", summary="Update client status")
async def update_client_status(
    client_id: str,
    data: StatusUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update client status.
    
    Only admin users can update client status.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can update client status"
            )
        
        valid_statuses = [s.value for s in ClientStatus]
        if data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
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
        
        old_status = client.status
        client.status = data.status
        client.updated_at = datetime.utcnow()
        
        if data.status == ClientStatus.ACTIVE.value and old_status == ClientStatus.PENDING_SETUP.value:
            if not client.onboarding_completed_at:
                client.onboarding_completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Updated client status: {client.name} from {old_status} to {data.status}")
        
        return {
            "success": True,
            "message": f"Client status updated from {old_status} to {data.status}",
            "data": client.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating client status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client status: {str(e)}"
        )


@router.delete("/{client_id}", summary="Delete client (soft delete)")
async def delete_client(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a client.
    
    Only admin users can delete clients.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_id = current_user.get("user_id", "system")
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can delete clients"
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
        
        client.is_deleted = True
        client.deleted_at = datetime.utcnow()
        client.deleted_by = user_id
        client.status = ClientStatus.CHURNED.value
        
        await db.commit()
        
        logger.info(f"✅ Soft deleted client: {client.name} (ID: {client.id})")
        
        return {
            "success": True,
            "message": f"Client '{client.name}' has been deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting client: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client: {str(e)}"
        )


VALID_INTEGRATION_NAMES = ["gupy", "linkedin", "greenhouse", "slack", "whatsapp", "email"]
VALID_INTEGRATION_STATUSES = ["connected", "disconnected", "pending"]


class IntegrationCreate(BaseModel):
    """Request model for creating an integration."""
    name: str = Field(..., description="Integration name (gupy, linkedin, greenhouse, slack, whatsapp, email)")
    description: str | None = Field(None, description="Integration description")
    status: str = Field(default="pending", description="Integration status")
    config: dict[str, Any] | None = Field(None, description="Non-sensitive configuration")


class IntegrationUpdate(BaseModel):
    """Request model for updating an integration."""
    name: str | None = Field(None, description="Integration name")
    description: str | None = Field(None, description="Integration description")
    status: str | None = Field(None, description="Integration status")
    config: dict[str, Any] | None = Field(None, description="Non-sensitive configuration")


async def get_client_for_integrations(
    client_id: str,
    current_user: dict[str, Any],
    db: AsyncSession
) -> ClientAccount:
    """Helper to get client and validate access for integration endpoints."""
    is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
    user_company_id = current_user.get("company_id")
    
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
    
    if not is_admin and str(client.id) != user_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client"
        )
    
    return client


@router.get("/{client_id}/integrations", summary="List client integrations")
async def list_client_integrations(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    List all integrations for a specific client.
    
    Integrations are stored in client.settings["integrations"].
    """
    try:
        client = await get_client_for_integrations(client_id, current_user, db)
        
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        
        logger.info(f"📋 Listed {len(integrations)} integrations for client {client_id}")
        
        return {
            "success": True,
            "data": {
                "integrations": integrations,
                "total": len(integrations)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing integrations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list integrations: {str(e)}"
        )


@router.post("/{client_id}/integrations", status_code=status.HTTP_201_CREATED, summary="Add integration")
async def add_client_integration(
    client_id: str,
    data: IntegrationCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new integration for a client.
    """
    try:
        client = await get_client_for_integrations(client_id, current_user, db)
        
        if data.name.lower() not in VALID_INTEGRATION_NAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid integration name. Must be one of: {', '.join(VALID_INTEGRATION_NAMES)}"
            )
        
        if data.status not in VALID_INTEGRATION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(VALID_INTEGRATION_STATUSES)}"
            )
        
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        
        import uuid
        now = datetime.utcnow()
        
        new_integration = {
            "id": str(uuid.uuid4()),
            "name": data.name.lower(),
            "description": data.description or f"Integração com {data.name}",
            "status": data.status,
            "last_sync": None,
            "config": data.config or {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        integrations.append(new_integration)
        settings["integrations"] = integrations
        client.settings = settings
        client.updated_at = now
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Added integration '{data.name}' for client {client_id}")
        
        return {
            "success": True,
            "message": f"Integration '{data.name}' added successfully",
            "data": new_integration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error adding integration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add integration: {str(e)}"
        )


@router.put("/{client_id}/integrations/{integration_id}", summary="Update integration")
async def update_client_integration(
    client_id: str,
    integration_id: str,
    data: IntegrationUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing integration for a client.
    """
    try:
        client = await get_client_for_integrations(client_id, current_user, db)
        
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        
        integration_index = None
        for i, integ in enumerate(integrations):
            if integ.get("id") == integration_id:
                integration_index = i
                break
        
        if integration_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration not found: {integration_id}"
            )
        
        integration = integrations[integration_index]
        
        if data.name is not None:
            if data.name.lower() not in VALID_INTEGRATION_NAMES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid integration name. Must be one of: {', '.join(VALID_INTEGRATION_NAMES)}"
                )
            integration["name"] = data.name.lower()
        
        if data.description is not None:
            integration["description"] = data.description
        
        if data.status is not None:
            if data.status not in VALID_INTEGRATION_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(VALID_INTEGRATION_STATUSES)}"
                )
            integration["status"] = data.status
        
        if data.config is not None:
            integration["config"] = data.config
        
        integration["updated_at"] = datetime.utcnow().isoformat()
        
        integrations[integration_index] = integration
        settings["integrations"] = integrations
        client.settings = settings
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Updated integration '{integration_id}' for client {client_id}")
        
        return {
            "success": True,
            "message": "Integration updated successfully",
            "data": integration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating integration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update integration: {str(e)}"
        )


@router.delete("/{client_id}/integrations/{integration_id}", summary="Remove integration")
async def delete_client_integration(
    client_id: str,
    integration_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an integration from a client.
    """
    try:
        client = await get_client_for_integrations(client_id, current_user, db)
        
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        
        integration_index = None
        integration_name = None
        for i, integ in enumerate(integrations):
            if integ.get("id") == integration_id:
                integration_index = i
                integration_name = integ.get("name")
                break
        
        if integration_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration not found: {integration_id}"
            )
        
        integrations.pop(integration_index)
        settings["integrations"] = integrations
        client.settings = settings
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"✅ Removed integration '{integration_name}' from client {client_id}")
        
        return {
            "success": True,
            "message": f"Integration '{integration_name}' removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error removing integration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove integration: {str(e)}"
        )


@router.post("/{client_id}/integrations/{integration_id}/sync", summary="Sync integration")
async def sync_client_integration(
    client_id: str,
    integration_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger synchronization for a specific integration.
    
    This updates the last_sync timestamp and can trigger external sync logic.
    """
    try:
        client = await get_client_for_integrations(client_id, current_user, db)
        
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        
        integration_index = None
        for i, integ in enumerate(integrations):
            if integ.get("id") == integration_id:
                integration_index = i
                break
        
        if integration_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration not found: {integration_id}"
            )
        
        integration = integrations[integration_index]
        
        if integration.get("status") != "connected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot sync a disconnected integration. Please connect it first."
            )
        
        now = datetime.utcnow()
        integration["last_sync"] = now.isoformat()
        integration["updated_at"] = now.isoformat()
        
        integrations[integration_index] = integration
        settings["integrations"] = integrations
        client.settings = settings
        client.updated_at = now
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Synced integration '{integration.get('name')}' for client {client_id}")
        
        return {
            "success": True,
            "message": f"Integration '{integration.get('name')}' synchronized successfully",
            "data": integration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error syncing integration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync integration: {str(e)}"
        )


@router.post("/{client_id}/integrations/sync-all", summary="Sync all integrations")
async def sync_all_client_integrations(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger synchronization for all connected integrations.
    """
    try:
        client = await get_client_for_integrations(client_id, current_user, db)
        
        settings = client.settings or {}
        integrations = settings.get("integrations", [])
        
        now = datetime.utcnow()
        synced_count = 0
        
        for i, integ in enumerate(integrations):
            if integ.get("status") == "connected":
                integrations[i]["last_sync"] = now.isoformat()
                integrations[i]["updated_at"] = now.isoformat()
                synced_count += 1
        
        settings["integrations"] = integrations
        client.settings = settings
        client.updated_at = now
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Synced {synced_count} integrations for client {client_id}")
        
        return {
            "success": True,
            "message": f"Synchronized {synced_count} connected integration(s)",
            "data": {
                "synced_count": synced_count,
                "integrations": integrations
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error syncing all integrations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync integrations: {str(e)}"
        )


# ============================================================================
# CLIENT AUTOMATIONS ENDPOINTS
# ============================================================================

class AutomationCreate(BaseModel):
    """Request model for creating an automation."""
    name: str = Field(..., min_length=1, max_length=255, description="Automation name")
    description: str | None = Field(None, max_length=500)
    trigger: str = Field(..., description="Trigger type: screening_reminder, interview_completed, offer_sent, candidate_applied, etc")
    action: str = Field(..., description="Action type: send_email, send_whatsapp, send_notification, webhook")
    is_active: bool = Field(default=True)
    config: dict[str, Any] | None = Field(None, description="Additional config like template_id, delay_hours, etc")


class AutomationUpdate(BaseModel):
    """Request model for updating an automation."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    trigger: str | None = None
    action: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None


async def get_client_for_automations(
    client_id: str,
    current_user: dict[str, Any],
    db: AsyncSession
) -> ClientAccount:
    """Helper to get and validate client access for automations."""
    is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
    user_company_id = current_user.get("company_id")
    
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
    
    if not is_admin and str(client.id) != user_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client"
        )
    
    return client


@router.get("/{client_id}/automations", summary="List client automations")
async def list_client_automations(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    List all automations for a specific client.
    
    Automations are stored in client.settings["automations"].
    """
    try:
        client = await get_client_for_automations(client_id, current_user, db)
        
        settings = client.settings or {}
        automations = settings.get("automations", [])
        
        logger.info(f"📋 Listed {len(automations)} automations for client {client_id}")
        
        return {
            "success": True,
            "data": {
                "automations": automations,
                "total": len(automations)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing automations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list automations: {str(e)}"
        )


@router.post("/{client_id}/automations", status_code=status.HTTP_201_CREATED, summary="Create automation")
async def create_client_automation(
    client_id: str,
    data: AutomationCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new automation for a client.
    """
    try:
        client = await get_client_for_automations(client_id, current_user, db)
        
        settings = client.settings or {}
        automations = settings.get("automations", [])
        
        import uuid
        now = datetime.utcnow()
        
        new_automation = {
            "id": str(uuid.uuid4()),
            "name": data.name,
            "description": data.description or "",
            "trigger": data.trigger,
            "action": data.action,
            "is_active": data.is_active,
            "trigger_count": 0,
            "config": data.config or {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        automations.append(new_automation)
        settings["automations"] = automations
        client.settings = settings
        client.updated_at = now
        flag_modified(client, 'settings')
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Created automation '{data.name}' for client {client_id}")
        
        return {
            "success": True,
            "message": "Automation created successfully",
            "data": new_automation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create automation: {str(e)}"
        )


@router.put("/{client_id}/automations/{automation_id}", summary="Update automation")
async def update_client_automation(
    client_id: str,
    automation_id: str,
    data: AutomationUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing automation.
    """
    try:
        client = await get_client_for_automations(client_id, current_user, db)
        
        settings = client.settings or {}
        automations = settings.get("automations", [])
        
        automation_index = None
        automation = None
        for i, a in enumerate(automations):
            if a.get("id") == automation_id:
                automation_index = i
                automation = a
                break
        
        if automation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Automation not found: {automation_id}"
            )
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            automation[field] = value
        
        now = datetime.utcnow()
        automation["updated_at"] = now.isoformat()
        
        automations[automation_index] = automation
        settings["automations"] = automations
        client.settings = settings
        client.updated_at = now
        flag_modified(client, 'settings')
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Updated automation '{automation.get('name')}' for client {client_id}")
        
        return {
            "success": True,
            "message": "Automation updated successfully",
            "data": automation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update automation: {str(e)}"
        )


@router.delete("/{client_id}/automations/{automation_id}", summary="Delete automation")
async def delete_client_automation(
    client_id: str,
    automation_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an automation.
    """
    try:
        client = await get_client_for_automations(client_id, current_user, db)
        
        settings = client.settings or {}
        automations = settings.get("automations", [])
        
        original_count = len(automations)
        automations = [a for a in automations if a.get("id") != automation_id]
        
        if len(automations) == original_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Automation not found: {automation_id}"
            )
        
        now = datetime.utcnow()
        settings["automations"] = automations
        client.settings = settings
        client.updated_at = now
        flag_modified(client, 'settings')
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Deleted automation {automation_id} for client {client_id}")
        
        return {
            "success": True,
            "message": "Automation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete automation: {str(e)}"
        )


@router.patch("/{client_id}/automations/{automation_id}/toggle", summary="Toggle automation active state")
async def toggle_client_automation(
    client_id: str,
    automation_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle the is_active state of an automation.
    """
    try:
        client = await get_client_for_automations(client_id, current_user, db)
        
        settings = client.settings or {}
        automations = settings.get("automations", [])
        
        automation_index = None
        automation = None
        for i, a in enumerate(automations):
            if a.get("id") == automation_id:
                automation_index = i
                automation = a
                break
        
        if automation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Automation not found: {automation_id}"
            )
        
        automation["is_active"] = not automation.get("is_active", False)
        
        now = datetime.utcnow()
        automation["updated_at"] = now.isoformat()
        
        automations[automation_index] = automation
        settings["automations"] = automations
        client.settings = settings
        client.updated_at = now
        flag_modified(client, 'settings')
        
        await db.commit()
        await db.refresh(client)
        
        status_text = "activated" if automation["is_active"] else "deactivated"
        logger.info(f"✅ Automation '{automation.get('name')}' {status_text} for client {client_id}")
        
        return {
            "success": True,
            "message": f"Automation {status_text} successfully",
            "data": automation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error toggling automation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle automation: {str(e)}"
        )


DEFAULT_SETUP_SECTIONS = [
    {
        "id": "company-profile",
        "title": "Perfil da Empresa",
        "description": "Informações básicas, logo, missão e valores",
        "status": "pending",
        "progress": 0,
        "updated_at": None
    },
    {
        "id": "benefits",
        "title": "Benefícios",
        "description": "Pacote de benefícios oferecidos",
        "status": "pending",
        "progress": 0,
        "updated_at": None
    },
    {
        "id": "culture",
        "title": "Cultura & EVP",
        "description": "Proposta de valor ao empregado",
        "status": "pending",
        "progress": 0,
        "updated_at": None
    },
    {
        "id": "departments",
        "title": "Departamentos",
        "description": "Estrutura organizacional",
        "status": "pending",
        "progress": 0,
        "updated_at": None
    },
    {
        "id": "documents",
        "title": "Documentos",
        "description": "Templates e documentação padrão",
        "status": "pending",
        "progress": 0,
        "updated_at": None
    }
]


class SetupSectionUpdate(BaseModel):
    """Request model for updating a setup section."""
    status: str | None = Field(None, description="Section status: complete, partial, pending")
    progress: int | None = Field(None, ge=0, le=100, description="Progress percentage 0-100")


@router.get("/{client_id}/setup", summary="Get client setup status")
async def get_client_setup(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get setup status for a specific client.
    Returns all setup sections with their progress.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
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
        
        if not is_admin and str(client.id) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client"
            )
        
        settings = client.settings or {}
        setup_sections = settings.get("setup_sections")
        
        if not setup_sections:
            setup_sections = [s.copy() for s in DEFAULT_SETUP_SECTIONS]
        
        return {
            "success": True,
            "data": {
                "client_id": str(client.id),
                "sections": setup_sections
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting client setup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client setup: {str(e)}"
        )


@router.put("/{client_id}/setup/{section_id}", summary="Update setup section progress")
async def update_client_setup_section(
    client_id: str,
    section_id: str,
    data: SetupSectionUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update progress for a specific setup section.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
        valid_section_ids = ["company-profile", "benefits", "culture", "departments", "documents"]
        if section_id not in valid_section_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid section ID. Must be one of: {', '.join(valid_section_ids)}"
            )
        
        valid_statuses = ["complete", "partial", "pending"]
        if data.status and data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
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
        
        if not is_admin and str(client.id) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update this client"
            )
        
        settings = client.settings or {}
        setup_sections = settings.get("setup_sections")
        
        if not setup_sections:
            setup_sections = [s.copy() for s in DEFAULT_SETUP_SECTIONS]
        
        section_index = None
        section = None
        for i, s in enumerate(setup_sections):
            if s.get("id") == section_id:
                section_index = i
                section = s
                break
        
        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section not found: {section_id}"
            )
        
        now = datetime.utcnow()
        
        if data.status is not None:
            section["status"] = data.status
        if data.progress is not None:
            section["progress"] = data.progress
            if data.progress == 100:
                section["status"] = "complete"
            elif data.progress > 0:
                section["status"] = "partial"
            else:
                section["status"] = "pending"
        
        section["updated_at"] = now.isoformat()
        
        setup_sections[section_index] = section
        settings["setup_sections"] = setup_sections
        client.settings = settings
        client.updated_at = now
        flag_modified(client, 'settings')
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"✅ Updated setup section '{section_id}' for client {client_id}: progress={section['progress']}%, status={section['status']}")
        
        return {
            "success": True,
            "message": "Setup section updated successfully",
            "data": {
                "section": section,
                "all_sections": setup_sections
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating setup section: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setup section: {str(e)}"
        )


@router.get("/{client_id}/hubspot/status", summary="Get HubSpot sync status")
async def get_hubspot_sync_status(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get HubSpot sync status for a client.
    
    Returns:
    - synced: Whether the client is synced to HubSpot
    - last_synced_at: Timestamp of last sync
    - hubspot_company_id: HubSpot Company ID
    - hubspot_deal_id: HubSpot Deal ID
    - hubspot_configured: Whether HubSpot is configured
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
        if not is_admin and client_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        status_result = await hubspot_service.get_sync_status(client_id, db)
        
        return {
            "success": True,
            "data": status_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting HubSpot status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get HubSpot status: {str(e)}"
        )


@router.post("/{client_id}/hubspot/sync", summary="Sync client to HubSpot")
async def sync_client_hubspot(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually sync a client to HubSpot CRM.
    
    Creates or updates:
    - Company record
    - Contact for primary admin
    - Deal associated with Company
    
    Only admin users can trigger manual sync.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can sync clients to HubSpot"
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
        
        sync_result = await hubspot_service.sync_client_to_hubspot(client, db)
        
        if sync_result.get("success"):
            return {
                "success": True,
                "message": "Client synced to HubSpot successfully",
                "data": {
                    "hubspot_company_id": sync_result.get("hubspot_company_id"),
                    "hubspot_contact_id": sync_result.get("hubspot_contact_id"),
                    "hubspot_deal_id": sync_result.get("hubspot_deal_id")
                }
            }
        else:
            return {
                "success": False,
                "message": "HubSpot sync failed",
                "error": sync_result.get("error")
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error syncing to HubSpot: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync to HubSpot: {str(e)}"
        )


class HubSpotOnboardingUpdate(BaseModel):
    """Request model for updating HubSpot onboarding status."""
    welcome_email_sent: bool | None = None
    workos_configured: bool | None = None
    sso_enabled: bool | None = None
    users_count: int | None = None


@router.put("/{client_id}/hubspot/onboarding", summary="Update HubSpot onboarding status")
async def update_hubspot_onboarding(
    client_id: str,
    data: HubSpotOnboardingUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update onboarding status on HubSpot for a client.
    
    Updates custom properties on HubSpot Company/Deal:
    - lia_welcome_email_sent
    - lia_workos_configured
    - lia_sso_enabled
    - lia_users_count
    
    Only admin users can update HubSpot onboarding status.
    """
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can update HubSpot onboarding status"
            )
        
        status_data = data.model_dump(exclude_unset=True)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided"
            )
        
        update_result = await hubspot_service.update_onboarding_status(
            client_id=client_id,
            status=status_data,
            db=db
        )
        
        if update_result.get("success"):
            return {
                "success": True,
                "message": "HubSpot onboarding status updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update HubSpot onboarding status",
                "error": update_result.get("error")
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating HubSpot onboarding: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update HubSpot onboarding status: {str(e)}"
        )
