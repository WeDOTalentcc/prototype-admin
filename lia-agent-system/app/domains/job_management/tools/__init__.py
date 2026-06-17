from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

JOB_MANAGEMENT_TOOLS: list[dict[str, Any]] = [
    {
        "tool_id": "create_job_vacancy",
        "name": "Criar Vaga",
        "description": "Cria uma nova vaga de emprego",
        "parameters": {
            "title": {"type": "string", "description": "Título da vaga", "required": True},
            "department": {"type": "string", "description": "Departamento", "required": False},
            "seniority": {"type": "string", "description": "Nível de senioridade", "required": False},
            "location": {"type": "string", "description": "Localização da vaga", "required": False},
            "work_model": {"type": "string", "description": "Modelo de trabalho (Remoto, Híbrido, Presencial)", "required": False},
            "salary_min": {"type": "float", "description": "Salário mínimo", "required": False},
            "salary_max": {"type": "float", "description": "Salário máximo", "required": False},
            "description": {"type": "string", "description": "Descrição da vaga", "required": False},
        },
        "handler": "app.domains.job_management.tools.job_tools_compat.create_job_vacancy",
    },
    {
        "tool_id": "update_job_vacancy",
        "name": "Atualizar Vaga",
        "description": "Atualiza uma vaga de emprego existente",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "title": {"type": "string", "description": "Novo título", "required": False},
            "department": {"type": "string", "description": "Novo departamento", "required": False},
            "seniority": {"type": "string", "description": "Novo nível de senioridade", "required": False},
            "location": {"type": "string", "description": "Nova localização", "required": False},
            "work_model": {"type": "string", "description": "Novo modelo de trabalho", "required": False},
            "salary_min": {"type": "float", "description": "Novo salário mínimo", "required": False},
            "salary_max": {"type": "float", "description": "Novo salário máximo", "required": False},
            "description": {"type": "string", "description": "Nova descrição", "required": False},
            "status": {"type": "string", "description": "Novo status da vaga", "required": False},
        },
        "handler": "app.domains.job_management.tools.job_tools_compat.update_job_vacancy",
    },
    {
        "tool_id": "close_job_vacancy",
        "name": "Fechar Vaga",
        "description": "Fecha ou arquiva uma vaga de emprego",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "reason": {"type": "string", "description": "Motivo do fechamento", "required": False},
        },
        "handler": "app.domains.job_management.tools.job_tools_compat.close_job_vacancy",
    },
    {
        "tool_id": "pause_job_vacancy",
        "name": "Pausar Vaga",
        "description": "Pausa uma vaga de emprego temporariamente",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "reason": {"type": "string", "description": "Motivo da pausa", "required": False},
        },
        "handler": "app.domains.job_management.tools.job_tools_compat.pause_job",
    },
    {
        "tool_id": "duplicate_job_vacancy",
        "name": "Duplicar Vaga",
        "description": "Duplica uma vaga existente com todos os dados",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga a duplicar", "required": True},
            "include_candidates": {"type": "boolean", "description": "Incluir candidatos na duplicação", "required": False, "default": False},
        },
        "handler": "app.domains.job_management.tools.job_tools_compat.duplicate_job_vacancy",
    },
    {
        "tool_id": "generate_job_description",
        "name": "Gerar Job Description",
        "description": "Gera uma job description completa usando IA",
        "parameters": {
            "title": {"type": "string", "description": "Título da vaga", "required": True},
            "requirements": {"type": "list", "description": "Lista de requisitos da vaga", "required": False},
            "company_context": {"type": "string", "description": "Contexto da empresa para personalização", "required": False},
        },
        "handler": "app.domains.job_management.services.jd_generator_service.generate_job_description",
    },
    {
        "tool_id": "enrich_job_description",
        "name": "Enriquecer Job Description",
        "description": "Enriquece uma job description existente com sugestões de IA",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "sections": {"type": "list", "description": "Seções a enriquecer", "required": False},
        },
        "handler": "app.domains.job_management.services.jd_enrichment_service.enrich_job_description",
    },
    {
        "tool_id": "import_job_description",
        "name": "Importar Job Description",
        "description": "Importa uma job description existente de texto",
        "parameters": {
            "text": {"type": "string", "description": "Texto da job description", "required": True},
            "format": {"type": "string", "description": "Formato do texto (plain, html, markdown)", "required": False, "default": "plain"},
        },
        "handler": "app.domains.job_management.services.jd_import_service.import_job_description",
    },
    {
        "tool_id": "search_job_templates",
        "name": "Buscar Templates de Vaga",
        "description": "Busca templates de vaga disponíveis",
        "parameters": {
            "query": {"type": "string", "description": "Termo de busca", "required": False},
            "industry": {"type": "string", "description": "Indústria ou setor", "required": False},
            "limit": {"type": "integer", "description": "Número máximo de resultados", "required": False, "default": 10},
        },
        "handler": "app.domains.job_management.services.job_template_service.search_job_templates",
    },
    {
        "tool_id": "get_job_health",
        "name": "Health Check da Vaga",
        "description": "Verifica a saúde e completude de uma vaga",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
        },
        "handler": "app.domains.analytics.services.job_insights_service.get_job_health",
    },
    {
        "tool_id": "get_wizard_step",
        "name": "Obter Etapa do Wizard",
        "description": "Obtém os dados da etapa atual do wizard de criação de vaga",
        "parameters": {
            "session_id": {"type": "string", "description": "ID da sessão do wizard", "required": True},
            "step": {"type": "string", "description": "Identificador da etapa", "required": False},
        },
        "handler": "app.domains.job_management.services.wizard_orchestrator_service.get_wizard_step",
    },
    {
        "tool_id": "advance_wizard",
        "name": "Avançar Wizard",
        "description": "Avança o wizard de criação de vaga para a próxima etapa",
        "parameters": {
            "session_id": {"type": "string", "description": "ID da sessão do wizard", "required": True},
        },
        "handler": "app.domains.job_management.services.wizard_orchestrator_service.advance_wizard",
    },
    {
        "tool_id": "get_job_analytics",
        "name": "Analytics de Vagas",
        "description": "Obtém métricas e analytics de vagas",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": False},
            "date_range": {"type": "string", "description": "Período de análise (week, month, quarter)", "required": False, "default": "month"},
        },
        "handler": "app.domains.analytics.services.job_analytics_prompt_service.get_job_analytics",
    },
]


def _get_tool_by_id(tool_id: str) -> dict[str, Any] | None:
    """Retrieve a tool definition by its ID."""
    for tool in JOB_MANAGEMENT_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_job_management_tool(
    tool_id: str, params: dict[str, Any], tenant_id: str
) -> dict[str, Any]:
    """Execute a job management tool by its ID.

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
