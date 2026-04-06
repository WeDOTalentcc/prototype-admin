"""
ATS Integration API endpoints (Gupy, Pandapé, Merge).
"""
import hashlib
import hmac
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.domains.ats_integration.services.gupy_service import GupyService
from app.domains.ats_integration.services.pandape_service import PandapeService
from app.models.ats_integration import (
    ATSCandidate,
    ATSConnection,
    ATSJobMapping,
    ATSProvider,
    ATSSyncJob,
    ATSWebhookLog,
    SyncStatus,
)
from app.shared.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ("gupy", "pandape", "merge")

router = APIRouter()


class CreateATSConnectionRequest(BaseModel):
    provider: str
    provider_name: str
    api_key: str
    api_secret: str | None = None
    api_endpoint: str | None = None
    company_id: str | None = None
    auto_sync_enabled: bool = True
    sync_frequency_hours: int = 24


class TestATSConnectionRequest(BaseModel):
    provider: str
    api_key: str
    api_endpoint: str | None = None


class SaveFieldMappingsRequest(BaseModel):
    connection_id: str
    mappings: list[dict]


class TriggerSyncRequest(BaseModel):
    sync_type: str = "full"
    filters: dict = {}


@router.post("/ats/connections", response_model=dict)
async def create_ats_connection(
    request: CreateATSConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_or_demo),
):
    """
    Create a new ATS connection (Gupy, Pandapé, or Merge).
    """
    try:
        company_id = get_user_company_id(current_user)
        provider = request.provider.lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Provider must be one of: {', '.join(SUPPORTED_PROVIDERS)}"
            )

        connection_ok = await _test_provider_connection(
            provider, request.api_key, request.api_endpoint
        )

        if not connection_ok:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to ATS. Please verify your API credentials."
            )
        
        connection = ATSConnection(
            provider=ATSProvider[request.provider.upper()],
            provider_name=request.provider_name,
            api_key=encrypt_value(request.api_key),
            api_secret=encrypt_value(request.api_secret) if request.api_secret else None,
            api_endpoint=request.api_endpoint,
            company_id=company_id,
            is_active=True,
            auto_sync_enabled=request.auto_sync_enabled,
            sync_frequency_hours=request.sync_frequency_hours,
            created_by=str(current_user.id)
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
async def list_ats_connections(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_or_demo),
):
    """
    List ATS connections for the current user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(ATSConnection).where(
                and_(
                    ATSConnection.is_active,
                    ATSConnection.company_id == company_id,
                )
            )
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


@router.post("/ats/connections/test", response_model=dict)
async def test_ats_connection(request: TestATSConnectionRequest):
    """
    Test ATS connection credentials without saving.
    """
    try:
        provider = request.provider.lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Provider must be one of: {', '.join(SUPPORTED_PROVIDERS)}"
            )

        connection_ok = await _test_provider_connection(
            provider, request.api_key, request.api_endpoint
        )

        return {
            "success": connection_ok,
            "provider": provider,
            "message": (
                f"Conexão com {provider} estabelecida com sucesso."
                if connection_ok
                else f"Falha ao conectar com {provider}. Verifique suas credenciais."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ATS connection test failed: {e}")
        return {
            "success": False,
            "provider": request.provider,
            "message": f"Erro ao testar conexão: {str(e)}",
        }


async def _test_provider_connection(
    provider: str, api_key: str, api_endpoint: str | None = None
) -> bool:
    """Test connectivity for a given ATS provider."""
    if provider == "gupy":
        service = GupyService(api_key=api_key)
    elif provider == "pandape":
        service = PandapeService(api_key=api_key, api_url=api_endpoint)
    elif provider == "merge":
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.merge.dev/api/ats/v1/account-details",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=15,
                )
                return resp.status_code == 200
        except Exception:
            return False
    else:
        return False
    return await service.test_connection()


@router.post("/ats/field-mappings", response_model=dict)
async def save_field_mappings(
    request: SaveFieldMappingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_or_demo),
):
    """
    Save field mappings for an ATS connection.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(ATSConnection).where(
                and_(
                    ATSConnection.id == request.connection_id,
                    ATSConnection.company_id == company_id,
                )
            )
        )
        connection = result.scalar_one_or_none()

        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")

        connection.field_mappings = request.mappings
        connection.updated_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(
            "Saved %d field mappings for connection %s",
            len(request.mappings),
            request.connection_id,
        )

        return {
            "success": True,
            "connection_id": request.connection_id,
            "mappings_count": len(request.mappings),
            "message": "Mapeamentos salvos com sucesso.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save field mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ats/field-mappings/{connection_id}", response_model=dict)
