"""Tool: get_application_status — fetches candidate pipeline stage from Rails API."""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

# Fields NEVER returned to candidate (ADR-006 + LGPD)
_FORBIDDEN_FIELDS = frozenset([
    "wsi_final_score", "lia_score", "match_percentage", "red_flags",
    "cpf", "current_salary", "desired_salary", "diversity_race_ethnicity",
    "diversity_disability", "diversity_lgbtqia", "is_private",
    "recruiter_notes", "rejection_code",
])


@tool_handler("candidate_self_service", require_company=True)
async def _get_application_status(**kwargs: Any) -> dict[str, Any]:
    candidate_id: str = kwargs.get("candidate_id", "")
    vacancy_id: str = kwargs.get("vacancy_id", "")
    company_id: str = kwargs.get("company_id", "")

    if not candidate_id or not vacancy_id:
        return {"success": False, "message": "candidate_id e vacancy_id são obrigatórios."}

    try:
        from app.shared.rails_client import rails_get
        data = await rails_get(
            f"/v1/candidate-portal/status",
            params={"candidate_id": candidate_id, "vacancy_id": vacancy_id},
            company_id=company_id,
        )
        # Strip forbidden fields before returning to LLM
        safe_data = {k: v for k, v in data.items() if k not in _FORBIDDEN_FIELDS}
        logger.info(
            "[CSS Tool] get_application_status candidate_id=%s vacancy_id=%s stage=%s",
            candidate_id, vacancy_id, safe_data.get("stage_name"),
        )
        return {"success": True, "data": safe_data}
    except Exception as exc:
        logger.error("[CSS Tool] get_application_status error: %s", exc)
        return {"success": False, "message": "Informação não disponível no momento."}


get_application_status = ToolDefinition(
    name="get_application_status",
    description=(
        "Retorna o status atual da candidatura: etapa no pipeline, "
        "data de entrada na etapa, título da vaga e próximos passos. "
        "Use quando o candidato perguntar sobre seu status ou andamento."
    ),
    parameters={
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string", "description": "ID do candidato (do token JWT)"},
            "vacancy_id": {"type": "string", "description": "ID da vaga (do token JWT)"},
        },
        "required": ["candidate_id", "vacancy_id"],
    },
    function=_get_application_status,
)
