"""
ATS Integration API endpoints (Gupy + Pandapé).
"""
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.ats_integration.services.gupy_service import GupyService
from app.domains.ats_integration.services.pandape_service import PandapeService
from app.models.ats_integration import (
    ATSCandidate,
    ATSConnection,
    ATSProvider,
    ATSSyncJob,
    ATSWebhookLog,
    SyncStatus,
)
from app.shared.encryption import encrypt_value

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class CreateATSConnectionRequest(BaseModel):
    provider: str  # "gupy" or "pandape"
    provider_name: str
    api_key: str
    api_secret: str | None = None
    api_endpoint: str | None = None
    company_id: str | None = None
    auto_sync_enabled: bool = True
    sync_frequency_hours: int = 24


class TriggerSyncRequest(BaseModel):
    sync_type: str = "full"  # full, candidates, jobs, applications
    filters: dict = {}


@router.post("/ats/connections", response_model=dict)
async def create_ats_connection(
    request: CreateATSConnectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new ATS connection (Gupy or Pandapé).
    """
    try:
        # Validate provider
        if request.provider.lower() not in ["gupy", "pandape"]:
            raise HTTPException(
                status_code=400,
                detail="Provider must be 'gupy' or 'pandape'"
            )
        
        # Test connection before saving
        if request.provider.lower() == "gupy":
            service = GupyService(api_key=request.api_key)
        else:  # pandape
            service = PandapeService(
                api_key=request.api_key,
                api_url=request.api_endpoint
            )
        
        connection_ok = await service.test_connection()
        
        if not connection_ok:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to ATS. Please verify your API credentials."
            )
        
        # Create connection record
        connection = ATSConnection(
            provider=ATSProvider[request.provider.upper()],
            provider_name=request.provider_name,
            api_key=encrypt_value(request.api_key),
            api_secret=encrypt_value(request.api_secret) if request.api_secret else None,
            api_endpoint=request.api_endpoint,
            company_id=request.company_id,
            is_active=True,
            auto_sync_enabled=request.auto_sync_enabled,
            sync_frequency_hours=request.sync_frequency_hours,
            created_by="admin"
        )
        
        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        
        logger.info(f"✅ ATS connection created: {request.provider} - {connection.id}")
        
        return {
            "success": True,
            "connection_id": str(connection.id),
            "provider": request.provider,
            "message": f"{request.provider_name} connected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create ATS connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ats/connections", response_model=list[dict])
async def list_ats_connections(db: AsyncSession = Depends(get_db)):
    """
    List all ATS connections.
    """
    try:
        result = await db.execute(
            select(ATSConnection).where(ATSConnection.is_active == True)
        )
        connections = result.scalars().all()
        
        return [
            {
                "id": str(conn.id),
                "provider": conn.provider.value,
                "provider_name": conn.provider_name,
                "is_active": conn.is_active,
                "auto_sync_enabled": conn.auto_sync_enabled,
                "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
                "last_sync_status": conn.last_sync_status.value if conn.last_sync_status else None,
                "total_candidates_synced": conn.total_candidates_synced,
                "total_jobs_synced": conn.total_jobs_synced,
                "created_at": conn.created_at.isoformat()
            }
            for conn in connections
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to list ATS connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ats/connections/{connection_id}/sync", response_model=dict)
async def trigger_ats_sync(
    connection_id: str,
    request: TriggerSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger synchronization for an ATS connection.
    """
    try:
        # Get connection
        result = await db.execute(
            select(ATSConnection).where(ATSConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Create sync job
        sync_job = ATSSyncJob(
            connection_id=connection.id,
            provider=connection.provider,
            sync_type=request.sync_type,
            sync_direction="import",
            status=SyncStatus.PENDING,
            filters_applied=request.filters,
            triggered_by="user"
        )
        
        db.add(sync_job)
        await db.commit()
        await db.refresh(sync_job)
        
        # TODO: Execute sync in background task
        # For now, we'll just create the job and return
        
        logger.info(f"✅ Sync job created: {sync_job.id} for connection {connection_id}")
        
        return {
            "success": True,
            "sync_job_id": str(sync_job.id),
            "status": "pending",
            "message": "Sync job created successfully. Processing will start shortly."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ats/sync-jobs", response_model=list[dict])
async def list_sync_jobs(
    connection_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List ATS synchronization jobs.
    """
    try:
        query = select(ATSSyncJob)
        
        filters = []
        if connection_id:
            filters.append(ATSSyncJob.connection_id == connection_id)
        if status:
            filters.append(ATSSyncJob.status == SyncStatus[status.upper()])
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(ATSSyncJob.created_at)).limit(limit)
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return [
            {
                "id": str(job.id),
                "connection_id": str(job.connection_id),
                "provider": job.provider.value,
                "sync_type": job.sync_type,
                "status": job.status.value,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "duration_seconds": job.duration_seconds,
                "records_created": job.records_created,
                "records_updated": job.records_updated,
                "records_failed": job.records_failed,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat()
            }
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to list sync jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ats/candidates", response_model=list[dict])
async def list_ats_candidates(
    provider: str | None = Query(None, description="Filter by provider (gupy/pandape)"),
    connection_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    List candidates imported from ATS platforms.
    """
    try:
        query = select(ATSCandidate)
        
        filters = [ATSCandidate.is_active == True]
        
        if provider:
            filters.append(ATSCandidate.provider == ATSProvider[provider.upper()])
        if connection_id:
            filters.append(ATSCandidate.connection_id == connection_id)
        
        query = query.where(and_(*filters))
        query = query.order_by(desc(ATSCandidate.last_synced_at)).limit(limit)
        
        result = await db.execute(query)
        candidates = result.scalars().all()
        
        return [
            {
                "id": str(candidate.id),
                "provider": candidate.provider.value,
                "ats_candidate_id": candidate.ats_candidate_id,
                "name": candidate.name,
                "email": candidate.email,
                "phone": candidate.phone,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "applied_job_title": candidate.applied_job_title,
                "application_status": candidate.application_status,
                "current_stage": candidate.current_stage,
                "ats_score": candidate.ats_score,
                "last_synced_at": candidate.last_synced_at.isoformat()
            }
            for candidate in candidates
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to list ATS candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ats/webhooks/{provider}", response_model=dict)
async def receive_ats_webhook(
    provider: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Receive webhook events from ATS platforms.
    """
    try:
        # Validate provider
        if provider.lower() not in ["gupy", "pandape"]:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        # Log webhook
        webhook_log = ATSWebhookLog(
            provider=ATSProvider[provider.upper()],
            event_type=payload.get("event") or payload.get("eventType", "unknown"),
            event_id=payload.get("id"),
            payload=payload,
            processed=False
        )
        
        db.add(webhook_log)
        await db.commit()
        
        logger.info(f"✅ Webhook received: {provider} - {webhook_log.event_type}")
        
        # TODO: Process webhook in background task
        # For now, just acknowledge receipt
        
        return {
            "success": True,
            "message": "Webhook received",
            "webhook_id": str(webhook_log.id)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ats/webhooks", response_model=list[dict])
async def list_webhook_logs(
    provider: str | None = Query(None),
    processed: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    List webhook logs from ATS platforms.
    """
    try:
        query = select(ATSWebhookLog)
        
        filters = []
        if provider:
            filters.append(ATSWebhookLog.provider == ATSProvider[provider.upper()])
        if processed is not None:
            filters.append(ATSWebhookLog.processed == processed)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(ATSWebhookLog.received_at)).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": str(log.id),
                "provider": log.provider.value,
                "event_type": log.event_type,
                "event_id": log.event_id,
                "processed": log.processed,
                "processed_at": log.processed_at.isoformat() if log.processed_at else None,
                "received_at": log.received_at.isoformat(),
                "processing_error": log.processing_error
            }
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to list webhook logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
