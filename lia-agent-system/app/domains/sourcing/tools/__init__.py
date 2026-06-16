"""Sourcing Domain - Tool definitions and executor for pipeline management."""
from typing import Any, Dict, List

from app.domains.base import DomainContext

SOURCING_TOOLS = [
    {
        "tool_id": "sourcing_update_candidate_stage",
        "name": "Mover Candidato de Etapa",
        "description": "Move um candidato para uma etapa diferente do pipeline de recrutamento",
        "handler": "app.domains.cv_screening.tools.candidate_tools.update_candidate_stage",
    },
    {
        "tool_id": "sourcing_reject_candidate",
        "name": "Rejeitar Candidato",
        "description": "Rejeita um candidato no processo seletivo",
        "handler": "app.domains.cv_screening.tools.candidate_tools.reject_candidate",
    },
    {
        "tool_id": "sourcing_shortlist_candidate",
        "name": "Shortlist Candidato",
        "description": "Adiciona candidato à shortlist/favoritos",
        "handler": "app.domains.cv_screening.tools.candidate_tools.shortlist_candidate",
    },
    {
        "tool_id": "sourcing_add_candidate_to_vacancy",
        "name": "Adicionar Candidato à Vaga",
        "description": "Adiciona um candidato a uma vaga de emprego",
        "handler": "app.domains.cv_screening.tools.candidate_tools.add_candidate_to_vacancy",
    },
    {
        "tool_id": "sourcing_search_candidates",
        "name": "Buscar Candidatos",
        "description": "Busca candidatos com filtros avançados (skills, experiência, localização, etc.)",
        "handler": "app.domains.sourcing.tools.query_tools.search_candidates",
    },
    {
        "tool_id": "sourcing_rank_candidates",
        "name": "Rankear Candidatos",
        "description": "Ordena candidatos por pontuação usando Weighted Rank Fusion",
        "handler": "app.domains.sourcing.tools.query_tools.rank_candidates",
    },
    {
        "tool_id": "sourcing_get_candidate_details",
        "name": "Detalhes do Candidato",
        "description": "Obtém informações detalhadas de um candidato específico",
        "handler": "app.domains.sourcing.tools.query_tools.get_candidate_details",
    },
    {
        "tool_id": "sourcing_get_candidate_stats",
        "name": "Estatísticas de Candidatos",
        "description": "Obtém métricas e estatísticas sobre candidatos",
        "handler": "app.domains.sourcing.tools.query_tools.get_candidate_stats",
    },
    {
        "tool_id": "sourcing_get_candidate_history",
        "name": "Histórico do Candidato",
        "description": "Consulta histórico de participação do candidato em processos",
        "handler": "app.domains.sourcing.tools.query_tools.get_candidate_history",
    },
    {
        "tool_id": "sourcing_get_talent_quality",
        "name": "Qualidade de Talentos",
        "description": "Obtém métricas de qualidade dos talentos no pipeline",
        "handler": "app.domains.sourcing.tools.query_tools.get_talent_quality",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in SOURCING_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_sourcing_tool(
    tool_id: str,
    parameters: dict[str, Any],
    context: DomainContext,
) -> dict[str, Any]:
    tool = _get_tool_by_id(tool_id)
    if not tool:
        return {"error": f"Tool {tool_id} not found", "status": "error"}

    handler_path = tool["handler"]
    parts = handler_path.rsplit(".", 1)
    if len(parts) != 2:
        return {"error": f"Invalid handler path: {handler_path}", "status": "error"}

    module_path, func_name = parts
    try:
        import importlib
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        result = await handler(**parameters) if callable(handler) else handler
        return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e), "status": "error", "tool_id": tool_id}
