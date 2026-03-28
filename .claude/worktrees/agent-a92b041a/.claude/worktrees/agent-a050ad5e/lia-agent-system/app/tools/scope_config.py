"""
Scope Configuration for Tool Access Control.

Defines which tools are available in each prompt context:
- TALENT_FUNNEL: Candidate-focused queries and actions
- JOB_TABLE: Vacancy management and analysis
- IN_JOB: Pipeline actions within specific job vacancy

This ensures strict separation between candidate and vacancy domains
for architectural clarity and user experience consistency.
"""
from typing import Dict, List, Set
from enum import Enum


class PromptScope(str, Enum):
    """Available prompt scopes in the platform."""
    TALENT_FUNNEL = "talent_funnel"
    JOB_TABLE = "job_table"
    IN_JOB = "in_job"
    GLOBAL = "global"


FUNNEL_QUERY_TOOLS: Set[str] = {
    "search_candidates",
    "get_candidate_details",
    "get_candidate_stats",
    "compare_candidates",
    "get_talent_quality",
    "get_talent_engagement",
    "get_talent_availability",
    "get_diversity_metrics",
    "get_candidate_history",
    "get_ml_predictions",
    "get_conversion_patterns",
}

FUNNEL_ACTION_TOOLS: Set[str] = {
    "add_candidate_to_vacancy",
    "reject_candidate",
    "shortlist_candidate",
    "add_to_list",
    "hide_candidate",
    "send_email",
    "send_whatsapp",
    "send_bulk_email",
    "export_candidates",
}

VACANCY_QUERY_TOOLS: Set[str] = {
    "search_jobs",
    "get_job_details",
    "get_pipeline_stats",
    "get_recruiter_metrics",
    "get_velocity_metrics",
    "get_efficiency_metrics",
    "get_comparative_metrics",
    "get_workload_distribution",
    "get_hiring_quality",
    "get_cost_metrics",
    "get_trends",
    "get_market_benchmarks",
}

VACANCY_ACTION_TOOLS: Set[str] = {
    "create_job",
    "update_job",
    "pause_job",
    "close_job",
    "publish_job",
    "export_job_analytics",
    "generate_report",
}

IN_JOB_QUERY_TOOLS: Set[str] = {
    "get_job_details",
    "get_vacancy_funnel",
    "get_candidate_details",
    "get_activity_summary",
    "get_pending_actions",
    "compare_candidates",
    "get_candidate_stats",
    "get_bottleneck_analysis",
    "get_job_velocity",
    "get_job_quality_metrics",
    "get_stakeholder_metrics",
    "get_prediction_metrics",
    "get_job_benchmark",
    "get_smart_alerts",
}

IN_JOB_ACTION_TOOLS: Set[str] = {
    "update_candidate_stage",
    "bulk_update_candidates_stage",
    "reject_candidate",
    "shortlist_candidate",
    "add_to_list",
    "hide_candidate",
    "wsi_screening",
    "send_email",
    "send_whatsapp",
    "schedule_interview",
    "send_feedback",
}

GLOBAL_TOOLS: Set[str] = {
    "generate_report",
    "schedule_report",
}


SCOPE_TOOL_MAPPING: Dict[PromptScope, Dict[str, Set[str]]] = {
    PromptScope.TALENT_FUNNEL: {
        "query": FUNNEL_QUERY_TOOLS,
        "action": FUNNEL_ACTION_TOOLS,
        "all": FUNNEL_QUERY_TOOLS | FUNNEL_ACTION_TOOLS,
    },
    PromptScope.JOB_TABLE: {
        "query": VACANCY_QUERY_TOOLS,
        "action": VACANCY_ACTION_TOOLS,
        "all": VACANCY_QUERY_TOOLS | VACANCY_ACTION_TOOLS,
    },
    PromptScope.IN_JOB: {
        "query": IN_JOB_QUERY_TOOLS,
        "action": IN_JOB_ACTION_TOOLS,
        "all": IN_JOB_QUERY_TOOLS | IN_JOB_ACTION_TOOLS,
    },
    PromptScope.GLOBAL: {
        "query": set(),
        "action": GLOBAL_TOOLS,
        "all": GLOBAL_TOOLS,
    },
}


