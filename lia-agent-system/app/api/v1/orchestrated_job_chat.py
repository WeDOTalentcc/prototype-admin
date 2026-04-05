"""
Orchestrated Job Chat API — delegates to MainOrchestrator (consolidated entry-point).

v3.0: Unified pipeline via MainOrchestrator.process() + ContextAdapter.from_job_chat().
      FairnessGuard, PendingAction, ActionExecutor, CascadedRouter all handled centrally.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies.token_budget import require_token_budget
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uuid

from app.domains.job_management.services.job_context_service import job_context_service, EnrichedJobContext
from app.api.orchestrator_routes import get_main_orchestrator
from app.orchestrator.context_adapter import ContextAdapter
from app.orchestrator.main_orchestrator import MainOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

class OrchestratedJobChatRequest(BaseModel):
    """Request for orchestrated job chat."""
    message: str = Field(..., description="User's natural language query")
    job_context: Dict[str, Any] = Field(
        ..., 
        description="Job vacancy context: title, department, level, requirements, skills, etc."
    )
    candidates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of candidates in the pipeline with their data"
    )
    selected_candidate_ids: Optional[List[str]] = Field(
        None,
        description="IDs of selected candidates for focused operations"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID for context continuity"
    )
    user_id: str = Field(default="recruiter", description="User ID for routing")
    company_id: str = Field(default="", description="Tenant company ID for multi-tenancy isolation")

class OrchestratedJobChatResponse(BaseModel):
    """Response from orchestrated job chat."""
    success: bool
    content: str = Field(..., description="Formatted markdown response")
    agent_used: str = Field(..., description="Primary agent that handled the query")
    agents_consulted: List[str] = Field(default_factory=list, description="All agents consulted")
    intent_detected: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Routing confidence")
    structured_data: Optional[Dict[str, Any]] = None
    suggested_prompts: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested UI actions")
    conversation_id: Optional[str] = None
    ui_action: Optional[str] = Field(None, description="Frontend action trigger (fallback)")
    ui_action_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for UI action (fallback)")
    action_executed: bool = Field(default=False, description="Whether a real action was executed via closed-loop")
    action_result: Optional[Dict[str, Any]] = Field(None, description="Result data of executed action")
    action_type: Optional[str] = Field(None, description="Type of action executed (move_candidate, send_email, etc.)")
    needs_confirmation: bool = Field(default=False, description="Whether action awaits user confirmation")
    needs_params: bool = Field(default=False, description="Whether action needs more parameters from user")
    pending_action_id: Optional[str] = Field(None, description="ID for pending multi-turn action")

INTENT_TO_UI_ACTION: Dict[str, str] = {
    "mover_candidato": "move_candidate",
    "atualizar_status_candidato": "move_candidate",
    "update_candidate_status": "move_candidate",
    "reprovar_candidato": "move_candidate",
    
    "aprovar_candidato": "approve_candidate",
    
    "enviar_email": "send_email",
    "enviar_mensagem": "send_email",
    "send_email": "send_email",
    
    "disparar_triagem": "start_screening",
    "iniciar_triagem": "start_screening",
    "start_screening": "start_screening",
    "cv_screening": "start_screening",
    "triagem_curricular": "start_screening",
    
    "agendar_entrevista": "schedule_interview",
    "schedule_interview": "schedule_interview",
    "scheduling": "schedule_interview",
    "reagendar_entrevista": "schedule_interview",
    
    "solicitar_dados": "request_data",
    "pedir_documentos": "request_data",
    "request_data": "request_data",
    
    "analisar_perfil": "analyze_profile",
    "analise_detalhada": "analyze_profile",
    "analyze_profile": "analyze_profile",
    
    "create_job_vacancy": "start_job_wizard",
    "create_job": "start_job_wizard",
}

@router.post("/orchestrator/job-chat", response_model=OrchestratedJobChatResponse)
async def orchestrated_job_chat(
    request: OrchestratedJobChatRequest,
    main_orchestrator: MainOrchestrator = Depends(get_main_orchestrator),
    _budget: None = Depends(require_token_budget),
) -> OrchestratedJobChatResponse:
    """
    Unified pipeline via MainOrchestrator.process() (v3.0):
      FairnessGuard → PendingAction → ActionExecutor → CascadedRouter → DomainWorkflow
    """
    from app.core.database import get_db as _get_db

    if not request.message:
        raise HTTPException(status_code=400, detail="Message is required")
    if not request.job_context:
        raise HTTPException(status_code=400, detail="Job context is required")

    try:
        logger.info(f"[JobChat] Processing: {request.message[:100]}...")

        ctx = ContextAdapter.from_job_chat(
            request,
            user_id=request.user_id,
            company_id=request.company_id or "",
        )

        db = None
        async for _db in _get_db():
            db = _db
            break

        chat_response = await main_orchestrator.process(ctx, db)
        return OrchestratedJobChatResponse(
            success=chat_response.success,
            content=chat_response.content,
            agent_used=chat_response.agent_used,
            agents_consulted=chat_response.agents_consulted,
            intent_detected=chat_response.intent_detected,
            confidence=chat_response.confidence,
            structured_data=chat_response.structured_data,
            suggested_prompts=chat_response.suggested_prompts,
            actions=chat_response.actions,
            conversation_id=chat_response.conversation_id,
            ui_action=chat_response.ui_action,
            ui_action_params=chat_response.ui_action_params,
            action_executed=chat_response.action_executed,
            action_result=chat_response.action_result,
            action_type=chat_response.action_type,
            needs_confirmation=chat_response.needs_confirmation,
            needs_params=chat_response.needs_params,
            pending_action_id=chat_response.pending_action_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[JobChat] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing job chat: {str(e)}"
        )

@router.get("/orchestrator/job-chat/intents")
async def get_job_chat_intents():
    """Get available intents and agent mappings for job chat."""
    return {
        "intents": [
            {
                "id": "criar_vaga",
                "description": "Criar uma nova vaga de recrutamento",
                "keywords": ["criar vaga", "nova vaga", "abrir vaga", "nova posição"],
                "agent": "JobPlanner",
                "ui_action": "start_job_wizard"
            },
            {
                "id": "ranking_candidatos",
                "description": "Ranking de candidatos por fit com a vaga",
                "keywords": ["melhores", "ranking", "top", "ordenar"],
                "agent": "AvaliadorWSI"
            },
            {
                "id": "analise_funil",
                "description": "Análise de métricas do funil de recrutamento",
                "keywords": ["funil", "pipeline", "métricas", "conversão"],
                "agent": "AnalistaFeedback"
            },
            {
                "id": "gargalos",
                "description": "Identificação de gargalos no processo",
                "keywords": ["gargalo", "problema", "travado", "parado"],
                "agent": "AnalistaFeedback"
            },
            {
                "id": "comparar_candidatos",
                "description": "Comparação detalhada entre candidatos",
                "keywords": ["comparar", "versus", "diferenças"],
                "agent": "AvaliadorWSI"
            },
            {
                "id": "candidatos_feedback",
                "description": "Candidatos que precisam de feedback",
                "keywords": ["feedback", "devolutiva", "retorno"],
                "agent": "AnalistaFeedback"
            },
            {
                "id": "perfil_candidato",
                "description": "Análise detalhada de perfil",
                "keywords": ["perfil", "resumo", "detalhes"],
                "agent": "TriagemCurricular"
            },
            {
                "id": "proximos_passos",
                "description": "Recomendações de próximos passos",
                "keywords": ["próximos passos", "sugestão", "recomendação"],
                "agent": "RecruiterAssistant"
            },
            {
                "id": "mover_candidato",
                "description": "Mover candidato para outra etapa do pipeline",
                "keywords": ["mover", "avançar", "mudar etapa", "aprovar", "reprovar", "rejeitar", "transferir"],
                "agent": "RecruiterAssistant",
                "ui_action": "move_candidate"
            }
        ]
    }
