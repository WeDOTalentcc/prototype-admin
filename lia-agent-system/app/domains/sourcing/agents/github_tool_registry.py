"""
GitHub Sourcing Tool Registry — busca de desenvolvedores via GitHub API.

Expõe tools para GithubSourcingAgent:
- github_search_developers: busca por linguagem, localização, métricas
- github_get_profile: perfil detalhado de um developer
- github_get_repos: repositórios públicos de um developer
"""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_GITHUB_TOOL_DEFINITIONS: list[ToolDefinition] = []


@tool_handler("github")
async def _wrap_github_search_developers(**kwargs: Any) -> dict[str, Any]:
    """Busca desenvolvedores no GitHub por linguagem, localização e métricas."""
    logger.info("[github_tools] github_search_developers called: %s", list(kwargs.keys()))
    from app.domains.sourcing.services.github_service import github_service
    from app.shared.compliance.fairness_guard import FairnessGuard

    language = kwargs.get("language", "")
    location = kwargs.get("location", "")
    min_repos = int(kwargs.get("min_repos", 5))
    min_followers = int(kwargs.get("min_followers", 0))
    keywords = kwargs.get("keywords", [])
    limit = min(int(kwargs.get("limit", 30)), 100)

    # FairnessGuard: verificar query
    query_str = f"{language} {location} {' '.join(keywords or [])}"
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
        logger.debug("[github_tools] FairnessGuard check skipped: %s", _fg_exc)

    result = await github_service.search_developers(
        language=language,
        location=location,
        min_repos=min_repos,
        min_followers=min_followers,
        keywords=keywords if isinstance(keywords, list) else [],
        limit=limit,
    )

    items = result.get("items", [])
    return {
        "success": True,
        "data": {
            "developers": items,
            "total_count": result.get("total_count", len(items)),
            "incomplete_results": result.get("incomplete_results", False),
            "filters": {
                "language": language,
                "location": location,
                "min_repos": min_repos,
                "min_followers": min_followers,
            },
        },
        "message": (
            f"{len(items)} desenvolvedor(es) encontrado(s) no GitHub"
            + (f" com linguagem '{language}'" if language else "")
            + (f" em '{location}'" if location else "")
            + "."
        ),
    }
_GITHUB_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="github_search_developers",
        description=(
            "Busca desenvolvedores no GitHub por linguagem de programação, "
            "localização e métricas (repositórios, seguidores). "
            "Use para sourcing de perfis tech que não estão no banco interno."
        ),
        parameters={
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "Linguagem principal (ex: python, typescript, rust, kotlin)",
                },
                "location": {
                    "type": "string",
                    "description": "Localização (ex: Brazil, São Paulo, Remote)",
                },
                "min_repos": {
                    "type": "integer",
                    "description": "Número mínimo de repositórios públicos (padrão: 5)",
                    "default": 5,
                },
                "min_followers": {
                    "type": "integer",
                    "description": "Número mínimo de seguidores (padrão: 0)",
                    "default": 0,
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Termos adicionais para busca (ex: ['machine-learning', 'open-source'])",
                },
                "limit": {
                    "type": "integer",
                    "description": "Máximo de resultados (1-100, padrão: 30)",
                    "default": 30,
                },
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_github_search_developers,
    )
)


@tool_handler("github")
async def _wrap_github_get_profile(**kwargs: Any) -> dict[str, Any]:
    """Obtém perfil detalhado de um desenvolvedor GitHub."""
    logger.info("[github_tools] github_get_profile called: %s", list(kwargs.keys()))
    from app.domains.sourcing.services.github_service import github_service
    login = kwargs.get("login", "")
    if not login:
        return {"success": False, "data": {}, "message": "Parâmetro 'login' é obrigatório."}

    profile = await github_service.get_user_profile(login)
    if not profile:
        return {"success": False, "data": {}, "message": f"Perfil '{login}' não encontrado no GitHub."}

    return {
        "success": True,
        "data": profile,
        "message": f"Perfil GitHub de '{profile.get('name') or login}' obtido com sucesso.",
    }
