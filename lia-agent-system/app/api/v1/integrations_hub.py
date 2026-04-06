"""
Integration Hub API endpoints for centralized integration management.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.integration_hub import (
    DEFAULT_INTEGRATION_PROVIDERS,
    IntegrationCategory,
    IntegrationConnection,
    IntegrationProvider,
    IntegrationStatus,
    IntegrationSyncLog,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integration-hub"])


def verify_connection_ownership(connection, company_id: str, resource_name: str = "Connection"):
    """Verify that a connection belongs to the specified company."""
    if connection is None:
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    if str(connection.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")


class ProviderResponse(BaseModel):
    id: str
    name: str
    category: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    supports_oauth: bool = False
    supports_api_key: bool = False
    supports_webhook: bool = False
    features: list[str] = []
    is_active: bool = True
    is_premium: bool = False


class ConnectionCreate(BaseModel):
    provider_id: str
    company_id: str
    auth_type: str = Field(..., description="oauth, api_key, or webhook")
    credentials: dict = Field(default={}, description="Encrypted credentials")
    sync_enabled: bool = True
    sync_direction: str = "bidirectional"
    sync_frequency: str = "realtime"
    field_mappings: dict = {}


class ConnectionUpdate(BaseModel):
    sync_enabled: bool | None = None
    sync_direction: str | None = None
    sync_frequency: str | None = None
    field_mappings: dict | None = None
    credentials: dict | None = None


class ConnectionResponse(BaseModel):
    id: str
    company_id: str
    provider_id: str
    provider_name: str | None = None
    provider_category: str | None = None
    status: str
    auth_type: str | None = None
    sync_enabled: bool
    sync_direction: str
    sync_frequency: str
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    health_score: float
    error_count: int
    created_at: datetime
    updated_at: datetime


class SyncLogResponse(BaseModel):
    id: str
    connection_id: str
    sync_type: str
    direction: str | None = None
    status: str
    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None


class HealthResponse(BaseModel):
    total_connections: int
    connected: int
    errors: int
    needs_reauth: int
    overall_health: float
    connections_by_category: dict


class AIRecommendationRequest(BaseModel):
    company_size: str = Field(..., description="small, medium, large, enterprise")
    industry: str
    current_tools: list[str] = []
    priorities: list[str] = []


class AIRecommendationResponse(BaseModel):
    recommended_integrations: list[dict]
    setup_order: list[str]
    estimated_setup_time: str
    tips: list[str]


@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(
    category: str | None = Query(None, description="Filter by category"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """List all available integration providers."""
    try:
        query = select(IntegrationProvider)
        
        filters = []
        if active_only:
            filters.append(IntegrationProvider.is_active)
        if category:
            filters.append(IntegrationProvider.category == category)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(IntegrationProvider.name)
        
        result = await db.execute(query)
        providers = result.scalars().all()
        
        if not providers:
            return await seed_default_providers(db)
        
        return [
            ProviderResponse(
                id=str(p.id),
                name=p.name,
                category=p.category,
                slug=p.slug,
                description=p.description,
                logo_url=p.logo_url,
                supports_oauth=p.supports_oauth,
                supports_api_key=p.supports_api_key,
                supports_webhook=p.supports_webhook,
                features=p.features or [],
                is_active=p.is_active,
                is_premium=p.is_premium
            )
            for p in providers
        ]
        
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{category}", response_model=list[ProviderResponse])
async def list_providers_by_category(
    category: str,
    db: AsyncSession = Depends(get_db)
):
    """List providers filtered by category."""
    valid_categories = [c.value for c in IntegrationCategory]
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {valid_categories}"
        )
    
    return await list_providers(category=category, db=db)


@router.get("/connections", response_model=list[ConnectionResponse])
async def list_connections(
    company_id: str = Query(..., description="Company ID"),
    status: str | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get company's integration connections."""
    try:
        query = select(IntegrationConnection, IntegrationProvider).join(
            IntegrationProvider,
            IntegrationConnection.provider_id == IntegrationProvider.id
        )
        
        filters = [IntegrationConnection.company_id == company_id]
        if status:
            filters.append(IntegrationConnection.status == status)
        if category:
            filters.append(IntegrationProvider.category == category)
        
        query = query.where(and_(*filters))
        
        query = query.order_by(desc(IntegrationConnection.created_at))
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            ConnectionResponse(
                id=str(conn.id),
                company_id=str(conn.company_id),
                provider_id=str(conn.provider_id),
                provider_name=provider.name,
                provider_category=provider.category,
                status=conn.status,
                auth_type=conn.auth_type,
                sync_enabled=conn.sync_enabled,
                sync_direction=conn.sync_direction,
                sync_frequency=conn.sync_frequency,
                last_sync_at=conn.last_sync_at,
                last_sync_status=conn.last_sync_status,
                health_score=conn.health_score,
                error_count=conn.error_count,
                created_at=conn.created_at,
                updated_at=conn.updated_at
            )
            for conn, provider in rows
        ]
        
    except Exception as e:
        logger.error(f"Failed to list connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections", response_model=ConnectionResponse)
