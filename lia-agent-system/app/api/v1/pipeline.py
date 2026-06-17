
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.recruiter_assistant.services.pipeline_service import pipeline_service
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.pii_masking import get_masked_logger
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.errors import LIAError

logger = get_masked_logger(__name__)

router = APIRouter()


class PipelineActionRequest(WeDoBaseModel):
    candidate_id: str
    action_id: str


@router.get("/stale-candidates", response_model=None)
async def get_stale_candidates(
    stale_days: int = Query(default=3, ge=1, le=30, description="Days of inactivity to consider stale"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum candidates to return"),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get candidates that have been inactive for X days.
    
    Returns candidates grouped by job vacancy with suggested actions.
    """
    try:
        # Onda 4.2b-P0-2 (2026-05-23): company_id obrigatorio cross-tenant.
        result = await pipeline_service.get_stale_candidates(
            db=db,
            stale_days=stale_days,
            limit=limit,
            company_id=company_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stale candidates: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/action", response_model=None)
async def execute_pipeline_action(
    request: PipelineActionRequest,
    db: AsyncSession = Depends(get_db),
    audit_svc: AuditService = Depends(get_audit_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Execute a pipeline action on a candidate.
    
    Actions include: start_screening, schedule_interview, add_feedback,
    advance_stage, send_offer, confirm_hire, reject_candidate, etc.
    """
    try:
        # Onda 4.2b-P0-1 (2026-05-23): company_id obrigatorio cross-tenant.
        result = await pipeline_service.execute_pipeline_action(
            candidate_id=request.candidate_id,
            action_id=request.action_id,
            db=db,
            company_id=company_id,
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))

        try:
            _is_gate_action = request.action_id in ("advance_stage", "reject_candidate", "send_offer", "confirm_hire")
            await audit_svc.log_decision(
                # Onda 4.2b-P1-7 (2026-05-23): audit trail tem company_id real.
                company_id=company_id,
                agent_name="pipeline_module",
                decision_type="move_stage",
                action=request.action_id,
                decision="executed",
                reasoning=[
                    f"Pipeline action '{request.action_id}' executed",
                    f"Result: {result.get('status', 'ok')}",
                    f"Gate decision: {_is_gate_action}",
                ],
                criteria_used=["action_id", "candidate_status", "pipeline_rules", "gate_policy"],
                candidate_id=request.candidate_id,
                human_review_required=_is_gate_action,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for pipeline_action: {audit_err}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing pipeline action: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")
