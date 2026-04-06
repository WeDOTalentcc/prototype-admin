"""
Semantic Cache — cache Redis com TTL para resultados de roteamento.

Tier 1 do Cost Cascade Orchestrator:
  Hash MD5 da mensagem normalizada → resultado de rota cacheado no Redis.

Complementa o cache in-process (LRU dict) do CascadedRouter:
- In-process: O(1), sem latência de rede, não persistido entre reinicializações
- Redis: distribuído, persistido, compartilhado entre workers Celery/Uvicorn

TTL configurável via ROUTER_CACHE_TTL (padrão: 3600s).
"""
import hashlib
import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "route_cache"


def _cache_key(message: str) -> str:
    normalized = message.lower().strip()
    return f"{_KEY_PREFIX}:{hashlib.md5(normalized.encode()).hexdigest()}"


async def _get_redis():
    try:
        import redis.asyncio as aioredis
        return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except ImportError:
        try:
            import aioredis
            return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except ImportError:
            return None


class SemanticCache:
    """
    Cache Redis de resultados de rota por hash de mensagem.

    Uso:
        cache = SemanticCache()
        hit = await cache.get(message)
        if hit is None:
            result = await route_via_llm(message)
            await cache.set(message, result)
    """

    def __init__(self, ttl: int = settings.ROUTER_CACHE_TTL):
        self.ttl = ttl

    async def get(self, message: str) -> dict[str, Any] | None:
        """Retorna resultado cacheado ou None se ausente."""
        key = _cache_key(message)
        try:
            redis = await _get_redis()
            if redis is None:
                return None
            async with redis:
                raw = await redis.get(key)
                if raw:
                    return json.loads(raw)
        except Exception as exc:
            logger.debug("[SemanticCache] get falhou: %s", exc)
        return None

    async def set(self, message: str, result: dict[str, Any]) -> None:
        """Armazena resultado com TTL configurado."""
        key = _cache_key(message)
        try:
            redis = await _get_redis()
            if redis is None:
                return
            async with redis:
                await redis.setex(key, self.ttl, json.dumps(result, default=str))
        except Exception as exc:
            logger.debug("[SemanticCache] set falhou: %s", exc)

    async def invalidate(self, message: str) -> None:
        """Remove entrada específica do cache."""
        key = _cache_key(message)
        try:
            redis = await _get_redis()
            if redis is None:
                return
            async with redis:
                await redis.delete(key)
        except Exception as exc:
            logger.debug("[SemanticCache] invalidate falhou: %s", exc)

    async def flush_all(self, pattern: str = f"{_KEY_PREFIX}:*") -> int:
        """Remove todas as entradas do cache de rota. Retorna número de chaves removidas."""
        try:
            redis = await _get_redis()
            if redis is None:
                return 0
            async with redis:
                keys = await redis.keys(pattern)
                if keys:
                    return await redis.delete(*keys)
        except Exception as exc:
            logger.debug("[SemanticCache] flush_all falhou: %s", exc)
        return 0


# Singleton compartilhado
semantic_cache = SemanticCache()
