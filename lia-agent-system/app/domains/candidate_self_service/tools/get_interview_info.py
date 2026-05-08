"""Tool: get_interview_info — fetches scheduled interview details from Rails API."""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_FORBIDDEN_FIELDS = frozenset([
    "interviewer_notes", "feedback", "lia_suggested_questions",
    "lia_preparation_notes", "recording_url", "is_private",
])


@tool_handler("candidate_self_service", require_company=True)
async def _get_interview_info(**kwargs: Any) -> dict[str, Any]:
    candidate_id: str = kwargs.get("candidate_id", "")
    vacancy_id: str = kwargs.get("vacancy_id", "")
    company_id: str = kwargs.get("company_id", "")

    if not candidate_id or not vacancy_id:
        return {"success": False, "message": "candidate_id e vacancy_id são obrigatórios."}

    try:
        from app.shared.rails_client import rails_get
        data = await rails_get(
            "/v1/candidate-portal/interview",
            params={"candidate_id": candidate_id, "vacancy_id": vacancy_id},
            company_id=company_id,
        )
        safe_data = {k: v for k, v in data.items() if k not in _FORBIDDEN_FIELDS}
        logger.info(
            "[CSS Tool] get_interview_info candidate_id=%s status=%s",
            candidate_id, safe_data.get("status"),
        )
        return {"success": True, "data": safe_data}
    except Exception as exc:
        logger.error("[CSS Tool] get_interview_info error: %s", exc)
        return {"success": False, "message": "Informação de entrevista não disponível."}


get_interview_info = ToolDefinition(
    name="get_interview_info",
    description=(
        "Retorna informações sobre entrevista agendada: data, horário, duração, "
        "formato (online/presencial) e link/localização. "
        "Use quando o candidato perguntar sobre entrevista ou agendamento."
    ),
    parameters={
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string", "description": "ID do candidato (do token JWT)"},
            "vacancy_id": {"type": "string", "description": "ID da vaga (do token JWT)"},
        },
        "required": ["candidate_id", "vacancy_id"],
    },
    function=_get_interview_info,
)
