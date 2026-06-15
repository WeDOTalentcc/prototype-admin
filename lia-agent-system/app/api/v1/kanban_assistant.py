"""
LIA Kanban Assistant API endpoints.
Provides AI-powered analysis for recruitment pipelines.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from app.domains.recruiter_assistant.services.kanban_assistant_service import kanban_assistant_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class KanbanAssistantRequest(WeDoBaseModel):
    """Request model for Kanban Assistant."""
    command: str = Field(..., description="User's natural language command")
    command_type: str | None = Field(None, description="Pre-detected command type (rankear, funil, etc.)")
    job_context: dict[str, Any] = Field(
        ..., 
        description="Job vacancy context: title, department, level, requirements, skills, etc."
    )
    candidates: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of candidates in the pipeline with their data"
    )
    selected_candidate_ids: list[str] | None = Field(
        None,
        description="IDs of selected candidates for comparison operations"
    )


class KanbanAssistantResponse(BaseModel):
    """Response model for Kanban Assistant."""
    success: bool = Field(..., description="Whether the request was successful")
    response_type: str = Field(..., description="Type of analysis performed")
    content: str = Field(..., description="Formatted markdown response")
    structured_data: dict[str, Any] | None = Field(
        None,
        description="Structured data from the analysis (ranking, metrics, etc.)"
    )
    suggested_actions: list[str] = Field(
        default_factory=list,
        description="List of suggested next actions"
    )
    follow_up_prompts: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )
    ui_action: str | None = Field(None, description="Frontend action trigger")
    ui_action_params: dict[str, Any] | None = Field(None, description="Parameters for UI action")


@router.post("/lia/kanban-assistant", response_model=KanbanAssistantResponse)
async def kanban_assistant(request: KanbanAssistantRequest, company_id: str = Depends(require_company_id)) -> KanbanAssistantResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Process a Kanban assistant command for AI-powered pipeline analysis.
    
    Supports various analysis types:
    - **rankear_candidatos**: Rank candidates by job fit
    - **performance_funil**: Analyze pipeline metrics
    - **gargalos_processo**: Identify bottlenecks
    - **comparar_candidatos**: Compare selected candidates
    - **resumir_perfil**: Executive summary of a candidate
    - **candidatos_ativos**: Active candidates by stage
    - **taxa_conversao**: Conversion rates analysis
    - **tempo_medio**: Average time analysis
    - **candidatos_parados**: Stalled candidates
    - **top_candidatos**: Top candidates by LIA score
    - **analise_geral**: General analysis based on query
    
    Returns structured analysis with markdown content and actionable insights.
    """
    if not request.command:
        raise HTTPException(status_code=400, detail="Command is required")
    
    if not request.job_context:
        raise HTTPException(status_code=400, detail="Job context is required")
    
    try:
        logger.info(f"Processing Kanban assistant command: {request.command[:100]}...")
        
        result = await kanban_assistant_service.process_command(
            command=request.command,
            command_type=request.command_type,
            job_context=request.job_context,
            candidates=request.candidates,
            selected_candidate_ids=request.selected_candidate_ids
        )
        
        logger.info(f"Kanban assistant response type: {result.get('response_type')}")
        
        return KanbanAssistantResponse(
            success=result.get("success", True),
            response_type=result.get("response_type", "analise_geral"),
            content=result.get("content", ""),
            structured_data=result.get("structured_data"),
            suggested_actions=result.get("suggested_actions", []),
            follow_up_prompts=result.get("follow_up_prompts", []),
            ui_action=result.get("ui_action"),
            ui_action_params=result.get("ui_action_params")
        )
        
    except ValueError as e:
        logger.error(f"Configuration error in Kanban assistant: {e}")
        raise HTTPException(status_code=503, detail=f"AI service not configured: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kanban assistant failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


class StageMoveContext(BaseModel):
    """# T-06 R2 fix canonical: StageMoveContext company_id field removed.

    Multi-tenancy via Depends(require_company_id) in get_stage_move_suggestions.
    """
    model_config = ConfigDict(extra='forbid')

    candidate_id: str = Field(..., description="ID do candidato sendo movido")
    candidate_name: str | None = Field(None, description="Nome do candidato")
    from_stage: str = Field(..., description="Etapa de origem")
    to_stage: str = Field(..., description="Etapa de destino")
    job_title: str | None = Field(None, description="Título da vaga")


class StageMovesuggestion(BaseModel):
    type: str
    content: str
    confidence: float


class StageMoveSuggestionsResponse(BaseModel):
    suggestions: list[StageMovesuggestion]
    generated_at: str


@router.post("/lia/kanban-assistant/stage-move-suggestions", response_model=StageMoveSuggestionsResponse)
async def get_stage_move_suggestions(context: StageMoveContext, company_id: str = Depends(require_company_id)) -> StageMoveSuggestionsResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Return contextual LIA suggestions when a candidate is moved to a new stage.

    Provides substatus suggestions and recommended next actions based on the
    from/to stage combination and any available candidate context.
    """
    from datetime import datetime

    stage_suggestions: dict[str, list[dict]] = {
        "applied": [
            {"type": "substatus", "content": "Aguardando análise de currículo", "confidence": 0.90},
            {"type": "next_action", "content": "Iniciar triagem curricular", "confidence": 0.85},
        ],
        "screening": [
            {"type": "substatus", "content": "Em triagem pela LIA", "confidence": 0.92},
            {"type": "next_action", "content": "Aguardar resultado da triagem automática", "confidence": 0.88},
            {"type": "substatus", "content": "Aguardando revisão manual", "confidence": 0.75},
        ],
        "interview": [
            {"type": "substatus", "content": "Aguardando agendamento de entrevista", "confidence": 0.90},
            {"type": "next_action", "content": "Agendar entrevista com o candidato", "confidence": 0.88},
            {"type": "substatus", "content": "Entrevista agendada", "confidence": 0.80},
        ],
        "technical": [
            {"type": "substatus", "content": "Aguardando envio do teste técnico", "confidence": 0.88},
            {"type": "next_action", "content": "Enviar teste técnico por email", "confidence": 0.85},
            {"type": "substatus", "content": "Teste técnico enviado — aguardando resposta", "confidence": 0.80},
        ],
        "offer": [
            {"type": "substatus", "content": "Proposta em elaboração", "confidence": 0.88},
            {"type": "next_action", "content": "Preparar proposta salarial e benefícios", "confidence": 0.85},
            {"type": "substatus", "content": "Proposta enviada — aguardando retorno", "confidence": 0.78},
        ],
        "hired": [
            {"type": "substatus", "content": "Proposta aceita", "confidence": 0.95},
            {"type": "next_action", "content": "Iniciar processo de onboarding", "confidence": 0.90},
            {"type": "substatus", "content": "Aguardando documentação de admissão", "confidence": 0.82},
        ],
        "rejected": [
            {"type": "substatus", "content": "Não avançou nesta etapa", "confidence": 0.90},
            {"type": "next_action", "content": "Enviar feedback ao candidato", "confidence": 0.85},
        ],
    }

    raw_suggestions = stage_suggestions.get(context.to_stage, [
        {"type": "substatus", "content": "Aguardando próxima ação", "confidence": 0.70},
        {"type": "next_action", "content": "Definir próximo passo com o candidato", "confidence": 0.68},
    ])

    suggestions = [
        StageMovesuggestion(
            type=s["type"],
            content=s["content"],
            confidence=s["confidence"],
        )
        for s in raw_suggestions
    ]

    logger.info(
        "Stage-move suggestions: candidate=%s from=%s to=%s suggestions=%d",
        context.candidate_id,
        context.from_stage,
        context.to_stage,
        len(suggestions),
    )

    return StageMoveSuggestionsResponse(
        suggestions=suggestions,
        generated_at=datetime.utcnow().isoformat(),
    )


@router.get("/lia/kanban-assistant/command-types", response_model=None)
async def get_command_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get available command types for the Kanban assistant.
    """
    return {
        "command_types": [
            {
                "type": "rankear_candidatos",
                "description": "Ordenar candidatos por fit com a vaga",
                "keywords": ["rankear", "ranking", "ordenar", "classificar", "melhores candidatos"],
                "example": "Rankear os candidatos por fit com a vaga"
            },
            {
                "type": "performance_funil",
                "description": "Análise de métricas do pipeline",
                "keywords": ["performance", "funil", "métricas", "pipeline", "desempenho"],
                "example": "Como está a performance do funil?"
            },
            {
                "type": "gargalos_processo",
                "description": "Identificar onde candidatos ficam parados",
                "keywords": ["gargalo", "gargalos", "travados", "parados", "atraso"],
                "example": "Identifique os gargalos do processo"
            },
            {
                "type": "comparar_candidatos",
                "description": "Comparação detalhada entre candidatos",
                "keywords": ["comparar", "comparação", "versus", "vs", "diferença"],
                "example": "Compare estes candidatos selecionados"
            },
            {
                "type": "resumir_perfil",
                "description": "Resumo executivo de um candidato",
                "keywords": ["resumir", "resumo", "perfil", "sobre", "quem é"],
                "example": "Faça um resumo do candidato X"
            },
            {
                "type": "candidatos_ativos",
                "description": "Quantos candidatos e distribuição por etapa",
                "keywords": ["quantos", "candidatos ativos", "total", "distribuição"],
                "example": "Quantos candidatos ativos temos?"
            },
            {
                "type": "taxa_conversao",
                "description": "Análise de conversão entre etapas",
                "keywords": ["conversão", "taxa", "aprovação", "reprovação"],
                "example": "Qual a taxa de conversão entre as etapas?"
            },
            {
                "type": "tempo_medio",
                "description": "Tempo médio para fechar vaga",
                "keywords": ["tempo", "dias", "duração", "quanto tempo", "demora"],
                "example": "Qual o tempo médio em cada etapa?"
            },
            {
                "type": "candidatos_parados",
                "description": "Candidatos inativos há muito tempo",
                "keywords": ["parado", "inativo", "esquecido", "sem movimento"],
                "example": "Quais candidatos estão parados há muito tempo?"
            },
            {
                "type": "top_candidatos",
                "description": "Melhores candidatos por score LIA",
                "keywords": ["top", "melhores", "destaque", "favoritos", "score alto"],
                "example": "Quais são os top candidatos?"
            },
            {
                "type": "analise_geral",
                "description": "Análise livre baseada na pergunta",
                "keywords": [],
                "example": "Qualquer outra pergunta sobre o pipeline"
            }
        ]
    }