SCOPE_DESCRIPTIONS: Dict[PromptScope, Dict[str, str]] = {
    PromptScope.TALENT_FUNNEL: {
        "name": "Funil de Talentos",
        "description": "Foco em candidatos: busca, avaliação, comparação e comunicação.",
        "capabilities": [
            "Buscar candidatos por skills, experiência, localização",
            "Ver detalhes e histórico de candidatos",
            "Comparar candidatos lado a lado",
            "Enviar comunicações em massa",
            "Adicionar candidatos a vagas",
            "Exportar lista de candidatos",
        ],
        "restrictions": [
            "Não pode criar ou gerenciar vagas",
            "Não pode acessar métricas de recrutador",
            "Não pode alterar pipeline de vaga específica",
        ],
    },
    PromptScope.JOB_TABLE: {
        "name": "Tabela de Vagas",
        "description": "Foco em vagas: criação, gestão, análise de pipeline e métricas.",
        "capabilities": [
            "Listar e buscar vagas por status, departamento",
            "Criar, editar, pausar e fechar vagas",
            "Ver métricas gerais do pipeline",
            "Analisar performance do recrutador",
            "Gerar relatórios de vagas",
        ],
        "restrictions": [
            "Não pode agir sobre candidatos individuais",
            "Não pode movimentar candidatos entre etapas",
            "Não pode enviar comunicações a candidatos",
        ],
    },
    PromptScope.IN_JOB: {
        "name": "Dentro da Vaga",
        "description": "Foco no pipeline: gestão de candidatos dentro de uma vaga específica.",
        "capabilities": [
            "Ver funil da vaga com taxas de conversão",
            "Mover candidatos entre etapas",
            "Ver atividades e pendências da vaga",
            "Agendar entrevistas",
            "Enviar feedbacks",
            "Comparar candidatos da vaga",
        ],
        "restrictions": [
            "Ações limitadas à vaga atual",
            "Não pode criar ou gerenciar outras vagas",
            "Não pode buscar candidatos fora da vaga",
        ],
    },
}


def get_tools_for_scope(
    scope: PromptScope,
    tool_type: str = "all"
) -> Set[str]:
    """
    Get the set of tools available for a given scope.
    
    Args:
        scope: The prompt scope (TALENT_FUNNEL, JOB_TABLE, IN_JOB)
        tool_type: Type of tools ("query", "action", or "all")
        
    Returns:
        Set of tool names available in this scope
    """
    if scope not in SCOPE_TOOL_MAPPING:
        return set()
    
    scope_tools = SCOPE_TOOL_MAPPING[scope]
    
    if tool_type not in scope_tools:
        return scope_tools.get("all", set())
    
    return scope_tools[tool_type]


def filter_tools_by_scope(
    tools: List[Dict],
    scope: PromptScope
) -> List[Dict]:
    """
    Filter a list of tool definitions to only those allowed in the scope.
    
    Args:
        tools: List of tool definition dictionaries
        scope: The prompt scope to filter for
        
    Returns:
        Filtered list of tool definitions
    """
    allowed_tools = get_tools_for_scope(scope, "all")
    return [t for t in tools if t.get("name") in allowed_tools]


def is_tool_allowed_in_scope(tool_name: str, scope: PromptScope) -> bool:
    """
    Check if a specific tool is allowed in the given scope.
    
    Args:
        tool_name: Name of the tool
        scope: The prompt scope to check
        
    Returns:
        True if tool is allowed, False otherwise
    """
    allowed_tools = get_tools_for_scope(scope, "all")
    return tool_name in allowed_tools


