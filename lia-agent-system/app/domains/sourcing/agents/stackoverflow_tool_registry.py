"""
StackOverflow Sourcing Tool Registry — busca de especialistas via Stack Exchange API.

Expõe tools para StackOverflowSourcingAgent:
- so_search_experts: busca especialistas por tag, reputação e localização
- so_get_user_tags: top tags de expertise de um usuário
- so_get_user_answers: top respostas de um usuário (avaliação de qualidade técnica)
"""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_SO_TOOL_DEFINITIONS: list[ToolDefinition] = []


@tool_handler("stackoverflow")
async def _wrap_so_search_experts(**kwargs: Any) -> dict[str, Any]:
    """Busca especialistas no StackOverflow por tag de tecnologia."""
    logger.info("[so_tools] so_search_experts called: %s", list(kwargs.keys()))
    from app.domains.sourcing.services.stackoverflow_service import stackoverflow_service
    from app.shared.compliance.fairness_guard import FairnessGuard

    tag = kwargs.get("tag", "")
    min_reputation = int(kwargs.get("min_reputation", 1000))
    location = kwargs.get("location", "")
    limit = min(int(kwargs.get("limit", 30)), 100)

    if not tag:
        return {"success": False, "data": {}, "message": "Parâmetro 'tag' é obrigatório (ex: python, react)."}

    query_str = f"{tag} {location}"
    try:
        _fg = FairnessGuard()
        _fg_result = _fg.check(query_str)
        if _fg_result.is_blocked:
            return {
                "success": False,
                "data": {},
                "message": _fg_result.educational_message or "Busca bloqueada por critério discriminatório.",
            }
    except Exception as _fg_exc:
        logger.debug("[so_tools] FairnessGuard check skipped: %s", _fg_exc)

    result = await stackoverflow_service.search_users_by_tag(
        tag=tag,
        min_reputation=min_reputation,
        location=location,
        limit=limit,
    )

    items = result.get("items", [])
    return {
        "success": True,
        "data": {
            "experts": items,
            "total_found": result.get("total_found", len(items)),
            "has_more": result.get("has_more", False),
            "quota_remaining": result.get("quota_remaining"),
            "filters": {
                "tag": tag,
                "min_reputation": min_reputation,
                "location": location,
            },
        },
        "message": (
            f"{len(items)} especialista(s) encontrado(s) no StackOverflow"
            + f" para tag '{tag}'"
            + (f" com reputação ≥ {min_reputation}" if min_reputation > 0 else "")
            + (f" em '{location}'" if location else "")
            + "."
        ),
    }
_SO_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="so_search_experts",
        description=(
            "Busca especialistas no StackOverflow por tag de tecnologia (ex: python, react, kubernetes). "
            "Filtra por reputação mínima e localização. "
            "Ideal para vagas técnicas que requerem expertise de nicho."
        ),
        parameters={
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "Tag de tecnologia (ex: python, react, machine-learning, docker)",
                },
                "min_reputation": {
                    "type": "integer",
                    "description": "Reputação mínima no SO (padrão: 1000; uso profissional: 2000+)",
                    "default": 1000,
                },
                "location": {
                    "type": "string",
                    "description": "Filtro de localização (ex: Brazil, São Paulo)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Máximo de resultados (1-100, padrão: 30)",
                    "default": 30,
                },
            },
            "required": ["tag"],
        },
        output_schema=ToolOutput,
        function=_wrap_so_search_experts,
    )
)


@tool_handler("stackoverflow")
async def _wrap_so_get_user_tags(**kwargs: Any) -> dict[str, Any]:
    """Obtém top tags de expertise de um usuário StackOverflow."""
    logger.info("[so_tools] so_get_user_tags called: %s", list(kwargs.keys()))
    from app.domains.sourcing.services.stackoverflow_service import stackoverflow_service
    user_id = kwargs.get("user_id")
    if not user_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'user_id' é obrigatório."}

    limit = min(int(kwargs.get("limit", 10)), 100)
    tags = await stackoverflow_service.get_user_top_tags(int(user_id), limit=limit)

    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "top_tags": tags,
            "count": len(tags),
        },
        "message": f"{len(tags)} tag(s) de expertise encontrada(s) para o usuário {user_id}.",
    }
_SO_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="so_get_user_tags",
        description=(
            "Obtém as principais tags de expertise de um usuário StackOverflow: "
            "score de respostas e contagem por tecnologia. "
            "Use após so_search_experts para avaliar profundidade técnica."
        ),
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID numérico do usuário no StackOverflow",
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de tags (padrão: 10)",
                    "default": 10,
                },
            },
            "required": ["user_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_so_get_user_tags,
    )
)


@tool_handler("stackoverflow")
async def _wrap_so_get_user_answers(**kwargs: Any) -> dict[str, Any]:
    """Obtém top respostas de um usuário SO para avaliar qualidade técnica."""
    logger.info("[so_tools] so_get_user_answers called: %s", list(kwargs.keys()))
    from app.domains.sourcing.services.stackoverflow_service import stackoverflow_service
    user_id = kwargs.get("user_id")
    if not user_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'user_id' é obrigatório."}

    limit = min(int(kwargs.get("limit", 5)), 30)
    answers = await stackoverflow_service.get_user_answers(int(user_id), limit=limit)

    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "top_answers": answers,
            "count": len(answers),
        },
        "message": f"{len(answers)} resposta(s) de destaque encontrada(s) para o usuário {user_id}.",
    }
_SO_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="so_get_user_answers",
        description=(
            "Obtém as melhores respostas de um usuário StackOverflow (por votos). "
            "Permite avaliar profundidade e qualidade técnica do candidato."
        ),
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID numérico do usuário no StackOverflow",
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de respostas (padrão: 5)",
                    "default": 5,
                },
            },
            "required": ["user_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_so_get_user_answers,
    )
)

_SO_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in _SO_TOOL_DEFINITIONS}


def get_stackoverflow_tools() -> list[ToolDefinition]:
    return list(_SO_TOOL_DEFINITIONS)
