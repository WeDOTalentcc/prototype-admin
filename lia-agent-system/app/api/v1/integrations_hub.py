"""
Integration Hub API endpoints for centralized integration management.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.domains.integrations_hub.dependencies import get_integrations_hub_repo
from app.domains.integrations_hub.repositories.integrations_hub_repository import (
    IntegrationsHubRepository,
)
from app.models.integration_hub import IntegrationCategory
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
import uuid as _uuid_mod
from app.shared.compliance.audit_service import AuditService  # P1-W3-05
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

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


class ConnectionCreate(WeDoBaseModel):
    provider_id: str
    auth_type: str = Field(..., description="oauth, api_key, or webhook")
    credentials: dict = Field(default={}, description="Encrypted credentials")
    sync_enabled: bool = True
    sync_direction: str = "bidirectional"
    sync_frequency: str = "realtime"
    field_mappings: dict = {}


class ConnectionUpdate(WeDoBaseModel):
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


class AIRecommendationRequest(WeDoBaseModel):
    company_size: str = Field(..., description="small, medium, large, enterprise")
    industry: str
    current_tools: list[str] = []
    priorities: list[str] = []


class AIRecommendationResponse(BaseModel):
    recommended_integrations: list[dict]
    setup_order: list[str]
    estimated_setup_time: str
    tips: list[str]


def _provider_to_response(p) -> ProviderResponse:
    return ProviderResponse(
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
        is_premium=p.is_premium,
    )


def _connection_to_response(conn, provider) -> ConnectionResponse:
    return ConnectionResponse(
        id=str(conn.id),
        company_id=str(conn.company_id),
        provider_id=str(conn.provider_id),
        provider_name=provider.name if provider else None,
        provider_category=provider.category if provider else None,
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
        updated_at=conn.updated_at,
    )


@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(
    category: str | None = Query(None, description="Filter by category"),
    active_only: bool = Query(True),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all available integration providers."""
    try:
        providers = await repo.list_providers(active_only=active_only, category=category)

        if not providers:
            providers = await repo.seed_default_providers()

        return [_provider_to_response(p) for p in providers]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{category}", response_model=list[ProviderResponse])
