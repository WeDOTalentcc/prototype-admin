from __future__ import annotations

from typing import Dict, Any, List, Optional
import importlib
import logging

logger = logging.getLogger(__name__)

SOURCING_TOOLS: List[Dict[str, Any]] = [
    {
        "tool_id": "search_candidates",
        "name": "Buscar Candidatos",
        "description": "Busca candidatos no banco de dados com filtros",
        "parameters": {
            "skills": {"type": "list", "description": "Lista de habilidades requeridas", "required": False},
            "seniority": {"type": "string", "description": "Nível de senioridade", "required": False},
            "location": {"type": "string", "description": "Localização desejada", "required": False},
            "min_experience_years": {"type": "integer", "description": "Experiência mínima em anos", "required": False},
            "max_experience_years": {"type": "integer", "description": "Experiência máxima em anos", "required": False},
            "min_score": {"type": "float", "description": "Score mínimo LIA/WSI", "required": False},
            "status": {"type": "string", "description": "Status do candidato", "required": False},
            "limit": {"type": "integer", "description": "Número máximo de resultados", "required": False, "default": 20},
        },
        "handler": "app.tools.query_tools.search_candidates",
    },
    {
        "tool_id": "search_jobs",
        "name": "Buscar Vagas",
        "description": "Busca vagas de emprego com filtros",
        "parameters": {
            "status": {"type": "string", "description": "Status da vaga (Ativa, Pausada, Fechada)", "required": False},
            "department": {"type": "string", "description": "Departamento", "required": False},
            "seniority": {"type": "string", "description": "Nível de senioridade", "required": False},
            "work_model": {"type": "string", "description": "Modelo de trabalho (Remoto, Híbrido, Presencial)", "required": False},
            "limit": {"type": "integer", "description": "Número máximo de resultados", "required": False, "default": 20},
        },
        "handler": "app.tools.query_tools.search_jobs",
    },
    {
        "tool_id": "boolean_search",
        "name": "Busca Booleana",
        "description": "Gera e executa queries booleanas para busca avançada de candidatos",
        "parameters": {
            "title": {"type": "string", "description": "Cargo ou título desejado", "required": False},
            "skills": {"type": "list", "description": "Habilidades requeridas", "required": False},
            "companies": {"type": "list", "description": "Empresas de interesse", "required": False},
            "industries": {"type": "list", "description": "Indústrias alvo", "required": False},
            "location": {"type": "string", "description": "Localização", "required": False},
            "seniority": {"type": "string", "description": "Nível de senioridade", "required": False},
            "exclude_terms": {"type": "list", "description": "Termos a excluir", "required": False},
        },
        "handler": "app.domains.sourcing.services.query_builders.BooleanQueryBuilder.build_query",
    },
    {
        "tool_id": "semantic_search",
        "name": "Busca Semântica",
        "description": "Busca candidatos por similaridade semântica usando embeddings",
        "parameters": {
            "query_text": {"type": "string", "description": "Texto de busca em linguagem natural", "required": True},
            "top_k": {"type": "integer", "description": "Número de resultados mais similares", "required": False, "default": 10},
            "min_similarity": {"type": "float", "description": "Similaridade mínima (0-1)", "required": False, "default": 0.7},
            "filters": {"type": "dict", "description": "Filtros adicionais a aplicar", "required": False},
        },
        "handler": "app.tools.query_tools.search_candidates",
    },
    {
        "tool_id": "pearch_search",
        "name": "Busca Pearch AI",
        "description": "Busca candidatos externos via integração Pearch AI",
        "parameters": {
            "query": {"type": "string", "description": "Query de busca para Pearch", "required": True},
            "location": {"type": "string", "description": "Localização alvo", "required": False},
            "seniority": {"type": "string", "description": "Nível de senioridade", "required": False},
            "skills": {"type": "list", "description": "Habilidades requeridas", "required": False},
            "limit": {"type": "integer", "description": "Número máximo de resultados", "required": False, "default": 20},
        },
        "handler": "app.tools.query_tools.search_candidates",
    },
    {
        "tool_id": "candidate_match",
        "name": "Match de Candidatos",
        "description": "Calcula compatibilidade entre candidato e vaga",
        "parameters": {
            "candidate_id": {"type": "string", "description": "ID do candidato", "required": True},
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "weights": {
                "type": "dict",
                "description": "Pesos para skills, experiência e localização",
                "required": False,
                "default": {"skills": 0.5, "experience": 0.3, "location": 0.2},
            },
        },
        "handler": "app.tools.query_tools.search_candidates",
    },
    {
        "tool_id": "talent_pool_query",
        "name": "Consulta Talent Pool",
        "description": "Busca candidatos no pool interno de talentos da empresa",
        "parameters": {
            "pool_name": {"type": "string", "description": "Nome do talent pool", "required": False},
            "skills": {"type": "list", "description": "Habilidades desejadas", "required": False},
            "seniority": {"type": "string", "description": "Nível de senioridade", "required": False},
            "available_only": {"type": "boolean", "description": "Apenas candidatos disponíveis", "required": False, "default": True},
            "limit": {"type": "integer", "description": "Número máximo de resultados", "required": False, "default": 20},
        },
        "handler": "app.tools.query_tools.search_candidates",
    },
    {
        "tool_id": "search_analytics",
        "name": "Análise de Busca",
        "description": "Analisa efetividade e métricas das buscas realizadas",
        "parameters": {
            "period": {"type": "string", "description": "Período de análise (week, month, quarter)", "required": False, "default": "month"},
            "search_type": {"type": "string", "description": "Tipo de busca a analisar", "required": False},
            "recruiter_id": {"type": "string", "description": "ID do recrutador", "required": False},
        },
        "handler": "app.tools.query_tools.search_jobs",
    },
    {
        "tool_id": "volume_check",
        "name": "Verificação de Volume",
        "description": "Avalia o volume disponível de candidatos para determinado perfil",
        "parameters": {
            "title": {"type": "string", "description": "Cargo ou título", "required": True},
            "skills": {"type": "list", "description": "Habilidades requeridas", "required": False},
            "location": {"type": "string", "description": "Localização", "required": False},
            "seniority": {"type": "string", "description": "Nível de senioridade", "required": False},
            "include_external": {"type": "boolean", "description": "Incluir fontes externas na estimativa", "required": False, "default": False},
        },
        "handler": "app.tools.query_tools.search_candidates",
    },
]


