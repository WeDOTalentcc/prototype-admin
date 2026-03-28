"""
Orchestrated Pipeline Chat API - Routes pipeline/persona/mapping queries through multi-agent system.

This endpoint handles intelligent conversations in the Pipelines, Personas, and Mapping tabs
of the Talent Funnel, providing context-aware responses and suggested actions.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import logging

from app.orchestrator import Orchestrator
from app.api.orchestrator_routes import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


class OrchestratedPipelineChatRequest(BaseModel):
    """Request for orchestrated pipeline chat."""
    message: str = Field(..., description="User's natural language query")
    mode: Literal['pipeline', 'persona', 'mapping'] = Field(
        ..., 
        description="Operation mode: pipeline, persona, or mapping"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context specific to the mode"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID for context continuity"
    )
    user_id: str = Field(default="recruiter", description="User ID for routing")


class OrchestratedPipelineChatResponse(BaseModel):
    """Response from orchestrated pipeline chat."""
    success: bool
    content: str = Field(..., description="Formatted markdown response")
    mode: str = Field(..., description="The mode that was used")
    intent_detected: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Routing confidence")
    suggested_prompts: List[str] = Field(default_factory=list)
    ui_action: Optional[str] = Field(None, description="Frontend action trigger")
    ui_action_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for UI action")
    structured_data: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None


PIPELINE_INTENTS = {
    "analyze_pipeline": {
        "keywords": ["analisar pipeline", "análise do pipeline", "como está o pipeline", "status do pipeline", "métricas do pipeline"],
        "description": "Análise de performance do pipeline"
    },
    "optimize_pipeline": {
        "keywords": ["otimizar", "melhorar pipeline", "sugestões de otimização", "como melhorar"],
        "description": "Sugestões de otimização"
    },
    "compare_pipelines": {
        "keywords": ["comparar pipelines", "diferença entre", "versus", "vs"],
        "description": "Comparar pipelines"
    },
    "identify_bottlenecks": {
        "keywords": ["gargalo", "bottleneck", "travado", "parado", "demora", "lento"],
        "description": "Identificar gargalos"
    },
    "suggest_actions": {
        "keywords": ["próximas ações", "o que fazer", "sugestões", "recomendações", "próximos passos"],
        "description": "Sugerir próximas ações"
    }
}

PERSONA_INTENTS = {
    "analyze_persona": {
        "keywords": ["analisar persona", "análise da persona", "sobre a persona", "entender persona"],
        "description": "Análise de persona"
    },
    "create_persona": {
        "keywords": ["criar persona", "nova persona", "definir persona", "construir persona"],
        "description": "Criar persona de vaga"
    },
    "refine_criteria": {
        "keywords": ["refinar critérios", "ajustar critérios", "melhorar critérios", "filtros"],
        "description": "Refinar critérios"
    },
    "expand_search": {
        "keywords": ["expandir busca", "ampliar busca", "mais candidatos", "aumentar pool"],
        "description": "Expandir busca"
    },
    "compare_personas": {
        "keywords": ["comparar personas", "diferença entre personas", "personas similares"],
        "description": "Comparar personas"
    }
}

MAPPING_INTENTS = {
    "analyze_company": {
        "keywords": ["analisar empresa", "análise da empresa", "sobre a empresa", "informações empresa"],
        "description": "Análise de empresa"
    },
    "identify_talents": {
        "keywords": ["identificar talentos", "encontrar talentos", "profissionais na empresa", "buscar na empresa"],
        "description": "Identificar talentos"
    },
    "monitor_changes": {
        "keywords": ["monitorar", "movimentações", "mudanças", "alertas", "acompanhar"],
        "description": "Monitorar movimentações"
    },
    "compare_companies": {
        "keywords": ["comparar empresas", "diferença entre empresas", "versus empresa"],
        "description": "Comparar empresas"
    },
    "find_similar": {
        "keywords": ["empresas similares", "empresas parecidas", "concorrentes", "empresas do setor"],
        "description": "Encontrar empresas similares"
    }
}


def detect_intent(message: str, mode: str) -> tuple[str, float]:
    """Detect user intent based on message and mode."""
    msg_lower = message.lower().strip()
    
    if mode == 'pipeline':
        intents = PIPELINE_INTENTS
    elif mode == 'persona':
        intents = PERSONA_INTENTS
    elif mode == 'mapping':
        intents = MAPPING_INTENTS
    else:
        return "general_query", 0.5
    
    for intent_id, intent_data in intents.items():
        for keyword in intent_data["keywords"]:
            if keyword in msg_lower:
                return intent_id, 0.85
    
    default_intents = {
        'pipeline': 'analyze_pipeline',
        'persona': 'analyze_persona',
        'mapping': 'analyze_company'
    }
    return default_intents.get(mode, 'general_query'), 0.6


def get_ui_action(intent: str, mode: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Determine UI action based on intent and mode."""
    ui_actions = {
        ('persona', 'create_persona'): ('open_persona_wizard', {}),
        ('persona', 'refine_criteria'): ('open_criteria_panel', {}),
        ('persona', 'expand_search'): ('expand_search_filters', {}),
        ('mapping', 'identify_talents'): ('open_talent_search', {}),
        ('mapping', 'monitor_changes'): ('open_monitoring_panel', {}),
        ('pipeline', 'identify_bottlenecks'): ('highlight_bottlenecks', {}),
        ('pipeline', 'suggest_actions'): ('show_action_recommendations', {}),
    }
    
    action = ui_actions.get((mode, intent))
    if action:
        return action[0], action[1]
    return None, None