_GITHUB_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="github_get_profile",
        description=(
            "Obtém perfil detalhado de um desenvolvedor no GitHub: bio, empresa, "
            "localização, número de repositórios, seguidores e hireable status."
        ),
        parameters={
            "type": "object",
            "properties": {
                "login": {
                    "type": "string",
                    "description": "Username do GitHub (ex: torvalds, gvanrossum)",
                },
            },
            "required": ["login"],
        },
        output_schema=ToolOutput,
        function=_wrap_github_get_profile,
    )
)


@tool_handler("github")
async def _wrap_github_get_repos(**kwargs: Any) -> dict[str, Any]:
    """Lista repositórios públicos de um desenvolvedor GitHub."""
    logger.info("[github_tools] github_get_repos called: %s", list(kwargs.keys()))
    from app.domains.sourcing.services.github_service import github_service
    login = kwargs.get("login", "")
    if not login:
        return {"success": False, "data": {}, "message": "Parâmetro 'login' é obrigatório."}

    limit = min(int(kwargs.get("limit", 10)), 100)
    repos = await github_service.get_user_repos(login, limit=limit)

    return {
        "success": True,
        "data": {
            "login": login,
            "repositories": repos,
            "count": len(repos),
        },
        "message": f"{len(repos)} repositório(s) encontrado(s) para '{login}'.",
    }
_GITHUB_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="github_get_repos",
        description=(
            "Lista repositórios públicos de um desenvolvedor GitHub: linguagem, "
            "estrelas, forks e tópicos. Útil para avaliar expertise e contribuições."
        ),
        parameters={
            "type": "object",
            "properties": {
                "login": {
                    "type": "string",
                    "description": "Username do GitHub",
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de repositórios (padrão: 10)",
                    "default": 10,
                },
            },
            "required": ["login"],
        },
        output_schema=ToolOutput,
        function=_wrap_github_get_repos,
    )
)

@tool_handler("github")
async def _wrap_github_get_contributions(**kwargs: Any) -> dict[str, Any]:
    """Obtém métricas de contribuição recente de um desenvolvedor GitHub via Events API."""
    logger.info("[github_tools] github_get_contributions called: %s", list(kwargs.keys()))
    from app.domains.sourcing.services.github_service import github_service
    login = kwargs.get("login", "")
    if not login:
        return {"success": False, "data": {}, "message": "Parâmetro 'login' é obrigatório."}

    days = min(int(kwargs.get("days", 90)), 90)  # GitHub API max 90 dias
    result = await github_service.get_user_contributions(login=login, days=days)

    if result.get("error"):
        return {"success": False, "data": {}, "message": result["error"]}

    metrics = result.get("contribution_metrics", {})
    return {
        "success": True,
        "data": result,
        "message": (
            f"Contribuições de '{login}' nos últimos {days} dias: "
            f"{metrics.get('total_commits', 0)} commits, "
            f"{metrics.get('pull_requests_merged', 0)} PRs merged, "
            f"{metrics.get('repos_contributed_to', 0)} repo(s) contribuído(s)."
        ),
    }
_GITHUB_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="github_get_contributions",
        description=(
            "Obtém métricas de contribuição recente de um desenvolvedor GitHub: "
            "commits, pull requests (abertos/merged), issues criadas, code reviews "
            "e repositórios únicos onde contribuiu. "
            "Usa GitHub Events API (janela máxima: 90 dias de eventos públicos)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "login": {
                    "type": "string",
                    "description": "Username do GitHub",
                },
                "days": {
                    "type": "integer",
                    "description": "Janela de tempo em dias (máx: 90, padrão: 90)",
                    "default": 90,
                },
            },
            "required": ["login"],
        },
        output_schema=ToolOutput,
        function=_wrap_github_get_contributions,
    )
)

_GITHUB_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in _GITHUB_TOOL_DEFINITIONS}


def get_github_tools() -> list[ToolDefinition]:
    return list(_GITHUB_TOOL_DEFINITIONS)