def _get_tool_by_id(tool_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a tool definition by its ID."""
    for tool in SOURCING_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_sourcing_tool(
    tool_id: str, params: Dict[str, Any], tenant_id: str
) -> Dict[str, Any]:
    """Execute a sourcing tool by its ID.

    Dynamically imports the handler function referenced in the tool definition
    and invokes it with the provided parameters.

    Args:
        tool_id: Identifier of the tool to execute.
        params: Parameters to pass to the handler function.
        tenant_id: Tenant identifier for multi-tenancy scoping.

    Returns:
        Result dictionary from the handler execution.
    """
    tool_def = _get_tool_by_id(tool_id)
    if tool_def is None:
        return {
            "success": False,
            "message": f"Ferramenta '{tool_id}' não encontrada.",
            "error": "tool_not_found",
        }

    handler_path = tool_def["handler"]
    module_path, func_name = handler_path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
        handler_fn = getattr(module, func_name)
    except (ImportError, AttributeError) as exc:
        logger.error(f"Falha ao carregar handler '{handler_path}': {exc}")
        return {
            "success": False,
            "message": f"Erro ao carregar ferramenta '{tool_id}'.",
            "error": str(exc),
        }

    try:
        enriched_params = dict(params)
        enriched_params["_tenant_id"] = tenant_id
        logger.info(f"Executando ferramenta '{tool_id}' (tenant={tenant_id})")

        if callable(handler_fn):
            import asyncio
            if asyncio.iscoroutinefunction(handler_fn):
                result = await handler_fn(**enriched_params)
            else:
                result = handler_fn(**enriched_params)
        else:
            return {
                "success": False,
                "message": f"Handler de '{tool_id}' não é invocável.",
                "error": "handler_not_callable",
            }

        return result

    except Exception as exc:
        logger.error(f"Erro ao executar ferramenta '{tool_id}': {exc}", exc_info=True)
        return {
            "success": False,
            "message": f"Erro na execução de '{tool_id}': {str(exc)}",
            "error": str(exc),
        }