def get_suggested_prompts(mode: str, intent: str, context: Dict[str, Any]) -> List[str]:
    """Get contextual suggested prompts based on mode and context."""
    
    pipeline_prompts = {
        "analyze_pipeline": [
            "Quais são os gargalos deste pipeline?",
            "Como posso melhorar a taxa de conversão?",
            "Quais candidatos estão há mais tempo parados?"
        ],
        "identify_bottlenecks": [
            "Sugira ações para resolver os gargalos",
            "Quais candidatos preciso priorizar?",
            "Compare com outros pipelines similares"
        ],
        "optimize_pipeline": [
            "Quais etapas posso automatizar?",
            "Como reduzir o tempo médio de contratação?",
            "Analise a eficiência do processo"
        ],
        "default": [
            "Analise o desempenho do pipeline",
            "Identifique candidatos prioritários",
            "Sugira otimizações para o processo"
        ]
    }
    
    persona_prompts = {
        "analyze_persona": [
            "Como posso refinar os critérios?",
            "Quantos candidatos atendem este perfil?",
            "Compare com personas similares"
        ],
        "create_persona": [
            "Adicione critérios de experiência",
            "Defina habilidades técnicas necessárias",
            "Inclua soft skills desejadas"
        ],
        "refine_criteria": [
            "Expanda a busca para mais candidatos",
            "Quais critérios são mais restritivos?",
            "Sugira critérios alternativos"
        ],
        "default": [
            "Analise a persona atual",
            "Sugira critérios de busca",
            "Compare com outras personas"
        ]
    }
    
    mapping_prompts = {
        "analyze_company": [
            "Quais talentos posso identificar?",
            "Monitore movimentações nesta empresa",
            "Compare com empresas concorrentes"
        ],
        "identify_talents": [
            "Filtre por senioridade específica",
            "Busque perfis em departamentos chave",
            "Identifique decision makers"
        ],
        "monitor_changes": [
            "Configure alertas de movimentação",
            "Analise histórico de mudanças",
            "Identifique padrões de turnover"
        ],
        "default": [
            "Analise a estrutura da empresa",
            "Identifique talentos potenciais",
            "Compare com empresas similares"
        ]
    }
    
    prompts_map = {
        'pipeline': pipeline_prompts,
        'persona': persona_prompts,
        'mapping': mapping_prompts
    }
    
    mode_prompts = prompts_map.get(mode, {})
    return mode_prompts.get(intent, mode_prompts.get("default", []))