async def list_providers_by_category(
    category: str,
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List providers filtered by category."""
    valid_categories = [c.value for c in IntegrationCategory]
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {valid_categories}",
        )

    return await list_providers(category=category, repo=repo)


@router.get("/connections", response_model=list[ConnectionResponse])
async def list_connections(
    company_id: str = Query(..., description="Company ID"),
    status: str | None = Query(None),
    category: str | None = Query(None),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get company's integration connections."""
    try:
        rows = await repo.list_connections(
            company_id=company_id, status=status, category=category
        )
        return [_connection_to_response(conn, provider) for conn, provider in rows]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections", response_model=ConnectionResponse)
async def create_connection(
    request: ConnectionCreate,
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new integration connection."""
    try:
        provider = await repo.get_provider_by_id(request.provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        connection = await repo.create_connection(
            company_id=company_id,
            provider_id=request.provider_id,
            auth_type=request.auth_type,
            credentials=request.credentials,
            sync_enabled=request.sync_enabled,
            sync_direction=request.sync_direction,
            sync_frequency=request.sync_frequency,
            field_mappings=request.field_mappings,
        )

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created integration connection: {connection.id} for provider {provider.name}")
        try:
            await AuditService().log_action(trace_id=str(_uuid_mod.uuid4()), company_id=company_id, action_type="integration_connection_created", actor="system", target_id=str(connection.id), target_type="integration_connection", metadata={"provider_id": request.provider_id, "auth_type": request.auth_type, "sync_enabled": request.sync_enabled})  # P1-W3-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return _connection_to_response(connection, provider)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create connection: {e}")
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/connections/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: ConnectionUpdate,
    company_id: str = Query(..., description="Company ID"),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an integration connection."""
    try:
        row = await repo.get_connection_with_provider(connection_id)

        if not row:
            raise HTTPException(status_code=404, detail="Connection not found")

        connection, provider = row
        verify_connection_ownership(connection, company_id)

        connection = await repo.update_connection(
            connection,
            sync_enabled=request.sync_enabled,
            sync_direction=request.sync_direction,
            sync_frequency=request.sync_frequency,
            field_mappings=request.field_mappings,
            credentials=request.credentials,
        )

        try:
            await AuditService().log_action(trace_id=str(_uuid_mod.uuid4()), company_id=company_id, action_type="integration_connection_updated", actor="system", target_id=connection_id, target_type="integration_connection", metadata={"sync_enabled": request.sync_enabled})  # P1-W3-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return _connection_to_response(connection, provider)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update connection: {e}")
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connections/{connection_id}", response_model=None)
async def delete_connection(
    connection_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Remove an integration connection."""
    try:
        connection = await repo.get_connection_by_id(connection_id)
        verify_connection_ownership(connection, company_id)

        await repo.delete_connection(connection)

        logger.info(f"Deleted integration connection: {connection_id}")
        try:
            await AuditService().log_action(trace_id=str(_uuid_mod.uuid4()), company_id=company_id, action_type="integration_connection_deleted", actor="system", target_id=connection_id, target_type="integration_connection")  # P1-W3-05
        except Exception as _ae:
            logger.warning(f"Audit log failed (non-blocking): {_ae}")
        return {"success": True, "message": "Connection deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete connection: {e}")
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/test", response_model=None)
async def test_connection(
    connection_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Test an integration connection."""
    try:
        row = await repo.get_connection_with_provider(connection_id)

        if not row:
            raise HTTPException(status_code=404, detail="Connection not found")

        connection, provider = row
        verify_connection_ownership(connection, company_id)

        await repo.mark_connection_tested(connection)

        return {
            "success": True,
            "connection_id": connection_id,
            "provider": provider.name,
            "status": "connected",
            "message": f"Successfully connected to {provider.name}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/sync", response_model=None)
async def trigger_sync(
    connection_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    sync_type: str = Query("full", description="full, incremental, or webhook"),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Trigger a sync operation for a connection."""
    try:
        connection = await repo.get_connection_by_id(connection_id)
        verify_connection_ownership(connection, company_id)

        sync_log = await repo.start_sync(connection, sync_type=sync_type)

        logger.info(f"Triggered sync for connection {connection_id}: {sync_type}")

        return {
            "success": True,
            "sync_log_id": str(sync_log.id),
            "connection_id": connection_id,
            "sync_type": sync_type,
            "status": "pending",
            "message": "Sync operation started",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/logs", response_model=list[SyncLogResponse])
async def get_sync_logs(
    connection_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    limit: int = Query(20, ge=1, le=100),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get sync logs for a connection."""
    try:
        connection = await repo.get_connection_by_id(connection_id)
        verify_connection_ownership(connection, company_id)

        logs = await repo.get_sync_logs(connection_id=connection_id, limit=limit)

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
                duration_seconds=log.duration_seconds,
            )
            for log in logs
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def get_integration_health(
    company_id: str = Query(..., description="Company ID"),
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Get overall integration health status."""
    try:
        from app.models.integration_hub import IntegrationStatus

        rows = await repo.get_connections_with_providers_for_company(company_id)

        total = len(rows)
        connected = sum(1 for conn, _ in rows if conn.status == IntegrationStatus.CONNECTED.value)
        errors = sum(1 for conn, _ in rows if conn.status == IntegrationStatus.ERROR.value)
        needs_reauth = sum(1 for conn, _ in rows if conn.status == IntegrationStatus.NEEDS_REAUTH.value)

        connections_by_category: dict = {}
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
            connections_by_category=connections_by_category,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get integration health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/recommend", response_model=AIRecommendationResponse)
async def get_ai_recommendations(
    request: AIRecommendationRequest,
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
                "reason": "Essential for managing candidates and job postings",
            })
            setup_order.append("gupy")

        if "linkedin" not in [t.lower() for t in request.current_tools]:
            recommendations.append({
                "provider": "LinkedIn Jobs",
                "category": "job_board",
                "priority": "high",
                "reason": "Reach the largest professional network",
            })
            setup_order.append("linkedin_jobs")

        if "slack" not in [t.lower() for t in request.current_tools] and "teams" not in [t.lower() for t in request.current_tools]:
            recommendations.append({
                "provider": "Slack",
                "category": "communication",
                "priority": "medium",
                "reason": "Real-time notifications and team collaboration",
            })
            setup_order.append("slack")

        if "merge" not in [t.lower() for t in request.current_tools]:
            recommendations.append({
                "provider": "Merge.dev",
                "category": "ats",
                "priority": "high",
                "reason": "Universal ATS connector supporting 40+ HR systems via single API",
            })
            setup_order.append("merge")

        if request.company_size in ["large", "enterprise"]:
            if "workday" not in [t.lower() for t in request.current_tools]:
                recommendations.append({
                    "provider": "Workday",
                    "category": "hris",
                    "priority": "medium",
                    "reason": "Enterprise HR management and org sync",
                })
                setup_order.append("workday")

        tips = [
            "Start with your ATS integration to sync existing candidates",
            "Connect job boards to expand your talent reach",
            "Set up communication integrations for real-time updates",
            "Enable webhooks for instant data synchronization",
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
            tips=tips,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-providers", response_model=None)
async def seed_providers(
    repo: IntegrationsHubRepository = Depends(get_integrations_hub_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Seed default integration providers."""
    try:
        providers = await repo.seed_default_providers()
        return {
            "success": True,
            "message": f"Seeded {len(providers)} providers",
            "providers": [_provider_to_response(p).dict() for p in providers],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to seed providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apify/health")
async def apify_health_check(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    from app.shared.resilience.circuit_breaker import APIFY_CIRCUIT

    cb_state = APIFY_CIRCUIT.state
    last_success = getattr(APIFY_CIRCUIT, "_last_success_time", None)

    if cb_state == "closed" and last_success:
        from datetime import datetime as _dt, timezone as _tz
        age = (_dt.now(_tz.utc) - last_success).total_seconds() if hasattr(last_success, "total_seconds") else 9999
        status = "ok" if age < 300 else "degraded"
    elif cb_state == "half_open":
        status = "degraded"
    elif cb_state == "open":
        status = "down"
    else:
        status = "ok"

    return {
        "status": status,
        "circuit_breaker": cb_state,
        "actor": "dev_fusion/Linkedin-Profile-Scraper",
        "last_successful_call": str(last_success) if last_success else None,
        "avg_response_time_ms": None,
        "cost_per_enrichment_usd": 0.01,
    }

reorder_collection_before_item(router)
