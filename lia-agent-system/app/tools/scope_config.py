from typing import List, Optional, Set, Type
"""
Scope Configuration for Tool Access Control.

Defines which tools are available in each prompt context:
- TALENT_FUNNEL: Candidate-focused queries and actions
- JOB_TABLE: Vacancy management and analysis
- IN_JOB: Pipeline actions within specific job vacancy

Configuration is loaded from tool_permissions.yaml (declarative, per-tenant).
Hardcoded Set[str] definitions remain as fallback constants for backward compatibility.

Task #125: Replaced hardcoded Sets with YAML-driven ToolPermissionsLoader.
"""
from enum import Enum

from app.tools.tool_permissions_loader import (
    get_permissions,
)
from app.tools.tool_permissions_loader import (
    get_tools_for_scope as _yaml_get_tools,
)
from app.tools.tool_permissions_loader import (
    is_tool_allowed as _yaml_is_tool_allowed,
)


class PromptScope(str, Enum):
    """Available prompt scopes in the platform."""
    TALENT_FUNNEL = "talent_funnel"
    JOB_TABLE = "job_table"
    IN_JOB = "in_job"
    GLOBAL = "global"


# ---------------------------------------------------------------------------
# Backward-compatible constants — derived from YAML global defaults.
# These are computed once at import time from the declarative config.
# ---------------------------------------------------------------------------

def _load_global_set(scope: str, tool_type: str) -> set[str]:
    try:
        return _yaml_get_tools(scope, tool_type, tenant_id=None)
    except Exception:
        return set()


FUNNEL_QUERY_TOOLS: set[str] = _load_global_set("talent_funnel", "query")
FUNNEL_ACTION_TOOLS: set[str] = _load_global_set("talent_funnel", "action")
VACANCY_QUERY_TOOLS: set[str] = _load_global_set("job_table", "query")
VACANCY_ACTION_TOOLS: set[str] = _load_global_set("job_table", "action")
IN_JOB_QUERY_TOOLS: set[str] = _load_global_set("in_job", "query")
IN_JOB_ACTION_TOOLS: set[str] = _load_global_set("in_job", "action")
GLOBAL_TOOLS: set[str] = _load_global_set("global", "action")


SCOPE_TOOL_MAPPING: dict[PromptScope, dict[str, set[str]]] = {
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


SCOPE_DESCRIPTIONS: dict[PromptScope, dict[str, object]] = {
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


# ---------------------------------------------------------------------------
# Public API — tenant-aware wrappers over ToolPermissionsLoader
# ---------------------------------------------------------------------------

def get_tools_for_scope(
    scope: PromptScope,
    tool_type: str = "all",
    tenant_id: str | None = None,
) -> set[str]:
    """
    Get the set of tools available for a given scope.

    Args:
        scope: The prompt scope (TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL).
        tool_type: Type of tools ("query", "action", or "all").
        tenant_id: Optional tenant identifier for per-tenant overrides.

    Returns:
        Set of tool names available in this scope.
    """
    scope_str = scope.value if isinstance(scope, PromptScope) else str(scope)
    return _yaml_get_tools(scope_str, tool_type, tenant_id=tenant_id)


def filter_tools_by_scope(
    tools: list[dict],
    scope: PromptScope,
    tenant_id: str | None = None,
) -> list[dict]:
    """
    Filter a list of tool definitions to only those allowed in the scope.

    Args:
        tools: List of tool definition dictionaries.
        scope: The prompt scope to filter for.
        tenant_id: Optional tenant identifier for per-tenant overrides.

    Returns:
        Filtered list of tool definitions.
    """
    scope_str = scope.value if isinstance(scope, PromptScope) else str(scope)
    return get_permissions(tenant_id).filter_tools(tools, scope_str)


def is_tool_allowed_in_scope(
    tool_name: str,
    scope: PromptScope,
    tenant_id: str | None = None,
) -> bool:
    """
    Check if a specific tool is allowed in the given scope.

    Args:
        tool_name: Name of the tool.
        scope: The prompt scope to check.
        tenant_id: Optional tenant identifier for per-tenant overrides.

    Returns:
        True if tool is allowed, False otherwise.
    """
    scope_str = scope.value if isinstance(scope, PromptScope) else str(scope)
    return _yaml_is_tool_allowed(tool_name, scope_str, tenant_id=tenant_id)


def get_scope_system_prompt_addition(scope: PromptScope) -> str:
    """
    Get additional system prompt text that enforces scope boundaries.

    Args:
        scope: The prompt scope.

    Returns:
        System prompt addition text.
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


SCOPE_INTENT_MAPPING: dict[str, PromptScope] = {
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
        intent: Intent or tool name.

    Returns:
        Suggested PromptScope.
    """
    return SCOPE_INTENT_MAPPING.get(intent, PromptScope.GLOBAL)