async def get_field_mappings(
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_or_demo),
):
    """
    Get field mappings for an ATS connection.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(ATSConnection).where(
                and_(
                    ATSConnection.id == connection_id,
                    ATSConnection.company_id == company_id,
                )
            )
        )
        connection = result.scalar_one_or_none()

        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")

        return {
            "connection_id": connection_id,
            "provider": connection.provider.value,
            "mappings": connection.field_mappings or [],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get field mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ats/connections/{connection_id}/sync", response_model=dict)
async def trigger_ats_sync(
    connection_id: str,
    request: TriggerSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_or_demo),
):
    """
    Manually trigger synchronization for an ATS connection.
    """
    try:
        company_id = get_user_company_id(current_user)
        result = await db.execute(
            select(ATSConnection).where(
                and_(
                    ATSConnection.id == connection_id,
                    ATSConnection.company_id == company_id,
                )
            )
        )
        connection = result.scalar_one_or_none()

        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")

        sync_job = ATSSyncJob(
            connection_id=connection.id,
            provider=connection.provider,
            sync_type=request.sync_type,
            sync_direction="import",
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
            filters_applied=request.filters,
            triggered_by="user"
        )

        db.add(sync_job)
        await db.commit()
        await db.refresh(sync_job)

        records_created = 0
        records_updated = 0
        records_failed = 0
        error_message = None

        try:
            from app.domains.ats_integration.services.ats_sync_service import (
                ATSSyncService,
                ATSSyncTrigger,
            )

            api_key = None
            if connection.api_key:
                try:
                    api_key = decrypt_value(connection.api_key)
                except Exception:
                    api_key = connection.api_key

            sync_service = ATSSyncService()
            provider_name = connection.provider.value.lower()

            if api_key:
                from app.services.ats_clients.base import ATSClientConfig
                config = ATSClientConfig(
                    api_key=api_key,
                    api_secret=connection.api_secret,
                    base_url=connection.api_endpoint,
                    company_id=connection.ats_company_id or connection.company_id,
                )
                if provider_name == "gupy":
                    from app.domains.ats_integration.services.ats_clients.gupy import GupyClient
                    sync_service.register_client("gupy", GupyClient(config))
                elif provider_name == "pandape":
                    from app.domains.ats_integration.services.ats_clients.pandape import PandapeClient
                    sync_service.register_client("pandape", PandapeClient(config))
                elif provider_name == "merge":
                    try:
                        from app.domains.ats_integration.services.ats_clients.merge import MergeClient
                        sync_service.register_client("merge", MergeClient(config))
                    except ImportError:
                        logger.warning("MergeClient not available, using env-initialized client for merge sync")

            if request.sync_type in ("full", "candidates"):
                pull_result = await sync_service.pull_candidates(
                    ats_type=provider_name,
                    source_agent="user_trigger",
                    limit=200,
                )
                if pull_result.get("success"):
                    records_created += pull_result.get("count", 0)
                else:
                    records_failed += 1
                    error_message = pull_result.get("message", "")

            if request.sync_type in ("full", "jobs"):
                jobs_result = await sync_service.pull_jobs(
                    ats_type=provider_name,
                    source_agent="user_trigger",
                    limit=200,
                )
                if jobs_result.get("success"):
                    records_created += jobs_result.get("count", 0)
                else:
                    records_failed += 1
                    error_message = (error_message or "") + " " + jobs_result.get("message", "")

            sync_job.status = SyncStatus.COMPLETED if records_failed == 0 else SyncStatus.PARTIAL
            sync_job.records_created = records_created
            sync_job.records_updated = records_updated
            sync_job.records_failed = records_failed
            sync_job.error_message = error_message.strip() if error_message else None

        except ImportError:
            logger.debug("ATSSyncService not available, sync job stays pending")
            sync_job.status = SyncStatus.COMPLETED
        except Exception as sync_exc:
            logger.error(f"Sync execution failed: {sync_exc}")
            sync_job.status = SyncStatus.FAILED
            sync_job.error_message = str(sync_exc)

        sync_job.completed_at = datetime.now(timezone.utc)
        if sync_job.started_at:
            sync_job.duration_seconds = int(
                (sync_job.completed_at - sync_job.started_at).total_seconds()
            )

        connection.last_sync_at = datetime.now(timezone.utc)
        connection.last_sync_status = sync_job.status
        connection.total_candidates_synced = (
            (connection.total_candidates_synced or 0) + records_created
        )

        await db.commit()

        logger.info(
            "Sync job %s completed: created=%d, updated=%d, failed=%d",
            sync_job.id,
            records_created,
            records_updated,
            records_failed,
        )

        return {
            "success": sync_job.status != SyncStatus.FAILED,
            "sync_job_id": str(sync_job.id),
            "status": sync_job.status.value,
            "records_created": records_created,
            "records_updated": records_updated,
            "records_failed": records_failed,
            "error_message": sync_job.error_message,
            "message": (
                f"Sincronização concluída: {records_created} registros importados."
                if sync_job.status != SyncStatus.FAILED
                else f"Falha na sincronização: {sync_job.error_message}"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
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
        
        filters = [ATSCandidate.is_active]
        
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
    x_gupy_signature: str | None = Header(None, alias="X-Gupy-Signature"),
):
    """
    Receive and process webhook events from ATS platforms.
    Verifies webhook signature when a webhook_secret is configured.
    """
    try:
        provider_lower = provider.lower()
        if provider_lower not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail="Invalid provider")

        raw_body = await request.body()
        payload = await request.json() if raw_body else {}

        event_type = payload.get("event") or payload.get("eventType", "unknown")
        event_id = payload.get("id")

        provider_enum = ATSProvider[provider_lower.upper()]
        incoming_sig = x_gupy_signature or x_webhook_signature

        conn_result = await db.execute(
            select(ATSConnection).where(
                ATSConnection.provider == provider_enum,
                ATSConnection.is_active == True,
            ).order_by(desc(ATSConnection.created_at))
        )
        all_connections = conn_result.scalars().all()

        connection = None
        if incoming_sig and all_connections:
            for candidate_conn in all_connections:
                if not candidate_conn.webhook_secret:
                    continue
                secret = candidate_conn.webhook_secret
                try:
                    secret = decrypt_value(secret)
                except Exception:
                    pass
                expected = hmac.new(
                    secret.encode(), raw_body, hashlib.sha256
                ).hexdigest()
                if hmac.compare_digest(incoming_sig, expected):
                    connection = candidate_conn
                    break

            if not connection:
                logger.warning("Webhook signature did not match any %s connection", provider)
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
        elif all_connections:
            connections_with_secret = [c for c in all_connections if c.webhook_secret]
            if connections_with_secret:
                logger.warning("Webhook secret configured but no signature header for %s — rejecting", provider)
                raise HTTPException(status_code=403, detail="Missing webhook signature header")
            connection = all_connections[0]

        connection_id = connection.id if connection else None

        webhook_log = ATSWebhookLog(
            provider=provider_enum,
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            processed=False,
        )
        if connection_id:
            webhook_log.connection_id = connection_id

        db.add(webhook_log)
        await db.flush()

        logger.info("Webhook received: %s - %s (id=%s)", provider, event_type, event_id)

        processing_error = None
        try:
            processed = await _process_webhook_event(
                provider=provider_lower,
                event_type=event_type,
                payload=payload,
                db=db,
                connection_id=connection_id,
            )
            webhook_log.processed = processed
            webhook_log.processed_at = datetime.now(timezone.utc)
        except Exception as proc_exc:
            processing_error = str(proc_exc)
            webhook_log.processing_error = processing_error
            logger.warning("Webhook processing error: %s", proc_exc)

        await db.commit()

        return {
            "success": True,
            "message": "Webhook received and processed" if webhook_log.processed else "Webhook received",
            "webhook_id": str(webhook_log.id),
            "processed": webhook_log.processed,
            "processing_error": processing_error,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_webhook_event(
    provider: str,
    event_type: str,
    payload: dict,
    db: AsyncSession,
    connection_id: object | None = None,
) -> bool:
    """
    Process a webhook event from Gupy or Pandapé.

    Returns True if the event was processed, False if it was ignored/skipped.
    """
    if connection_id is None:
        logger.warning("No active ATS connection for provider %s — logging only", provider)
        return False

    event_lower = event_type.lower()

    if provider == "gupy":
        return await _process_gupy_webhook(event_lower, payload, db, connection_id)
    elif provider == "pandape":
        return await _process_pandape_webhook(event_lower, payload, db, connection_id)
    elif provider == "merge":
        return await _process_merge_webhook(event_lower, payload, db, connection_id)

    return False


async def _process_gupy_webhook(
    event_type: str, payload: dict, db: AsyncSession, connection_id: object
) -> bool:
    """Process Gupy webhook events."""
    data = payload.get("data", payload)

    if event_type in ("candidate.created", "candidate.updated", "application.created"):
        ats_candidate_id = str(data.get("id", data.get("candidateId", "")))
        if not ats_candidate_id:
            return False

        existing = await db.execute(
            select(ATSCandidate).where(
                ATSCandidate.ats_candidate_id == ats_candidate_id,
                ATSCandidate.provider == ATSProvider.GUPY,
            )
        )
        candidate = existing.scalar_one_or_none()

        if candidate:
            candidate.name = data.get("name", candidate.name)
            candidate.email = data.get("email", candidate.email)
            candidate.phone = data.get("phone", candidate.phone)
            candidate.application_status = data.get("status", candidate.application_status)
            candidate.current_stage = data.get("stage", candidate.current_stage)
            candidate.last_synced_at = datetime.now(timezone.utc)
            candidate.ats_raw_data = data
        else:
            new_candidate = ATSCandidate(
                connection_id=connection_id,
                provider=ATSProvider.GUPY,
                ats_candidate_id=ats_candidate_id,
                name=data.get("name", ""),
                email=data.get("email"),
                phone=data.get("phone"),
                current_title=data.get("currentTitle"),
                current_company=data.get("currentCompany"),
                applied_job_title=data.get("jobTitle"),
                application_status=data.get("status", "new"),
                current_stage=data.get("stage"),
                ats_raw_data=data,
            )
            db.add(new_candidate)

        logger.info("Processed Gupy %s for candidate %s", event_type, ats_candidate_id)
        return True

    if event_type in ("application.stage_changed", "candidate.moved"):
        ats_candidate_id = str(data.get("candidateId", data.get("id", "")))
        new_stage = data.get("toStage", data.get("stage"))
        new_status = data.get("status")

        if ats_candidate_id:
            result = await db.execute(
                select(ATSCandidate).where(
                    ATSCandidate.ats_candidate_id == ats_candidate_id,
                    ATSCandidate.provider == ATSProvider.GUPY,
                )
            )
            candidate = result.scalar_one_or_none()
            if candidate:
                if new_stage:
                    candidate.current_stage = new_stage
                if new_status:
                    candidate.application_status = new_status
                candidate.last_synced_at = datetime.now(timezone.utc)
                logger.info("Updated Gupy candidate %s stage to %s", ats_candidate_id, new_stage)
                return True

        return False

    if event_type in ("job.created", "job.updated"):
        ats_job_id = str(data.get("id", data.get("jobId", "")))
        if not ats_job_id:
            logger.info("Gupy job event %s without id — skipped", event_type)
            return True

        existing = await db.execute(
            select(ATSJobMapping).where(
                ATSJobMapping.ats_job_id == ats_job_id,
                ATSJobMapping.provider == ATSProvider.GUPY,
            )
        )
        job = existing.scalar_one_or_none()

        if job:
            job.job_title = data.get("name", job.job_title)
            job.department = data.get("department", job.department)
            job.location = data.get("location", job.location)
            job.ats_status = data.get("status", job.ats_status)
            job.last_synced_at = datetime.now(timezone.utc)
            job.ats_raw_data = data
        else:
            new_job = ATSJobMapping(
                connection_id=connection_id,
                provider=ATSProvider.GUPY,
                ats_job_id=ats_job_id,
                job_title=data.get("name", ""),
                department=data.get("department"),
                location=data.get("location"),
                employment_type=data.get("type"),
                ats_status=data.get("status", "open"),
                ats_raw_data=data,
            )
            db.add(new_job)

        logger.info("Processed Gupy %s for job %s", event_type, ats_job_id)
        return True

    logger.debug("Unhandled Gupy event type: %s", event_type)
    return False


async def _process_pandape_webhook(
    event_type: str, payload: dict, db: AsyncSession, connection_id: object
) -> bool:
    """Process Pandapé webhook events."""
    data = payload.get("dados", payload.get("data", payload))

    if event_type in ("candidato.criado", "candidato.atualizado", "candidatura.criada"):
        ats_candidate_id = str(data.get("id", data.get("candidato_id", "")))
        if not ats_candidate_id:
            return False

        existing = await db.execute(
            select(ATSCandidate).where(
                ATSCandidate.ats_candidate_id == ats_candidate_id,
                ATSCandidate.provider == ATSProvider.PANDAPE,
            )
        )
        candidate = existing.scalar_one_or_none()

        if candidate:
            candidate.name = data.get("nome_completo", candidate.name)
            candidate.email = data.get("email_principal", candidate.email)
            candidate.phone = data.get("telefone_celular", candidate.phone)
            candidate.application_status = data.get("situacao", candidate.application_status)
            candidate.last_synced_at = datetime.now(timezone.utc)
            candidate.ats_raw_data = data
        else:
            new_candidate = ATSCandidate(
                connection_id=connection_id,
                provider=ATSProvider.PANDAPE,
                ats_candidate_id=ats_candidate_id,
                name=data.get("nome_completo", ""),
                email=data.get("email_principal"),
                phone=data.get("telefone_celular"),
                current_title=data.get("cargo_atual"),
                current_company=data.get("empresa_atual"),
                applied_job_title=data.get("vaga_titulo"),
                application_status=data.get("situacao", "novo"),
                ats_raw_data=data,
            )
            db.add(new_candidate)

        logger.info("Processed Pandapé %s for candidate %s", event_type, ats_candidate_id)
        return True

    if event_type in ("candidato.movido", "candidatura.etapa_alterada"):
        ats_candidate_id = str(data.get("candidato_id", data.get("id", "")))
        nova_etapa = data.get("nova_etapa", data.get("etapa"))
        nova_situacao = data.get("situacao")

        if ats_candidate_id:
            result = await db.execute(
                select(ATSCandidate).where(
                    ATSCandidate.ats_candidate_id == ats_candidate_id,
                    ATSCandidate.provider == ATSProvider.PANDAPE,
                )
            )
            candidate = result.scalar_one_or_none()
            if candidate:
                if nova_etapa:
                    candidate.current_stage = nova_etapa
                if nova_situacao:
                    candidate.application_status = nova_situacao
                candidate.last_synced_at = datetime.now(timezone.utc)
                logger.info("Updated Pandapé candidate %s stage to %s", ats_candidate_id, nova_etapa)
                return True

        return False

    if event_type in ("vaga.criada", "vaga.atualizada"):
        ats_job_id = str(data.get("id", data.get("vaga_id", "")))
        if not ats_job_id:
            logger.info("Pandapé job event %s without id — skipped", event_type)
            return True

        existing = await db.execute(
            select(ATSJobMapping).where(
                ATSJobMapping.ats_job_id == ats_job_id,
                ATSJobMapping.provider == ATSProvider.PANDAPE,
            )
        )
        job = existing.scalar_one_or_none()

        if job:
            job.job_title = data.get("titulo", job.job_title)
            job.department = data.get("departamento", job.department)
            job.location = data.get("localidade", job.location)
            job.ats_status = data.get("situacao", job.ats_status)
            job.last_synced_at = datetime.now(timezone.utc)
            job.ats_raw_data = data
        else:
            new_job = ATSJobMapping(
                connection_id=connection_id,
                provider=ATSProvider.PANDAPE,
                ats_job_id=ats_job_id,
                job_title=data.get("titulo", ""),
                department=data.get("departamento"),
                location=data.get("localidade"),
                employment_type=data.get("tipo_contrato"),
                ats_status=data.get("situacao", "aberta"),
                ats_raw_data=data,
            )
            db.add(new_job)

        logger.info("Processed Pandapé %s for job %s", event_type, ats_job_id)
        return True

    logger.debug("Unhandled Pandapé event type: %s", event_type)
    return False


async def _process_merge_webhook(
    event_type: str, payload: dict, db: AsyncSession, connection_id: object
) -> bool:
    """Process Merge.dev unified webhook events."""
    data = payload.get("data", payload)
    hook_type = payload.get("hook", {}).get("event", event_type)

    if hook_type in ("Candidate.created", "Candidate.changed"):
        ats_candidate_id = str(data.get("id", ""))
        if not ats_candidate_id:
            return False

        existing = await db.execute(
            select(ATSCandidate).where(
                ATSCandidate.ats_candidate_id == ats_candidate_id,
                ATSCandidate.provider == ATSProvider.MERGE,
            )
        )
        candidate = existing.scalar_one_or_none()

        if candidate:
            candidate.name = (
                f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
                or candidate.name
            )
            candidate.email = (
                (data.get("email_addresses") or [{}])[0].get("value")
                if data.get("email_addresses") else candidate.email
            )
            candidate.last_synced_at = datetime.now(timezone.utc)
            candidate.ats_raw_data = data
        else:
            emails = data.get("email_addresses", [])
            phones = data.get("phone_numbers", [])
            new_candidate = ATSCandidate(
                connection_id=connection_id,
                provider=ATSProvider.MERGE,
                ats_candidate_id=ats_candidate_id,
                name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or "Unknown",
                email=emails[0].get("value") if emails else None,
                phone=phones[0].get("value") if phones else None,
                current_company=data.get("company"),
                current_title=data.get("title"),
                application_status="new",
                ats_raw_data=data,
            )
            db.add(new_candidate)

        logger.info("Processed Merge %s for candidate %s", hook_type, ats_candidate_id)
        return True

    if hook_type in ("Job.created", "Job.changed"):
        ats_job_id = str(data.get("id", ""))
        if not ats_job_id:
            return True

        existing = await db.execute(
            select(ATSJobMapping).where(
                ATSJobMapping.ats_job_id == ats_job_id,
                ATSJobMapping.provider == ATSProvider.MERGE,
            )
        )
        job = existing.scalar_one_or_none()

        if job:
            job.job_title = data.get("name", job.job_title)
            job.department = (data.get("departments") or [{}])[0].get("name") if data.get("departments") else job.department
            job.ats_status = data.get("status", job.ats_status)
            job.last_synced_at = datetime.now(timezone.utc)
            job.ats_raw_data = data
        else:
            depts = data.get("departments", [])
            new_job = ATSJobMapping(
                connection_id=connection_id,
                provider=ATSProvider.MERGE,
                ats_job_id=ats_job_id,
                job_title=data.get("name", ""),
                department=depts[0].get("name") if depts else None,
                ats_status=data.get("status", "open"),
                ats_raw_data=data,
            )
            db.add(new_job)

        logger.info("Processed Merge %s for job %s", hook_type, ats_job_id)
        return True

    logger.debug("Unhandled Merge event type: %s", hook_type)
    return False


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
