"""
ATS sync event handlers.

Routes:
- POST /handle-trigger/ats-sync
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service as get_activity_service_canonical
from app.shared.compliance.audit_service import AuditService, get_audit_service

from .._shared import (
    ATSSyncRequest,
    ATSSyncResponse,
    get_ats_sync_service,
    map_lia_stage_to_ats,
    notify_unmapped_stage,
    validate_multi_tenancy,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _execute_outbound_ats_sync(ats_sync_service, request, ats_stage: str) -> tuple:
    """Execute outbound ATS sync (LIA -> ATS). Returns (sync_status, ats_response, error)."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncTrigger
    sync_data = {
        "status": ats_stage, "previous_status": request.previous_stage,
        "candidate_name": request.candidate_name, "candidate_email": request.candidate_email,
        "job_title": request.job_title,
    }
    try:
        result = await ats_sync_service.trigger_sync(
            trigger=ATSSyncTrigger.STATUS_CHANGE, source_agent="automation",
            ats_type=request.ats_platform,
            candidate_id=request.ats_candidate_id or request.candidate_id,
            job_id=request.ats_vacancy_id or request.vacancy_id, data=sync_data
        )
        if result.get("success"):
            return "completed", result, None
        return "failed", result, result.get("message", "Sync failed without error message")
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Exception during outbound sync: {e}")
        return "failed", None, str(e)


async def _execute_inbound_ats_sync(ats_sync_service, request) -> tuple:
    """Execute inbound ATS sync (ATS -> LIA). Returns (sync_status, ats_response, error)."""
    try:
        result = await ats_sync_service.pull_candidate(
            ats_type=request.ats_platform,
            ats_candidate_id=request.ats_candidate_id or request.candidate_id,
            source_agent="automation"
        )
        if result.get("success"):
            return "completed", result, None
        return "failed", result, result.get("message", "Pull failed")
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Exception during inbound sync: {e}")
        return "failed", None, str(e)


async def _notify_ats_sync_failure(activity_svc, request, error: str) -> bool:
    """Notify recruiter of ATS sync failure. Returns True if notification created."""
    try:
        candidate_name = request.candidate_name or request.candidate_id
        await activity_svc.create_activity(
            activity_type="ats_sync_failed",
            title=f"Falha na Sincronização com {request.ats_platform.upper()}",
            description=(
                f"Não foi possível sincronizar a mudança de etapa do candidato "
                f"{candidate_name} de '{request.previous_stage or 'N/A'}' para '{request.new_stage}'. "
                f"Erro: {error}"
            ),
            actor_id="system", actor_name="LIA Automation", actor_type="system",
            target_id=request.candidate_id, target_type="candidate",
            extra_data={
                "vacancy_id": request.vacancy_id, "company_id": request.company_id,
                "ats_platform": request.ats_platform, "ats_candidate_id": request.ats_candidate_id,
                "new_stage": request.new_stage, "previous_stage": request.previous_stage, "error": error
            },
            category="ats_sync"
        )
        return True
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Failed to create failure notification: {e}")
        return False


async def _log_ats_sync_audit(db, audit_svc, request, ats_stage: str, is_mapped: bool, sync_status: str, ats_response, error, notification_created: bool) -> None:
    """Log automation execution log and centralized audit for ATS sync."""
    try:
        from app.models.automation import AutomationExecutionLog
