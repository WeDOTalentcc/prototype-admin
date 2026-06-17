"""
Orchestrated Talent Chat API — delegates to MainOrchestrator (consolidated entry-point).

v4.0: Unified pipeline via MainOrchestrator.process() + ContextAdapter.from_talent_chat().
      FairnessGuard, PendingAction, ActionExecutor, CascadedRouter all handled centrally.
"""
import logging
from app.shared.errors import LIAInternalError
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.orchestrator_routes import get_main_orchestrator
from app.dependencies.token_budget import require_token_budget
from app.orchestrator.context.context_adapter import ContextAdapter
from app.orchestrator.execution.main_orchestrator import MainOrchestrator
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class OrchestratedTalentChatRequest(WeDoBaseModel):
    message: str = Field(..., description="User's natural language query")
    candidates: list[dict[str, Any]] = Field(
        default_factory=list, description="List of candidates in current view"
    )
    selected_candidate_ids: list[str] | None = Field(
        None, description="IDs of selected candidates for focused operations"
    )
    search_context: dict[str, Any] | None = Field(
        None, description="Current search context: query, mode, filters, results count"
    )
    target_job: dict[str, Any] | None = Field(
        None, description="Optional job vacancy for matching/scoring context"
    )
    conversation_id: str | None = Field(
        None, description="Optional conversation ID for context continuity"
    )
    user_id: str = Field(default="recruiter", description="User ID for routing")

class OrchestratedTalentChatResponse(BaseModel):
    success: bool
    content: str = Field(..., description="Formatted markdown response")
    agent_used: str = Field(..., description="Primary agent that handled the query")
    agents_consulted: list[str] = Field(default_factory=list)
    intent_detected: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Routing confidence")
    structured_data: dict[str, Any] | None = None
    suggested_prompts: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    conversation_id: str | None = None
    ui_action: str | None = Field(None, description="Frontend action trigger")
    ui_action_params: dict[str, Any] | None = Field(None)
    action_executed: bool = Field(default=False)
    action_result: dict[str, Any] | None = None
    action_type: str | None = None
    needs_confirmation: bool = Field(default=False, description="Whether action awaits user confirmation")
    needs_params: bool = Field(default=False, description="Whether action needs more parameters from user")
    pending_action_id: str | None = Field(None, description="ID for pending multi-turn action")
    execution_plan: dict[str, Any] | None = Field(None, description="Multi-step plan summary if a plan was executed")

@router.post("/talent-chat", response_model=OrchestratedTalentChatResponse)
async def orchestrated_talent_chat(
    request: OrchestratedTalentChatRequest,
    main_orchestrator: MainOrchestrator = Depends(get_main_orchestrator),
    _budget: None = Depends(require_token_budget),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Unified pipeline via MainOrchestrator.process() (v4.0):
      FairnessGuard → PendingAction → ActionExecutor → CascadedRouter → DomainWorkflow
    """
    from app.core.database import get_db as _get_db
    try:
        logger.info(f"[TalentChat] Processing: {request.message[:100]}...")

        ctx = ContextAdapter.from_talent_chat(
            request,
            user_id=request.user_id,
            company_id=company_id or "",
        )

        db = None
        async for _db in _get_db():
            db = _db
            break

        chat_response = await main_orchestrator.process(ctx, db)
        return OrchestratedTalentChatResponse(
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
            execution_plan=getattr(chat_response, "execution_plan", None),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TalentChat] Error: {e}", exc_info=True)
        raise LIAInternalError("Internal server error")

@router.get("/talent-chat/intents", response_model=None)
async def get_talent_chat_intents(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return {
        "intents": [
            {"id": "rankear_candidatos", "description": "Ranking de candidatos", "keywords": ["ranking", "ordenar", "top", "melhores"]},
            {"id": "comparar_candidatos", "description": "Comparar candidatos", "keywords": ["comparar", "compare", "versus", "vs"]},
            {"id": "analisar_perfil", "description": "Analisar perfil", "keywords": ["analisar", "analise", "avaliar", "parecer"]},
            {"id": "buscar_similar", "description": "Buscar perfis similares", "keywords": ["perfil similar", "similar a", "parecido"], "ui_action": "switch_search_mode"},
            {"id": "skills_analysis", "description": "Análise de skills", "keywords": ["skills", "habilidades", "competências"]},
            {"id": "match_vaga", "description": "Match com vaga", "keywords": ["match", "fit", "aderência"]},
            {"id": "analise_pool", "description": "Análise do pool", "keywords": ["pool", "banco", "base de candidatos"]},
            {"id": "contact_candidate", "description": "Contatar candidatos", "keywords": ["email", "contatar", "whatsapp"], "ui_action": "open_communication_modal"},
            {"id": "schedule_interview", "description": "Agendar entrevistas", "keywords": ["agendar", "entrevista"], "ui_action": "open_schedule_modal"},
            {"id": "wsi_screening", "description": "Triagem WSI", "keywords": ["triagem", "screening", "wsi"], "ui_action": "open_screening_modal"},
            {"id": "criar_vaga", "description": "Criar nova vaga", "keywords": ["criar vaga", "nova vaga", "abrir vaga"], "ui_action": "start_job_wizard"},
        ],
        "context": "talent_funnel",
    }
