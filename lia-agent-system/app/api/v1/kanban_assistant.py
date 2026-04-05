"""
LIA Kanban Assistant API endpoints.
Provides AI-powered analysis for recruitment pipelines.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.domains.recruiter_assistant.services.kanban_assistant_service import kanban_assistant_service

logger = logging.getLogger(__name__)

router = APIRouter()


class KanbanAssistantRequest(BaseModel):
    """Request model for Kanban Assistant."""
    command: str = Field(..., description="User's natural language command")
    command_type: Optional[str] = Field(None, description="Pre-detected command type (rankear, funil, etc.)")
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
        description="IDs of selected candidates for comparison operations"
    )


class KanbanAssistantResponse(BaseModel):
    """Response model for Kanban Assistant."""
    success: bool = Field(..., description="Whether the request was successful")
    response_type: str = Field(..., description="Type of analysis performed")
    content: str = Field(..., description="Formatted markdown response")
    structured_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured data from the analysis (ranking, metrics, etc.)"
    )
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="List of suggested next actions"
    )
    follow_up_prompts: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )
    ui_action: Optional[str] = Field(None, description="Frontend action trigger")
    ui_action_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for UI action")


@router.post("/lia/kanban-assistant", response_model=KanbanAssistantResponse)
async def kanban_assistant(request: KanbanAssistantRequest) -> KanbanAssistantResponse:
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
    except Exception as e:
        logger.error(f"Kanban assistant failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/lia/kanban-assistant/command-types")
async def get_command_types():
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
