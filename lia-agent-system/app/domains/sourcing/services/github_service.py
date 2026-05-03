"""
GitHub Sourcing Service — integração com GitHub API para busca de desenvolvedores.

Busca perfis por linguagem de programação, repositórios públicos relevantes e
contagem de contribuições. Usa circuit breaker para resiliência.
"""
import logging
import os
from typing import Any

import httpx

from app.shared.resilience.circuit_breaker import circuit_breaker
from lia_config.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = (
    os.environ.get("GITHUB_TOKEN")
    or os.environ.get("Github")
    or os.environ.get("GITHUB_PAT_WEDOTALENT")
    or ""
)

_DEFAULT_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _get_headers() -> dict[str, str]:
    headers = dict(_DEFAULT_HEADERS)
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


async def _github_search_fallback(self, *args, **kwargs) -> dict[str, Any]:
    logger.warning("[GithubService][CB] Circuit aberto — retornando vazio")
    return {"items": [], "total_count": 0, "incomplete_results": True}


class GithubService:
    """
    Cliente para GitHub API v3 com foco em talent sourcing.

    Permite buscar desenvolvedores por linguagem, localização, número mínimo de
    repositórios e contagem de estrelas/contribuições recentes.
    """

    def __init__(self) -> None:
        self.base_url = GITHUB_API_BASE
        self.timeout = httpx.Timeout(settings.HTTP_TIMEOUT_GITHUB_SECONDS, connect=settings.HTTP_TIMEOUT_GITHUB_CONNECT_SECONDS)  # UC-P2-12

    @circuit_breaker("github_api", failure_threshold=3, recovery_timeout=30.0, fallback=_github_search_fallback)
    async def search_developers(
        self,
        language: str = "",
        location: str = "",
        min_repos: int = 5,
        min_followers: int = 0,
        keywords: list[str] | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """
        Busca desenvolvedores no GitHub.

        Args:
            language: Linguagem principal (ex: "python", "typescript").
            location: Localização (ex: "Brazil", "São Paulo").
            min_repos: Número mínimo de repositórios públicos.
            min_followers: Número mínimo de seguidores.
            keywords: Termos adicionais para busca.
            limit: Máximo de resultados (1-100).

        Returns:
            Dict com lista de perfis de desenvolvedores.
        """
        limit = min(max(1, limit), 100)
        query_parts: list[str] = ["type:user"]

        if language:
            query_parts.append(f"language:{language}")
        if location:
            query_parts.append(f"location:{location}")
        if min_repos > 0:
            query_parts.append(f"repos:>={min_repos}")
        if min_followers > 0:
            query_parts.append(f"followers:>={min_followers}")
        if keywords:
            for kw in keywords:
                query_parts.append(kw)

        query = " ".join(query_parts)
        logger.info("[GithubService] Buscando developers: query=%s limit=%d", query, limit)

        params = {
            "q": query,
            "per_page": limit,
            "sort": "repositories",
            "order": "desc",
        }

        async with httpx.AsyncClient(timeout=self.timeout, headers=_get_headers()) as client:
            resp = await client.get(f"{self.base_url}/search/users", params=params)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("items", [])
        profiles = []
        for item in items:
            profiles.append({
                "login": item.get("login", ""),
                "github_url": item.get("html_url", ""),
                "avatar_url": item.get("avatar_url", ""),
                "type": item.get("type", "User"),
                "score": item.get("score", 0),
            })

        return {
            "total_count": data.get("total_count", 0),
            "incomplete_results": data.get("incomplete_results", False),
            "items": profiles,
        }

    async def get_user_profile(self, login: str) -> dict[str, Any]:
        """
        Obtém perfil detalhado de um usuário GitHub.

        Args:
            login: Username do GitHub.

        Returns:
            Dict com dados do perfil incluindo bio, empresa, localização e métricas.
        """
        if not login:
            return {}

        logger.info("[GithubService] Buscando perfil: login=%s", login)
        async with httpx.AsyncClient(timeout=self.timeout, headers=_get_headers()) as client:
            try:
                resp = await client.get(f"{self.base_url}/users/{login}")
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                logger.warning("[GithubService] Erro ao buscar perfil %s: %s", login, e)
                return {}

        return {
            "login": data.get("login", ""),
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "bio": data.get("bio", ""),
            "company": data.get("company", ""),
            "location": data.get("location", ""),
            "blog": data.get("blog", ""),
            "github_url": data.get("html_url", ""),
            "public_repos": data.get("public_repos", 0),
            "followers": data.get("followers", 0),
            "following": data.get("following", 0),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "hireable": data.get("hireable"),
            "twitter_username": data.get("twitter_username", ""),
        }

    async def get_user_repos(
        self,
        login: str,
        limit: int = 10,
        sort: str = "updated",
    ) -> list[dict[str, Any]]:
        """
        Lista repositórios públicos de um usuário.

        Args:
            login: Username do GitHub.
            limit: Número máximo de repositórios.
            sort: Ordenação (updated, created, pushed, full_name).

        Returns:
            Lista de repositórios com métricas.
        """
        if not login:
            return []

        limit = min(max(1, limit), 100)
        logger.info("[GithubService] Listando repos: login=%s limit=%d", login, limit)

        async with httpx.AsyncClient(timeout=self.timeout, headers=_get_headers()) as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/users/{login}/repos",
                    params={"per_page": limit, "sort": sort, "type": "owner"},
                )
                resp.raise_for_status()
                repos = resp.json()
            except httpx.HTTPStatusError as e:
                logger.warning("[GithubService] Erro ao listar repos de %s: %s", login, e)
                return []

        result = []
        for repo in repos:
            result.append({
                "name": repo.get("name", ""),
                "description": repo.get("description", ""),
                "language": repo.get("language", ""),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "watchers": repo.get("watchers_count", 0),
                "topics": repo.get("topics", []),
                "url": repo.get("html_url", ""),
                "updated_at": repo.get("updated_at", ""),
                "pushed_at": repo.get("pushed_at", ""),
                "is_fork": repo.get("fork", False),
                "open_issues": repo.get("open_issues_count", 0),
                "size_kb": repo.get("size", 0),
            })

        return result

    async def get_user_contributions(
        self,
        login: str,
        days: int = 365,
    ) -> dict[str, Any]:
        """
        Obtém métricas de contribuição de um usuário via GitHub Events API.

        Usa /users/{login}/events para calcular:
        - Commits recentes (PushEvent)
        - Pull requests abertos/merged (PullRequestEvent)
        - Issues criadas (IssuesEvent)
        - Code reviews (PullRequestReviewEvent)
        - Repos únicos onde contribuiu

        Args:
            login: Username do GitHub.
            days: Janela de tempo em dias para eventos recentes (padrão: 365).
                  Nota: GitHub API retorna eventos dos últimos 90 dias (limite da API).

        Returns:
            Dict com métricas de contribuição.
        """
        if not login:
            return {"login": login, "contribution_metrics": {}, "error": "login obrigatório"}

        logger.info("[GithubService] Buscando contributions: login=%s days=%d", login, days)

        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=min(days, 90))

        events: list[dict] = []
        async with httpx.AsyncClient(timeout=self.timeout, headers=_get_headers()) as client:
            for page in range(1, 4):  # Máximo 3 páginas (300 eventos)
                try:
                    resp = await client.get(
                        f"{self.base_url}/users/{login}/events/public",
                        params={"per_page": 100, "page": page},
                    )
                    if resp.status_code == 404:
                        break
                    resp.raise_for_status()
                    page_events = resp.json()
                    if not page_events:
                        break
                    events.extend(page_events)
                    # GitHub não permite paginação além de 3 páginas para eventos
                    if len(page_events) < 100:
                        break
                except httpx.HTTPStatusError as e:
                    logger.warning("[GithubService] Erro ao buscar eventos de %s page=%d: %s", login, page, e)
                    break

        # Filtrar eventos dentro da janela de tempo
        recent_events = []
        for ev in events:
            created_at = ev.get("created_at", "")
            try:
                ev_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if ev_dt >= cutoff:
                    recent_events.append(ev)
            except (ValueError, AttributeError):
                continue

        # Contagens por tipo de evento
        push_events = [e for e in recent_events if e.get("type") == "PushEvent"]
        pr_events = [e for e in recent_events if e.get("type") == "PullRequestEvent"]
        issue_events = [e for e in recent_events if e.get("type") == "IssuesEvent"]
        review_events = [e for e in recent_events if e.get("type") == "PullRequestReviewEvent"]

        # Commits = soma dos commits em cada PushEvent
        total_commits = sum(
            len(e.get("payload", {}).get("commits", []))
            for e in push_events
        )

        # PRs merged/opened
        prs_opened = sum(
            1 for e in pr_events
            if e.get("payload", {}).get("action") in ("opened", "reopened")
        )
        prs_merged = sum(
            1 for e in pr_events
            if e.get("payload", {}).get("pull_request", {}).get("merged") is True
        )

        # Repos únicos onde contribuiu
        repos_contributed = list({e.get("repo", {}).get("name", "") for e in recent_events if e.get("repo")})

        return {
            "login": login,
            "contribution_window_days": min(days, 90),
            "contribution_metrics": {
                "total_commits": total_commits,
                "push_events": len(push_events),
                "pull_requests_opened": prs_opened,
                "pull_requests_merged": prs_merged,
                "issues_created": len(issue_events),
                "code_reviews": len(review_events),
                "repos_contributed_to": len(repos_contributed),
                "top_repos": repos_contributed[:5],
                "total_public_events": len(recent_events),
            },
            "note": (
                "Baseado em eventos públicos via GitHub Events API. "
                "Janela máxima: 90 dias (limite da API). "
                "Contribuições em repos privados não são visíveis."
            ),
        }


github_service = GithubService()