def build_context_summary(mode: str, context: Dict[str, Any]) -> str:
    """Build a structured context summary for the orchestrator."""
    lines = [f"[CONTEXTO: {mode.upper()}]", ""]
    
    if mode == 'pipeline':
        if context.get('pipeline_name'):
            lines.append(f"Pipeline: {context['pipeline_name']}")
        if context.get('pipeline_id'):
            lines.append(f"ID: {context['pipeline_id']}")
        if context.get('stages'):
            lines.append(f"Etapas: {len(context['stages'])}")
            for stage in context.get('stages', [])[:5]:
                if isinstance(stage, dict):
                    lines.append(f"  - {stage.get('name', 'N/A')}: {stage.get('count', 0)} candidatos")
                else:
                    lines.append(f"  - {stage}")
        if context.get('candidates'):
            lines.append(f"Total de candidatos: {len(context['candidates'])}")
        if context.get('metrics'):
            metrics = context['metrics']
            if metrics.get('conversion_rate'):
                lines.append(f"Taxa de conversão: {metrics['conversion_rate']}%")
            if metrics.get('avg_time_to_hire'):
                lines.append(f"Tempo médio de contratação: {metrics['avg_time_to_hire']} dias")
    
    elif mode == 'persona':
        if context.get('persona_name'):
            lines.append(f"Persona: {context['persona_name']}")
        if context.get('persona_id'):
            lines.append(f"ID: {context['persona_id']}")
        if context.get('criteria'):
            lines.append("Critérios:")
            criteria = context['criteria']
            if criteria.get('skills'):
                lines.append(f"  Skills: {', '.join(criteria['skills'][:5])}")
            if criteria.get('experience_years'):
                lines.append(f"  Experiência: {criteria['experience_years']} anos")
            if criteria.get('locations'):
                lines.append(f"  Localização: {', '.join(criteria['locations'][:3])}")
        if context.get('candidates_count'):
            lines.append(f"Candidatos compatíveis: {context['candidates_count']}")
    
    elif mode == 'mapping':
        if context.get('company_name'):
            lines.append(f"Empresa: {context['company_name']}")
        if context.get('company_id'):
            lines.append(f"ID: {context['company_id']}")
        if context.get('employees'):
            lines.append(f"Funcionários mapeados: {len(context['employees'])}")
        if context.get('departments'):
            lines.append(f"Departamentos: {len(context['departments'])}")
            for dept in context.get('departments', [])[:5]:
                if isinstance(dept, dict):
                    lines.append(f"  - {dept.get('name', 'N/A')}: {dept.get('count', 0)} pessoas")
                else:
                    lines.append(f"  - {dept}")
        if context.get('industry'):
            lines.append(f"Setor: {context['industry']}")
    
    lines.append("")
    return "\n".join(lines)


def generate_fallback_response(mode: str, intent: str, context: Dict[str, Any]) -> str:
    """Generate a fallback response when orchestrator fails."""
    
    responses = {
        ('pipeline', 'analyze_pipeline'): """## Análise do Pipeline

Estou analisando os dados do pipeline. Com base no contexto fornecido:

- **Status geral**: Pipeline ativo
- **Próximos passos recomendados**: Revisar candidatos em etapas avançadas

*Use os prompts sugeridos para explorar análises mais específicas.*""",
        
        ('pipeline', 'identify_bottlenecks'): """## Identificação de Gargalos

Para identificar gargalos com precisão, analiso:

1. **Tempo médio por etapa** - Etapas com maior tempo de permanência
2. **Taxa de conversão** - Onde ocorrem as maiores perdas
3. **Candidatos parados** - Perfis sem movimentação recente

*Forneça mais detalhes sobre as etapas para uma análise completa.*""",
        
        ('persona', 'analyze_persona'): """## Análise da Persona

Analisando a persona definida:

- **Critérios atuais**: Configurados
- **Compatibilidade**: Avaliando pool de candidatos
- **Sugestões**: Considere ajustar critérios para ampliar ou refinar resultados

*Use os prompts sugeridos para refinar a persona.*""",
        
        ('mapping', 'analyze_company'): """## Análise da Empresa

Mapeando a estrutura organizacional:

- **Departamentos identificados**: Em análise
- **Talentos potenciais**: Buscando perfis relevantes
- **Movimentações recentes**: Monitorando mudanças

*Use os prompts sugeridos para explorar talentos específicos.*""",
    }
    
    key = (mode, intent)
    if key in responses:
        return responses[key]
    
    return f"""## Processando sua solicitação

Estou analisando sua pergunta no contexto de **{mode}**.

Por favor, use os prompts sugeridos para explorar funcionalidades específicas ou forneça mais detalhes sobre sua necessidade."""


