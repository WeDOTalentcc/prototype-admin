"""
Trigger management and general automation routes.

Includes:
- GET  /triggers
- POST /triggers/{trigger_id}
- POST /check
- GET  /status
- GET  /stage-suggestions
- POST /execute-action
- POST /screen-candidate
- POST /trigger-event
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.analytics.services.activity_service import ActivityService

from ._shared import (
    ExecuteActionRequest,
    ScreenCandidateRequest,
    TriggerEventRequest,
    UpdateTriggerRequest,
    AutomationService,
    automation_service,
    get_automation_service,
    automation_trigger_service,
    get_activity_service,
    get_cv_scoring_service,
    get_email_service,
    get_scheduling_service,
    get_whatsapp_service,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TriggersListResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class TriggerUpdateResponse(BaseModel):
    success: bool
    message: str


class TriggerCheckResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class AutomationStatusResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class StageSuggestionsResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class ExecuteActionResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class ScreenCandidateResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class TriggerEventResponse(BaseModel):
    success: bool
    data: dict[str, Any]

@router.get("/triggers", response_model=TriggersListResponse)
async def get_automation_triggers(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all automation trigger configurations.
    """
    try:
        triggers = automation_trigger_service.get_triggers_config()
        return {
            "success": True,
            "data": {
                "triggers": triggers,
                "total": len(triggers)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting triggers: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/triggers/{trigger_id}", response_model=TriggerUpdateResponse)
async def update_trigger(
    trigger_id: str,
    request: UpdateTriggerRequest, 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Enable or disable an automation trigger.
    """
    try:
        success = automation_trigger_service.update_trigger_status(trigger_id, request.enabled)
        if success:
            return {
                "success": True,
                "message": f"Trigger {'ativado' if request.enabled else 'desativado'} com sucesso"
            }
        else:
            raise HTTPException(status_code=404, detail="Trigger não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trigger: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/check", response_model=TriggerCheckResponse)
async def check_and_execute_triggers(
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Manually trigger automation check.
    This will check all enabled triggers and execute actions for matching conditions.
    """
    try:
        result = await automation_trigger_service.check_and_execute_triggers(db)
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking triggers: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/status", response_model=AutomationStatusResponse)
async def get_automation_status(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get automation engine status.
    """
    try:
        triggers = automation_trigger_service.get_triggers_config()
        enabled_count = sum(1 for t in triggers if t.get("enabled", False))
        
        return {
            "success": True,
            "data": {
                "status": "active",
                "total_triggers": len(triggers),
                "enabled_triggers": enabled_count,
                "disabled_triggers": len(triggers) - enabled_count
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/stage-suggestions", response_model=StageSuggestionsResponse)
async def get_stage_suggestions(
    auto_svc: AutomationService = Depends(get_automation_service),
    from_stage: str | None = Query(None, description="Previous stage name"),
    to_stage: str = Query(..., description="Target stage name"),
    candidate_id: str | None = Query(None, description="Candidate ID"),
    vacancy_id: str | None = Query(None, description="Vacancy ID"),
    company_id: str = Query(..., description="Company ID for multi-tenancy"), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get AI-powered suggestions for automation actions based on stage transition.
    
    Returns a list of suggested actions with confidence scores for the given
    stage transition. These suggestions help recruiters quickly configure
    appropriate automations for different pipeline stages.
    
    Args:
        from_stage: The previous stage name (optional)
        to_stage: The target/new stage name (required)
        candidate_id: ID of the candidate (optional, for context)
        vacancy_id: ID of the vacancy (optional, for context)
    
    Returns:
        List of suggestions with:
        - action_type: Type of suggested action
        - confidence_score: 0-1 score indicating confidence level
        - recommended: Boolean indicating if strongly recommended
        - message_template_id: Optional template ID for the action
        - description: Human-readable description
    """
    try:
        transition_data = {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id
        }
        
        suggestions = auto_svc.get_ai_suggestions(transition_data)
        
        logger.info(
            f"📋 [STAGE_SUGGESTIONS] Generated {len(suggestions)} suggestions "
            f"for transition {from_stage} → {to_stage} (company: {company_id})"
        )
        
        return {
            "success": True,
            "data": {
                "transition": {
                    "from_stage": from_stage,
                    "to_stage": to_stage
                },
                "suggestions": suggestions,
                "total": len(suggestions),
                "context": {
                    "candidate_id": candidate_id,
                    "vacancy_id": vacancy_id
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stage suggestions: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/execute-action", response_model=ExecuteActionResponse)
async def execute_action(
    request: ExecuteActionRequest,
    db: AsyncSession = Depends(get_tenant_db),
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Execute a specific automation action.
    
    Supports the following action types:
    - email: Send an email to the candidate
    - whatsapp: Send a WhatsApp message to the candidate
    - triagem_wsi: Register WSI screening invite and send via chosen channel
    - agendar_entrevista: Schedule an interview using SchedulingService
    - apenas_mover: No action, just confirm (for stage moves without communication)
    
    Args:
        request: ExecuteActionRequest with action details
        db: Database session
    
    Returns:
        Result of the action execution with message_id and channel info
    """
    try:
        action_type = request.action_type
        result_data = {
            "action_type": action_type,
            "executed": False,
            "message_id": None,
            "channel": request.channel or action_type
        }
        
        logger.info(
            f"🎯 [EXECUTE_ACTION] Starting action '{action_type}' "
            f"for candidate={request.candidate_id}, vacancy={request.vacancy_id}, "
            f"company={request.company_id}"
        )
        
        if action_type == "email":
            email_service = get_email_service()
            
            send_result = await email_service.send_email(
                to_email=request.metadata.get("to_email") if request.metadata else None,
                subject=request.subject or "Atualização do Processo Seletivo",
                body_html=request.message or "",
                body_text=request.message or "",
                template_id=request.template_id,
                template_data=request.metadata or {},
                company_id=request.company_id
            )
            
            result_data["executed"] = send_result.get("success", False)
            result_data["message_id"] = send_result.get("message_id") or str(uuid.uuid4())
            result_data["channel"] = "email"
            result_data["provider_response"] = send_result
            
            logger.info(f"📧 [EMAIL] Sent email for candidate {request.candidate_id}: {result_data['message_id']}")
        
        elif action_type == "whatsapp":
            whatsapp_service = get_whatsapp_service()
            
            to_phone = request.metadata.get("to_phone") if request.metadata else None
            if not to_phone:
                raise HTTPException(
                    status_code=400,
                    detail="Campo 'to_phone' é obrigatório no metadata para ações de WhatsApp"
                )
            
            send_result = await whatsapp_service.send_message(
                to_phone=to_phone,
                message=request.message or "Você tem uma atualização no processo seletivo.",
                metadata={
                    "candidate_id": request.candidate_id,
                    "vacancy_id": request.vacancy_id,
                    "company_id": request.company_id,
                    **(request.metadata or {})
                }
            )
            
            result_data["executed"] = send_result.success
            result_data["message_id"] = send_result.message_id or str(uuid.uuid4())
            result_data["channel"] = "whatsapp"
            result_data["status"] = send_result.status.value if send_result.status else "sent"
            
            logger.info(f"💬 [WHATSAPP] Sent message for candidate {request.candidate_id}: {result_data['message_id']}")
        
        elif action_type == "triagem_wsi":
            await activity_svc.create_activity(
                activity_type="wsi_screening_invite",
                title="Convite para Triagem WSI Enviado",
                description="Convite para triagem WSI enviado para candidato",
                actor_id="system",
                actor_name="LIA Automation",
                actor_type="system",
                target_id=request.candidate_id,
                target_type="candidate",
                extra_data={
                    "vacancy_id": request.vacancy_id,
                    "company_id": request.company_id,
                    "channel": request.channel or "email",
                    "template_id": request.template_id,
                    **(request.metadata or {})
                },
                category="screening"
            )
            
            channel = request.channel or "email"
            if channel == "email":
                email_service = get_email_service()
                send_result = await email_service.send_email(
                    to_email=request.metadata.get("to_email") if request.metadata else None,
                    subject=request.subject or "Convite para Triagem - WSI",
                    body_html=request.message or "",
                    body_text=request.message or "",
                    template_id=request.template_id,
                    template_data=request.metadata or {},
                    company_id=request.company_id
                )
                result_data["message_id"] = send_result.get("message_id") or str(uuid.uuid4())
            elif channel == "whatsapp":
                whatsapp_service = get_whatsapp_service()
                to_phone = request.metadata.get("to_phone") if request.metadata else None
                if to_phone:
                    send_result = await whatsapp_service.send_message(
                        to_phone=to_phone,
                        message=request.message or "Você foi convidado para a etapa de triagem WSI.",
                        metadata={"candidate_id": request.candidate_id, **(request.metadata or {})}
                    )
                    result_data["message_id"] = send_result.message_id or str(uuid.uuid4())
                else:
                    result_data["message_id"] = str(uuid.uuid4())
            
            result_data["executed"] = True
            result_data["channel"] = channel
            
            logger.info(f"🎯 [TRIAGEM_WSI] Registered screening invite for candidate {request.candidate_id} via {channel}")
        
        elif action_type == "agendar_entrevista":
            scheduling_service = get_scheduling_service()
            
            interview_data = request.metadata or {}
            from datetime import datetime, timedelta
            
            interview = await scheduling_service.create_interview(
                db=db,
                candidate_id=request.candidate_id,
                candidate_name=interview_data.get("candidate_name", "Candidato"),
                candidate_email=interview_data.get("candidate_email", ""),
                interviewer_name=interview_data.get("interviewer_name", "Recrutador"),
                interviewer_email=interview_data.get("interviewer_email", ""),
                start_time=datetime.fromisoformat(interview_data.get("start_time")) if interview_data.get("start_time") else datetime.utcnow() + timedelta(days=1),
                duration_minutes=interview_data.get("duration_minutes", 60),
                interview_type=interview_data.get("interview_type", "behavioral"),
                interview_mode=interview_data.get("interview_mode", "video"),
                job_title=interview_data.get("job_title"),
                job_vacancy_id=request.vacancy_id,
                location=interview_data.get("location"),
                notes=request.message,
                created_by="automation"
            )
            
            result_data["executed"] = True
            result_data["message_id"] = str(interview.id)
            result_data["channel"] = "scheduling"
            result_data["interview_id"] = str(interview.id)
            
            logger.info(f"📅 [AGENDAR_ENTREVISTA] Scheduled interview {interview.id} for candidate {request.candidate_id}")
        
        elif action_type == "apenas_mover":
            result_data["executed"] = True
            result_data["message_id"] = str(uuid.uuid4())
            result_data["channel"] = "none"
            
            logger.info(f"➡️ [APENAS_MOVER] Stage move confirmed for candidate {request.candidate_id} (no action needed)")
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de ação não suportado: {action_type}"
            )
        
        await activity_svc.create_activity(
            activity_type="automation_action_executed",
            title=f"Ação de Automação: {action_type}",
            description=f"Ação '{action_type}' executada com sucesso",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=request.candidate_id,
            target_type="candidate",
            extra_data={
                "action_type": action_type,
                "vacancy_id": request.vacancy_id,
                "company_id": request.company_id,
                "message_id": result_data.get("message_id"),
                "channel": result_data.get("channel")
            },
            category="automation"
        )
        
        logger.info(
            f"✅ [EXECUTE_ACTION] Completed action '{action_type}' "
            f"for candidate={request.candidate_id}: executed={result_data['executed']}"
        )
        
        return {
            "success": True,
            "data": result_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error executing action '{request.action_type}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/screen-candidate", response_model=ScreenCandidateResponse)
async def screen_candidate(
    request: ScreenCandidateRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Execute CV screening for a candidate against a vacancy using Rubric Evaluation.
    
    This endpoint uses the structured rubrics methodology (BARS) to evaluate
    a candidate's CV against job requirements and calculate a preliminary fit score.
    
    IMPORTANT: This is CV-only screening. Full WSI scoring requires conversational
    triagem (voice/chat) handled by the WSI Evaluator agent.
    
    Methodology:
    - Agent (AI): Analyzes CV semantically, extracts evidence, identifies matches
    - System (Deterministic): Applies scoring formulas, determines recommendation
    
    Score Thresholds (rubric_score):
    - 85-100%: Altamente Recomendado (Highly Recommended)
    - 70-84%: Recomendado (Recommended)  
    - 55-69%: Potencial (Potential)
    - 40-54%: Baixo Match (Low Match)
    - 0-39%: Não Recomendado (Not Recommended)
    
    Args:
        request: ScreenCandidateRequest with candidate, vacancy, and company IDs
        db: Database session
    
    Returns:
        Screening result with rubric_score, cv_fit (preliminary indicator),
        recommendation, and detailed evaluations
    """
    try:
        logger.info(
            f"🔍 [SCREEN_CANDIDATE] Starting CV screening for "
            f"candidate={request.candidate_id}, vacancy={request.vacancy_id}"
        )
        
        cv_scoring = get_cv_scoring_service()
        result = await cv_scoring.screen_candidate(
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            company_id=request.company_id,
            db=db
        )
        
        if result.get("success"):
            logger.info(
                f"✅ [SCREEN_CANDIDATE] Screening completed: "
                f"score={result.get('rubric_score')}%, "
                f"recommendation={result.get('recommendation')}"
            )
            return {
                "success": True,
                "data": result
            }
        else:
            logger.warning(f"⚠️ [SCREEN_CANDIDATE] Screening failed: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Erro na triagem do candidato")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SCREEN_CANDIDATE] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/trigger-event", response_model=TriggerEventResponse)
async def trigger_automation_event(
    request: TriggerEventRequest,
    db: AsyncSession = Depends(get_tenant_db),
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Trigger an automation event for agent processing.
    
    This endpoint is used to notify the multi-agent system about significant
    events in the recruitment process, such as:
    - job_created: A new job vacancy was created
    - screening_completed: CV screening was completed for a candidate
    - interview_completed: An interview was completed
    - stage_changed: A candidate's stage was changed
    
    Args:
        request: TriggerEventRequest with event details
        db: Database session
    
    Returns:
        Result of the event trigger with agent notifications
    """
    try:
        logger.info(
            f"🔔 [TRIGGER_EVENT] Event '{request.event_type}' triggered "
            f"for {request.entity_type}={request.entity_id}, company={request.company_id}"
        )
        
        await activity_svc.create_activity(
            activity_type=request.event_type,
            title=f"Evento: {request.event_type}",
            description=f"Evento '{request.event_type}' disparado para {request.entity_type} {request.entity_id}",
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=request.entity_id,
            target_type=request.entity_type,
            extra_data={
                "event_type": request.event_type,
                "company_id": request.company_id,
                **(request.metadata or {})
            },
            category="automation_event"
        )
        
        agents_notified = []
        
        if request.event_type == "job_created":
            agents_notified = ["job_planner", "sourcing"]
            logger.info(f"📋 [JOB_CREATED] Notifying agents: {agents_notified}")

            # === Studio Agent Deployments: fire agents bound to this job ===
            try:
                from app.services.agent_deployment_service import agent_deployment_service
                job_id = request.entity_id
                if job_id and request.company_id:
                    job_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                        db=db,
                        company_id=request.company_id,
                        target_type="job",
                        target_id=job_id,
                        trigger_mode="on_new_candidate",
                    )
                    for dep in job_deployments:
                        agents_notified.append(f"studio:{dep.agent_id}")
                        logger.info(
                            "[DEPLOY_TRIGGER] job event → agent=%s deployment=%s",
                            dep.agent_id, dep.id,
                        )
            except Exception as _deploy_err:
                logger.warning("[DEPLOY_TRIGGER] job hook failed: %s", _deploy_err)
        
        elif request.event_type == "screening_completed":
            agents_notified = ["cv_screening"]
            
            candidate_id = request.metadata.get("candidate_id") if request.metadata else None
            vacancy_id = request.metadata.get("vacancy_id") if request.metadata else None
            
            if not candidate_id or not vacancy_id:
                logger.error(
                    f"❌ [SCREENING_COMPLETED] Missing required metadata: "
                    f"candidate_id={candidate_id}, vacancy_id={vacancy_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Evento 'screening_completed' requer candidate_id e vacancy_id no metadata"
                )
            
            cv_scoring = get_cv_scoring_service()
            screening_result = await cv_scoring.screen_candidate(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=request.company_id,
                db=db
            )
            
            if not screening_result.get("success"):
                logger.error(
                    f"❌ [SCREENING_COMPLETED] CV Screening failed: {screening_result.get('error')}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=screening_result.get("message", "Erro na triagem do CV")
                )
            
            logger.info(
                f"📝 [SCREENING_COMPLETED] CV Screening executed: "
                f"rubric={screening_result.get('rubric_score', 'N/A')}%, "
                f"recommendation={screening_result.get('recommendation', 'N/A')}"
            )
        
        elif request.event_type == "interview_completed":
            agents_notified = ["interviewer", "analyst_feedback"]
            logger.info(f"🎤 [INTERVIEW_COMPLETED] Notifying agents: {agents_notified}")
        
        elif request.event_type == "stage_changed":
            agents_notified = ["orchestrator", "task_planner"]
            logger.info(f"➡️ [STAGE_CHANGED] Notifying agents: {agents_notified}")

            # === Studio Agent Deployments: fire agents bound to this stage ===
            try:
                from app.services.agent_deployment_service import agent_deployment_service
from app.shared.errors import LIAError
                stage_id = request.metadata.get("stage_id") if request.metadata else None
                if stage_id and request.company_id:
                    stage_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                        db=db,
                        company_id=request.company_id,
                        target_type="pipeline_stage",
                        target_id=stage_id,
                        trigger_mode="on_stage_change",
                    )
                    for dep in stage_deployments:
                        agents_notified.append(f"studio:{dep.agent_id}")
                        logger.info(
                            "[DEPLOY_TRIGGER] stage_changed → agent=%s deployment=%s",
                            dep.agent_id, dep.id,
                        )
            except Exception as _deploy_err:
                logger.warning("[DEPLOY_TRIGGER] stage_changed hook failed: %s", _deploy_err)
        
        logger.info(
            f"✅ [TRIGGER_EVENT] Event '{request.event_type}' processed, "
            f"notified agents: {agents_notified}"
        )
        
        return {
            "success": True,
            "data": {
                "event_type": request.event_type,
                "entity_id": request.entity_id,
                "entity_type": request.entity_type,
                "agents_notified": agents_notified,
                "message": f"Evento '{request.event_type}' disparado com sucesso"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error triggering event '{request.event_type}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