def get_scope_system_prompt_addition(scope: PromptScope) -> str:
    """
    Get additional system prompt text that enforces scope boundaries.
    
    Args:
        scope: The prompt scope
        
    Returns:
        System prompt addition text
    """
    if scope not in SCOPE_DESCRIPTIONS:
        return ""
    
    desc = SCOPE_DESCRIPTIONS[scope]
    
    capabilities_text = "\n".join(f"  - {c}" for c in desc["capabilities"])
    restrictions_text = "\n".join(f"  - {r}" for r in desc["restrictions"])
    
    return f"""
## Contexto: {desc['name']}

{desc['description']}

### O que você PODE fazer:
{capabilities_text}

### O que você NÃO PODE fazer:
{restrictions_text}

Sempre respeite os limites do seu escopo atual. Se o usuário pedir algo fora do escopo, explique educadamente que essa ação deve ser feita em outra área da plataforma.
"""


SCOPE_INTENT_MAPPING: Dict[str, PromptScope] = {
    "search_candidates": PromptScope.TALENT_FUNNEL,
    "get_candidate_details": PromptScope.TALENT_FUNNEL,
    "get_candidate_stats": PromptScope.TALENT_FUNNEL,
    "compare_candidates": PromptScope.TALENT_FUNNEL,
    "add_candidate_to_vacancy": PromptScope.TALENT_FUNNEL,
    "get_talent_quality": PromptScope.TALENT_FUNNEL,
    "get_talent_engagement": PromptScope.TALENT_FUNNEL,
    "get_talent_availability": PromptScope.TALENT_FUNNEL,
    "get_diversity_metrics": PromptScope.TALENT_FUNNEL,
    "get_candidate_history": PromptScope.TALENT_FUNNEL,
    "get_ml_predictions": PromptScope.TALENT_FUNNEL,
    "get_conversion_patterns": PromptScope.TALENT_FUNNEL,
    
    "search_jobs": PromptScope.JOB_TABLE,
    "get_job_details": PromptScope.JOB_TABLE,
    "create_job": PromptScope.JOB_TABLE,
    "update_job": PromptScope.JOB_TABLE,
    "get_pipeline_stats": PromptScope.JOB_TABLE,
    "get_recruiter_metrics": PromptScope.JOB_TABLE,
    "get_velocity_metrics": PromptScope.JOB_TABLE,
    "get_efficiency_metrics": PromptScope.JOB_TABLE,
    "get_comparative_metrics": PromptScope.JOB_TABLE,
    "get_workload_distribution": PromptScope.JOB_TABLE,
    "get_hiring_quality": PromptScope.JOB_TABLE,
    "get_cost_metrics": PromptScope.JOB_TABLE,
    "get_trends": PromptScope.JOB_TABLE,
    "get_market_benchmarks": PromptScope.JOB_TABLE,
    
    "update_candidate_stage": PromptScope.IN_JOB,
    "get_vacancy_funnel": PromptScope.IN_JOB,
    "get_activity_summary": PromptScope.IN_JOB,
    "get_pending_actions": PromptScope.IN_JOB,
    "schedule_interview": PromptScope.IN_JOB,
    "get_bottleneck_analysis": PromptScope.IN_JOB,
    "get_job_velocity": PromptScope.IN_JOB,
    "get_job_quality_metrics": PromptScope.IN_JOB,
    "get_stakeholder_metrics": PromptScope.IN_JOB,
    "get_prediction_metrics": PromptScope.IN_JOB,
    "get_job_benchmark": PromptScope.IN_JOB,
    "get_smart_alerts": PromptScope.IN_JOB,
}


def get_suggested_scope_for_intent(intent: str) -> PromptScope:
    """
    Get the suggested scope for a given intent/tool name.
    
    Args:
        intent: Intent or tool name
        
    Returns:
        Suggested PromptScope
    """
    return SCOPE_INTENT_MAPPING.get(intent, PromptScope.GLOBAL)