@router.post("/pipeline-chat", response_model=OrchestratedPipelineChatResponse)
async def orchestrated_pipeline_chat(
    request: OrchestratedPipelineChatRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Process pipeline/persona/mapping queries through the multi-agent orchestrator.
    
    Handles three modes:
    - pipeline: Analysis and optimization of recruitment pipelines
    - persona: Management and refinement of candidate personas
    - mapping: Company mapping and talent identification
    """
    try:
        logger.info(f"[PipelineChat] Mode: {request.mode}, Message: {request.message[:100]}...")
        
        intent, confidence = detect_intent(request.message, request.mode)
        logger.info(f"[PipelineChat] Detected intent: {intent}, confidence: {confidence}")
        
        context_summary = build_context_summary(request.mode, request.context)
        
        enriched_message = f"{context_summary}\n[SOLICITAÇÃO DO RECRUTADOR]\n{request.message}"
        
        ui_action, ui_action_params = get_ui_action(intent, request.mode)
        
        try:
            result = await orchestrator.route_message(
                message=enriched_message,
                user_id=request.user_id,
                context={
                    "source": f"pipeline_chat_{request.mode}",
                    "mode": request.mode,
                    "intent": intent,
                    "pipeline_context": request.context,
                    "conversation_id": request.conversation_id
                }
            )
            
            response_content = result.get("response", "")
            if not response_content:
                response_content = generate_fallback_response(request.mode, intent, request.context)
            
            return OrchestratedPipelineChatResponse(
                success=True,
                content=response_content,
                mode=request.mode,
                intent_detected=intent,
                confidence=result.get("confidence", confidence),
                suggested_prompts=get_suggested_prompts(request.mode, intent, request.context),
                ui_action=ui_action,
                ui_action_params=ui_action_params,
                structured_data=result.get("structured_data"),
                conversation_id=request.conversation_id
            )
            
        except Exception as orch_error:
            logger.warning(f"[PipelineChat] Orchestrator error: {orch_error}, using fallback")
            
            fallback_content = generate_fallback_response(request.mode, intent, request.context)
            
            return OrchestratedPipelineChatResponse(
                success=True,
                content=fallback_content,
                mode=request.mode,
                intent_detected=intent,
                confidence=confidence,
                suggested_prompts=get_suggested_prompts(request.mode, intent, request.context),
                ui_action=ui_action,
                ui_action_params=ui_action_params,
                structured_data=None,
                conversation_id=request.conversation_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Pipeline chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing pipeline chat: {str(e)}"
        )


@router.get("/pipeline-chat/intents")
async def get_pipeline_chat_intents():
    """Get available intents for each mode in pipeline chat."""
    return {
        "modes": {
            "pipeline": {
                "description": "Análise e otimização de pipelines de recrutamento",
                "intents": [
                    {
                        "id": intent_id,
                        "description": intent_data["description"],
                        "keywords": intent_data["keywords"]
                    }
                    for intent_id, intent_data in PIPELINE_INTENTS.items()
                ]
            },
            "persona": {
                "description": "Gestão e refinamento de personas de candidatos",
                "intents": [
                    {
                        "id": intent_id,
                        "description": intent_data["description"],
                        "keywords": intent_data["keywords"]
                    }
                    for intent_id, intent_data in PERSONA_INTENTS.items()
                ]
            },
            "mapping": {
                "description": "Mapeamento de empresas e identificação de talentos",
                "intents": [
                    {
                        "id": intent_id,
                        "description": intent_data["description"],
                        "keywords": intent_data["keywords"]
                    }
                    for intent_id, intent_data in MAPPING_INTENTS.items()
                ]
            }
        }
    }
