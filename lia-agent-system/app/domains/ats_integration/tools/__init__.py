"""ATS Integration Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.base import DomainContext

ATS_INTEGRATION_TOOLS = [
    {
        "tool_id": "ats_sync_candidate",
        "name": "Sincronizar Candidato",
        "description": "Sincroniza dados de candidato com o ATS externo",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.sync_candidate",
    },
    {
        "tool_id": "ats_sync_job",
        "name": "Sincronizar Vaga",
        "description": "Sincroniza dados de vaga com o ATS externo",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.sync_job",
    },
    {
        "tool_id": "ats_pull_candidates",
        "name": "Importar Candidatos",
        "description": "Importa candidatos do ATS externo para o WedoTalent",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.pull_candidates",
    },
    {
        "tool_id": "ats_pull_jobs",
        "name": "Importar Vagas",
        "description": "Importa vagas do ATS externo para o WedoTalent",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.pull_jobs",
    },
    {
        "tool_id": "ats_check_status",
        "name": "Verificar Status",
        "description": "Verifica o status atual da sincronização com o ATS",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.check_sync_status",
    },
    {
        "tool_id": "ats_list_connections",
        "name": "Listar Conexões",
        "description": "Lista conexões ATS configuradas",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.list_connections",
    },
    {
        "tool_id": "ats_test_connection",
        "name": "Testar Conexão",
        "description": "Testa a saúde da conexão com o ATS externo",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.test_connection",
    },
    {
        "tool_id": "ats_view_sync_log",
        "name": "Ver Log de Sincronização",
        "description": "Visualiza log de auditoria de sincronização",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.view_sync_log",
    },
    {
        "tool_id": "ats_update_status",
        "name": "Atualizar Status no ATS",
        "description": "Envia atualização de status do candidato para o ATS",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.update_candidate_status",
    },
    {
        "tool_id": "ats_send_score",
        "name": "Enviar Score para ATS",
        "description": "Envia score/parecer WSI do candidato para o ATS",
        "handler": "app.domains.ats_integration.services.ats_sync_service.ats_sync_service.send_score",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in ATS_INTEGRATION_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_ats_integration_tool(
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
