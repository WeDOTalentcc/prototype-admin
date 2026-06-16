from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CV_SCREENING_TOOLS: list[dict[str, Any]] = [
    {
        "tool_id": "parse_cv",
        "name": "Parse CV",
        "description": "Parse CV and extract structured data",
        "parameters": {
            "cv_text": {"type": "string", "description": "Texto do CV para análise", "required": True},
            "format": {"type": "string", "description": "Formato do CV (plain, html, pdf)", "required": False},
        },
        "handler": "app.domains.cv_screening.services.cv_parser.parse_cv",
    },
    {
        "tool_id": "score_cv",
        "name": "Score CV",
        "description": "Score CV against job requirements",
        "parameters": {
            "candidate_id": {"type": "string", "description": "ID do candidato", "required": True},
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
        },
        "handler": "app.domains.cv_screening.services.cv_scoring_service.score_cv",
    },
    {
        "tool_id": "evaluate_rubric",
        "name": "Avaliar Rubrica",
        "description": "Evaluate candidate by rubric",
        "parameters": {
            "candidate_id": {"type": "string", "description": "ID do candidato", "required": True},
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "rubric_id": {"type": "string", "description": "ID da rubrica", "required": False},
        },
        "handler": "app.domains.cv_screening.services.rubric_evaluation_service.evaluate_rubric",
    },
    {
        "tool_id": "calculate_wsi",
        "name": "Calcular WSI",
        "description": "Calculate WSI score",
        "parameters": {
            "candidate_id": {"type": "string", "description": "ID do candidato", "required": True},
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
        },
        "handler": "app.domains.cv_screening.services.wsi_service.calculate_wsi",
    },
    {
        "tool_id": "generate_wsi_questions",
        "name": "Gerar Perguntas WSI",
        "description": "Generate WSI screening questions",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "count": {"type": "integer", "description": "Número de perguntas a gerar", "required": False, "default": 5},
        },
        "handler": "app.domains.cv_screening.services.wsi_service.generate_wsi_questions_tool",
    },
    {
        "tool_id": "adjust_wsi_questions",
        "name": "Ajustar Perguntas WSI",
        "description": "Adjust/refine questions with AI",
        "parameters": {
            "question_ids": {"type": "list", "description": "IDs das perguntas a ajustar", "required": True},
            "feedback": {"type": "string", "description": "Feedback para ajuste", "required": False},
        },
        "handler": "app.domains.cv_screening.services.wsi_question_adjuster.adjust_questions",
    },
    {
        "tool_id": "normalize_scores",
        "name": "Normalizar Scores",
        "description": "Normalize scores across candidates",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "candidate_ids": {"type": "list", "description": "IDs dos candidatos", "required": False},
        },
        "handler": "app.domains.cv_screening.services.score_normalization_service.normalize",
    },
    {
        "tool_id": "assess_seniority",
        "name": "Avaliar Senioridade",
        "description": "Assess candidate seniority level",
        "parameters": {
            "candidate_id": {"type": "string", "description": "ID do candidato", "required": True},
            "job_id": {"type": "string", "description": "ID da vaga", "required": False},
        },
        "handler": "app.domains.cv_screening.services.seniority_resolver.resolve_seniority",
    },
    {
        "tool_id": "send_candidate_feedback",
        "name": "Enviar Feedback",
        "description": "Send personalized feedback",
        "parameters": {
            "candidate_id": {"type": "string", "description": "ID do candidato", "required": True},
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
        },
        "handler": "app.domains.cv_screening.services.personalized_feedback_service.send_feedback",
    },
    {
        "tool_id": "pre_qualify_candidate",
        "name": "Pré-qualificar Candidato",
        "description": "Pre-qualify candidate",
        "parameters": {
            "candidate_id": {"type": "string", "description": "ID do candidato", "required": True},
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
        },
        "handler": "app.domains.cv_screening.services.pre_qualification_service.pre_qualify",
    },
    {
        "tool_id": "run_screening_pipeline",
        "name": "Pipeline de Triagem",
        "description": "Run full WSI screening pipeline",
        "parameters": {
            "job_id": {"type": "string", "description": "ID da vaga", "required": True},
            "candidate_ids": {"type": "list", "description": "IDs dos candidatos", "required": False},
        },
        "handler": "app.domains.cv_screening.services.wsi_screening_pipeline.run_pipeline",
    },
]


def _get_tool_by_id(tool_id: str) -> dict[str, Any] | None:
    """Retrieve a tool definition by its ID."""
    for tool in CV_SCREENING_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_cv_screening_tool(
    tool_id: str, params: dict[str, Any], tenant_id: str
) -> dict[str, Any]:
    """Execute a cv screening tool by its ID.

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