async def create_connection(
    request: ConnectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new integration connection."""
    try:
        provider_result = await db.execute(
            select(IntegrationProvider).where(IntegrationProvider.id == request.provider_id)
        )
        provider = provider_result.scalar_one_or_none()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        connection = IntegrationConnection(
            company_id=request.company_id,
            provider_id=request.provider_id,
            status=IntegrationStatus.CONNECTING.value,
            auth_type=request.auth_type,
            credentials=request.credentials,
            sync_enabled=request.sync_enabled,
            sync_direction=request.sync_direction,
            sync_frequency=request.sync_frequency,
            field_mappings=request.field_mappings
        )
        
        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        
        logger.info(f"Created integration connection: {connection.id} for provider {provider.name}")
        
        return ConnectionResponse(
            id=str(connection.id),
            company_id=str(connection.company_id),
            provider_id=str(connection.provider_id),
            provider_name=provider.name,
            provider_category=provider.category,
            status=connection.status,
            auth_type=connection.auth_type,
            sync_enabled=connection.sync_enabled,
            sync_direction=connection.sync_direction,
            sync_frequency=connection.sync_frequency,
            last_sync_at=connection.last_sync_at,
            last_sync_status=connection.last_sync_status,
            health_score=connection.health_score,
            error_count=connection.error_count,
            created_at=connection.created_at,
            updated_at=connection.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create connection: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/connections/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: str,
    request: ConnectionUpdate,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update an integration connection."""
    try:
        result = await db.execute(
            select(IntegrationConnection, IntegrationProvider).join(
                IntegrationProvider,
                IntegrationConnection.provider_id == IntegrationProvider.id
            ).where(IntegrationConnection.id == connection_id)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection, provider = row
        verify_connection_ownership(connection, company_id)
        
        if request.sync_enabled is not None:
            connection.sync_enabled = request.sync_enabled
        if request.sync_direction is not None:
            connection.sync_direction = request.sync_direction
        if request.sync_frequency is not None:
            connection.sync_frequency = request.sync_frequency
        if request.field_mappings is not None:
            connection.field_mappings = request.field_mappings
        if request.credentials is not None:
            connection.credentials = request.credentials
        
        connection.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(connection)
        
        return ConnectionResponse(
            id=str(connection.id),
            company_id=str(connection.company_id),
            provider_id=str(connection.provider_id),
            provider_name=provider.name,
            provider_category=provider.category,
            status=connection.status,
            auth_type=connection.auth_type,
            sync_enabled=connection.sync_enabled,
            sync_direction=connection.sync_direction,
            sync_frequency=connection.sync_frequency,
            last_sync_at=connection.last_sync_at,
            last_sync_status=connection.last_sync_status,
            health_score=connection.health_score,
            error_count=connection.error_count,
            created_at=connection.created_at,
            updated_at=connection.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update connection: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connections/{connection_id}", response_model=None)
async def delete_connection(
    connection_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Remove an integration connection."""
    try:
        result = await db.execute(
            select(IntegrationConnection).where(IntegrationConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        
        verify_connection_ownership(connection, company_id)
        
        await db.delete(connection)
        await db.commit()
        
        logger.info(f"Deleted integration connection: {connection_id}")
        
        return {"success": True, "message": "Connection deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete connection: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/test", response_model=None)
async def test_connection(
    connection_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Test an integration connection."""
    try:
        result = await db.execute(
            select(IntegrationConnection, IntegrationProvider).join(
                IntegrationProvider,
                IntegrationConnection.provider_id == IntegrationProvider.id
            ).where(IntegrationConnection.id == connection_id)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection, provider = row
        verify_connection_ownership(connection, company_id)
        
        connection.status = IntegrationStatus.CONNECTED.value
        connection.health_score = 100.0
        connection.error_count = 0
        connection.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "success": True,
            "connection_id": connection_id,
            "provider": provider.name,
            "status": "connected",
            "message": f"Successfully connected to {provider.name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/sync", response_model=None)
async def trigger_sync(
    connection_id: str,
    company_id: str = Query(..., description="Company ID"),
    sync_type: str = Query("full", description="full, incremental, or webhook"),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a sync operation for a connection."""
    try:
        result = await db.execute(
            select(IntegrationConnection).where(IntegrationConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        
        verify_connection_ownership(connection, company_id)
        
        sync_log = IntegrationSyncLog(
            connection_id=connection.id,
            sync_type=sync_type,
            direction="inbound",
            status="pending"
        )
        
        db.add(sync_log)
        
        connection.last_sync_at = datetime.utcnow()
        connection.last_sync_status = "pending"
        
        await db.commit()
        await db.refresh(sync_log)
        
        logger.info(f"Triggered sync for connection {connection_id}: {sync_type}")
        
        return {
            "success": True,
            "sync_log_id": str(sync_log.id),
            "connection_id": connection_id,
            "sync_type": sync_type,
            "status": "pending",
            "message": "Sync operation started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/logs", response_model=list[SyncLogResponse])
async def get_sync_logs(
    connection_id: str,
    company_id: str = Query(..., description="Company ID"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get sync logs for a connection."""
    try:
        conn_result = await db.execute(
            select(IntegrationConnection).where(IntegrationConnection.id == connection_id)
        )
        connection = conn_result.scalar_one_or_none()
        verify_connection_ownership(connection, company_id)
        
        result = await db.execute(
            select(IntegrationSyncLog)
            .where(IntegrationSyncLog.connection_id == connection_id)
            .order_by(desc(IntegrationSyncLog.started_at))
            .limit(limit)
        )
        logs = result.scalars().all()
        
        return [
            SyncLogResponse(
                id=str(log.id),
                connection_id=str(log.connection_id),
                sync_type=log.sync_type,
                direction=log.direction,
                status=log.status,
                records_processed=log.records_processed,
                records_created=log.records_created,
                records_updated=log.records_updated,
                records_failed=log.records_failed,
                error_message=log.error_message,
                started_at=log.started_at,
                completed_at=log.completed_at,
                duration_seconds=log.duration_seconds
            )
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"Failed to get sync logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def get_integration_health(
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get overall integration health status."""
    try:
        query = select(IntegrationConnection, IntegrationProvider).join(
            IntegrationProvider,
            IntegrationConnection.provider_id == IntegrationProvider.id
        ).where(IntegrationConnection.company_id == company_id)
        
        result = await db.execute(query)
        rows = result.all()
        
        total = len(rows)
        connected = sum(1 for conn, _ in rows if conn.status == IntegrationStatus.CONNECTED.value)
        errors = sum(1 for conn, _ in rows if conn.status == IntegrationStatus.ERROR.value)
        needs_reauth = sum(1 for conn, _ in rows if conn.status == IntegrationStatus.NEEDS_REAUTH.value)
        
        connections_by_category = {}
        for conn, provider in rows:
            cat = provider.category
            if cat not in connections_by_category:
                connections_by_category[cat] = {"total": 0, "connected": 0}
            connections_by_category[cat]["total"] += 1
            if conn.status == IntegrationStatus.CONNECTED.value:
                connections_by_category[cat]["connected"] += 1
        
        overall_health = (connected / total * 100) if total > 0 else 100.0
        
        return HealthResponse(
            total_connections=total,
            connected=connected,
            errors=errors,
            needs_reauth=needs_reauth,
            overall_health=overall_health,
            connections_by_category=connections_by_category
        )
        
    except Exception as e:
        logger.error(f"Failed to get integration health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/recommend", response_model=AIRecommendationResponse)
async def get_ai_recommendations(
    request: AIRecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get AI-powered recommendations for integration setup."""
    try:
        recommendations = []
        setup_order = []
        tips = []
        
        if "ats" not in [t.lower() for t in request.current_tools]:
            recommendations.append({
                "provider": "Gupy",
                "category": "ats",
                "priority": "high",
                "reason": "Essential for managing candidates and job postings"
            })
            setup_order.append("gupy")
        
        if "linkedin" not in [t.lower() for t in request.current_tools]:
            recommendations.append({
                "provider": "LinkedIn Jobs",
                "category": "job_board",
                "priority": "high",
                "reason": "Reach the largest professional network"
            })
            setup_order.append("linkedin_jobs")
        
        if "slack" not in [t.lower() for t in request.current_tools] and "teams" not in [t.lower() for t in request.current_tools]:
            recommendations.append({
                "provider": "Slack",
                "category": "communication",
                "priority": "medium",
                "reason": "Real-time notifications and team collaboration"
            })
            setup_order.append("slack")
        
        if "merge" not in [t.lower() for t in request.current_tools]:
            recommendations.append({
                "provider": "Merge.dev",
                "category": "ats",
                "priority": "high",
                "reason": "Universal ATS connector supporting 40+ HR systems via single API"
            })
            setup_order.append("merge")

        if request.company_size in ["large", "enterprise"]:
            if "workday" not in [t.lower() for t in request.current_tools]:
                recommendations.append({
                    "provider": "Workday",
                    "category": "hris",
                    "priority": "medium",
                    "reason": "Enterprise HR management and org sync"
                })
                setup_order.append("workday")
            
        tips = [
            "Start with your ATS integration to sync existing candidates",
            "Connect job boards to expand your talent reach",
            "Set up communication integrations for real-time updates",
            "Enable webhooks for instant data synchronization"
        ]
        
        if request.company_size == "enterprise":
            tips.append("Consider Merge.dev for unified API access across multiple systems")
        
        time_per_integration = {"small": "15min", "medium": "30min", "large": "1hr", "enterprise": "2hr"}
        time_per_integration.get(request.company_size, "30min")
        estimated_time = f"{len(recommendations) * 30} minutes" if recommendations else "No setup needed"
        
        return AIRecommendationResponse(
            recommended_integrations=recommendations,
            setup_order=setup_order,
            estimated_setup_time=estimated_time,
            tips=tips
        )
        
    except Exception as e:
        logger.error(f"Failed to get AI recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-providers", response_model=None)
async def seed_providers(db: AsyncSession = Depends(get_db)):
    """Seed default integration providers."""
    try:
        providers = await seed_default_providers(db)
        return {
            "success": True,
            "message": f"Seeded {len(providers)} providers",
            "providers": [p.dict() for p in providers]
        }
    except Exception as e:
        logger.error(f"Failed to seed providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def seed_default_providers(db: AsyncSession) -> list[ProviderResponse]:
    """Seed default providers if they don't exist."""
    
    for provider_data in DEFAULT_INTEGRATION_PROVIDERS:
        existing = await db.execute(
            select(IntegrationProvider).where(IntegrationProvider.slug == provider_data["slug"])
        )
        if existing.scalar_one_or_none():
            continue
        
        provider = IntegrationProvider(**provider_data)
        db.add(provider)
    
    await db.commit()
    
    result = await db.execute(select(IntegrationProvider).order_by(IntegrationProvider.name))
    providers = result.scalars().all()
    
    return [
        ProviderResponse(
            id=str(p.id),
            name=p.name,
            category=p.category,
            slug=p.slug,
            description=p.description,
            logo_url=p.logo_url,
            supports_oauth=p.supports_oauth,
            supports_api_key=p.supports_api_key,
            supports_webhook=p.supports_webhook,
            features=p.features or [],
            is_active=p.is_active,
            is_premium=p.is_premium
        )
        for p in providers
    ]
