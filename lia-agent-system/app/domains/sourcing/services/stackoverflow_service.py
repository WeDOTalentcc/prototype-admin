"""
StackOverflow Careers Sourcing Service — busca especialistas via Stack Exchange API.

Acessa perfis de desenvolvedores no Stack Exchange (StackOverflow) por tag de
tecnologia, reputação mínima e localização. Usa circuit breaker para resiliência.

Referência API: https://api.stackexchange.com/docs
"""
import logging
import os
from typing import Any

import httpx

from app.shared.resilience.circuit_breaker import circuit_breaker
from lia_config.config import settings

logger = logging.getLogger(__name__)

SO_API_BASE = "https://api.stackexchange.com/2.3"
SO_API_KEY = os.environ.get("STACKOVERFLOW_API_KEY", "")


async def _so_search_fallback(self, *args, **kwargs) -> dict[str, Any]:
    logger.warning("[StackOverflowService][CB] Circuit aberto — retornando vazio")
    return {"items": [], "has_more": False, "quota_remaining": 0}


class StackOverflowService:
    """
    Cliente para Stack Exchange API v2.3 com foco em talent sourcing.

    Permite buscar usuários por tag de expertise, reputação mínima e localização.
    """

    def __init__(self) -> None:
        self.base_url = SO_API_BASE
        self.api_key = SO_API_KEY
        self.timeout = httpx.Timeout(settings.HTTP_TIMEOUT_STACKOVERFLOW_SECONDS, connect=settings.HTTP_TIMEOUT_STACKOVERFLOW_CONNECT_SECONDS)  # UC-P2-12

    def _get_common_params(self) -> dict[str, str]:
        params: dict[str, str] = {"site": "stackoverflow"}
        if self.api_key:
            params["key"] = self.api_key
        return params

    @circuit_breaker("stackoverflow_api", failure_threshold=3, recovery_timeout=30.0, fallback=_so_search_fallback)
    async def search_users_by_tag(
        self,
        tag: str,
        min_reputation: int = 1000,
        location: str = "",
        limit: int = 30,
    ) -> dict[str, Any]:
        """
        Busca usuários do StackOverflow especializados em uma tag, via top answerers.

        Estratégia correta para a Stack Exchange API:
        1. GET /tags/{tag}/top-answerers/all_time — retorna user_ids dos top respondedores
           desta tag (endpoint dedicado para filtro por tag, ao contrário de /users)
        2. GET /users/{ids} — enriquece com perfil completo (reputação, localização, etc.)
        3. Filtra por min_reputation e localização opcional.

        Nota: /users?tagged= IGNORA o parâmetro na API Stack Exchange. Usar top-answerers
        é a abordagem correta e documentada para tag-based user search.

        Args:
            tag: Tag de tecnologia (ex: "python", "react", "kubernetes").
            min_reputation: Reputação mínima (filtro de qualidade, padrão: 1000).
            location: Filtro de localização livre (match no campo location do perfil).
            limit: Máximo de resultados (1-100).

        Returns:
            Dict com lista de perfis de especialistas filtrados pela tag solicitada.
        """
        limit = min(max(1, limit), 100)
        logger.info(
            "[StackOverflowService] Buscando top answerers: tag=%s min_rep=%d location=%s limit=%d",
            tag, min_reputation, location, limit,
        )

        # Passo 1: obter top answerers para a tag (retorna usuários reais da tag)
        params_ta = self._get_common_params()
        params_ta["pagesize"] = str(min(limit * 2, 100))  # Pegar extras para compensar filtragem

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp_ta = await client.get(
                    f"{self.base_url}/tags/{tag}/top-answerers/all_time",
                    params=params_ta,
                )
                resp_ta.raise_for_status()
                ta_data = resp_ta.json()
            except httpx.HTTPStatusError as e:
                logger.warning("[StackOverflowService] top-answerers falhou para tag '%s': %s", tag, e)
                ta_data = {"items": []}

        answerer_items = ta_data.get("items", [])
        if not answerer_items:
            logger.info("[StackOverflowService] Nenhum top-answerer encontrado para tag='%s'", tag)
            return {"items": [], "has_more": False, "quota_remaining": ta_data.get("quota_remaining", 0), "total_found": 0, "tag": tag}

        # Passo 2: coletar user_ids dos top answerers
        user_ids = [str(item["user"]["user_id"]) for item in answerer_items if "user" in item]
        if not user_ids:
            return {"items": [], "has_more": False, "quota_remaining": 0, "total_found": 0, "tag": tag}

        # Passo 3: enriquecer com perfis completos via /users/{ids}
        ids_str = ";".join(user_ids[:100])
        params_users = self._get_common_params()
        params_users.update({
            "sort": "reputation",
            "order": "desc",
            "pagesize": "100",
        })

        profiles = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp_users = await client.get(
                    f"{self.base_url}/users/{ids_str}",
                    params=params_users,
                )
                resp_users.raise_for_status()
                users_data = resp_users.json()
            except httpx.HTTPStatusError as e:
                logger.warning("[StackOverflowService] Enriquecimento de perfis falhou: %s", e)
                users_data = {"items": []}

        # Construir mapa answer_score por user_id (métricas da tag)
        answerer_score_map: dict[int, dict] = {}
        for item in answerer_items:
            if "user" in item:
                uid = item["user"]["user_id"]
                answerer_score_map[uid] = {
                    "answer_score": item.get("answer_score", 0),
                    "answer_count": item.get("answer_count", 0),
                }

        # Filtrar por min_reputation e localização
        for user in users_data.get("items", []):
            reputation = user.get("reputation", 0)
            if reputation < min_reputation:
                continue
            if location:
                loc_lower = location.lower()
                user_location = (user.get("location") or "").lower()
                if loc_lower not in user_location:
                    continue

            uid = user.get("user_id")
            tag_metrics = answerer_score_map.get(uid, {})
            profiles.append({
                "user_id": uid,
                "display_name": user.get("display_name", ""),
                "reputation": reputation,
                "location": user.get("location", ""),
                "website_url": user.get("website_url", ""),
                "link": user.get("link", ""),
                "profile_image": user.get("profile_image", ""),
                "badge_counts": user.get("badge_counts", {}),
                "accept_rate": user.get("accept_rate"),
                "answer_count": user.get("answer_count", 0),
                "question_count": user.get("question_count", 0),
                "last_access_date": user.get("last_access_date"),
                "creation_date": user.get("creation_date"),
                "tag_answer_score": tag_metrics.get("answer_score", 0),
                "tag_answer_count": tag_metrics.get("answer_count", 0),
                "sourced_via_tag": tag,  # Confirma que vem da tag solicitada
            })
            if len(profiles) >= limit:
                break

        return {
            "items": profiles,
            "has_more": ta_data.get("has_more", False),
            "quota_remaining": users_data.get("quota_remaining", ta_data.get("quota_remaining", 0)),
            "total_found": len(profiles),
            "tag": tag,
        }

    async def get_user_top_tags(self, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        """
        Obtém as top tags de um usuário SO (indica áreas de expertise).

        Args:
            user_id: ID numérico do usuário no StackOverflow.
            limit: Número máximo de tags.

        Returns:
            Lista de tags com score de respostas e perguntas.
        """
        params = self._get_common_params()
        params["pagesize"] = str(min(limit, 100))

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/users/{user_id}/tags",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                logger.warning("[StackOverflowService] Erro ao buscar tags de user %d: %s", user_id, e)
                return []

        tags = []
        for item in data.get("items", []):
            tags.append({
                "tag_name": item.get("tag_name", ""),
                "answer_score": item.get("answer_score", 0),
                "answer_count": item.get("answer_count", 0),
                "question_score": item.get("question_score", 0),
                "question_count": item.get("question_count", 0),
            })

        return tags

    async def get_user_answers(
        self, user_id: int, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Obtém as top respostas de um usuário SO para avaliar qualidade técnica.

        Args:
            user_id: ID do usuário.
            limit: Número máximo de respostas.

        Returns:
            Lista de respostas com score e body resumido.
        """
        params = self._get_common_params()
        params.update({
            "sort": "votes",
            "order": "desc",
            "pagesize": str(min(limit, 30)),
            "filter": "withbody",
        })

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/users/{user_id}/answers",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                logger.warning("[StackOverflowService] Erro ao buscar answers de user %d: %s", user_id, e)
                return []

        answers = []
        for item in data.get("items", []):
            body = item.get("body", "")
            answers.append({
                "answer_id": item.get("answer_id"),
                "score": item.get("score", 0),
                "is_accepted": item.get("is_accepted", False),
                "question_id": item.get("question_id"),
                "body_preview": body[:500] if body else "",
                "creation_date": item.get("creation_date"),
            })

        return answers


stackoverflow_service = StackOverflowService()