from app.shared.errors import LIAError
        db.add(AutomationExecutionLog(
            company_id=request.company_id, trigger_event="ats_sync",
            trigger_data={
                "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
                "ats_platform": request.ats_platform, "ats_candidate_id": request.ats_candidate_id,
                "ats_vacancy_id": request.ats_vacancy_id, "new_stage": request.new_stage,
                "previous_stage": request.previous_stage, "sync_direction": request.sync_direction,
                "ats_stage_mapped": ats_stage, "is_stage_mapped": is_mapped
            },
            candidate_id=request.candidate_id, vacancy_id=request.vacancy_id,
            action_executed=f"ats_sync_{request.sync_direction}_{request.ats_platform}",
            action_result={
                "sync_status": sync_status, "ats_response": ats_response,
                "error": error, "notification_created": notification_created
            },
            status="success" if sync_status == "completed" else "failed",
            execution_time_ms=0
        ))
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Failed to create execution log: {e}")

    try:
        reasoning_items = [
            f"ATS platform: {request.ats_platform}", f"Sync direction: {request.sync_direction}",
            f"Stage transition: {request.previous_stage or 'N/A'} → {request.new_stage}",
            f"Mapped ATS stage: {ats_stage} (explicit_mapping={is_mapped})",
            f"Sync status: {sync_status}"
        ]
        if error:
            reasoning_items.append(f"Error: {error}")
        await audit_svc.log_decision(
            company_id=request.company_id, agent_name="ats_integrator",
            decision_type="ats_sync", action=f"sync_{request.sync_direction}",
            decision=sync_status, score=None,
            confidence=1.0 if sync_status == "completed" else 0.0,
            reasoning=reasoning_items, criteria_used=["ats_platform", "sync_direction", "stage_mapping"],
            candidate_id=request.candidate_id, job_vacancy_id=request.vacancy_id,
            human_review_required=(sync_status == "failed")
        )
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Failed to create centralized audit log: {e}")


def _build_ats_sync_response(request, ats_stage: str, sync_status: str, ats_response, error) -> dict:
    """Build the response dict for ats_sync trigger."""
    return {
        "success": sync_status == "completed",
        "trigger": "ats_sync",
        "ats_platform": request.ats_platform,
        "sync_status": sync_status,
        "sync_direction": request.sync_direction,
        "stage_mapping": {"lia_stage": request.new_stage, "ats_stage": ats_stage},
        "ats_response": ats_response,
        "error": error,
        "metadata": {
            "candidate_id": request.candidate_id, "vacancy_id": request.vacancy_id,
            "ats_candidate_id": request.ats_candidate_id,
            "ats_vacancy_id": request.ats_vacancy_id,
            "processed_at": datetime.utcnow().isoformat()
        }
    }


async def _run_ats_sync_direction(ats_sync_service, request, ats_stage: str) -> tuple:
    """Dispatch sync by direction. Returns (sync_status, ats_response, error)."""
    if request.sync_direction == "outbound":
        return await _execute_outbound_ats_sync(ats_sync_service, request, ats_stage)
    if request.sync_direction == "inbound":
        return await _execute_inbound_ats_sync(ats_sync_service, request)
    return "pending", None, None


async def _process_ats_sync(request, db, audit_svc, activity_svc) -> dict:
    """Orchestrate ats_sync trigger: validate, map stage, sync, notify on failure, audit."""
    logger.info(
        f"🔄 [ATS_SYNC] Starting: platform={request.ats_platform}, "
        f"candidate={request.candidate_id}, stage={request.previous_stage} → {request.new_stage}"
    )

    is_valid, error_msg = await validate_multi_tenancy(
        db, request.candidate_id, request.vacancy_id, request.company_id
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail=error_msg)

    ats_stage, is_mapped = map_lia_stage_to_ats(request.new_stage, request.ats_platform, request.company_id)
    if not is_mapped:
        await notify_unmapped_stage(
            company_id=request.company_id, lia_stage=request.new_stage,
            ats_platform=request.ats_platform, candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id
        )

    sync_status, ats_response, error = await _run_ats_sync_direction(
        get_ats_sync_service(), request, ats_stage
    )

    notification_created = False
    if sync_status == "failed":
        notification_created = await _notify_ats_sync_failure(activity_svc, request, error or "Unknown error")

    await _log_ats_sync_audit(db, audit_svc, request, ats_stage, is_mapped, sync_status, ats_response, error, notification_created)

    logger.info(f"{'✅' if sync_status == 'completed' else '⚠️'} [ATS_SYNC] Done: status={sync_status}")
    return _build_ats_sync_response(request, ats_stage, sync_status, ats_response, error)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/handle-trigger/ats-sync", response_model=ATSSyncResponse)
async def handle_ats_sync(
    request: ATSSyncRequest,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service_canonical),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Handle ats_sync trigger: sync candidate stage with external ATS platform."""
    try:
        return await _process_ats_sync(request, db, audit_svc, activity_svc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [ATS_SYNC] Error: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")
