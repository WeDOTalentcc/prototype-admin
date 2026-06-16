"""
Semantic Cache — cache Redis com TTL para resultados de roteamento.

Tier 1 do Cost Cascade Orchestrator:
  Hash MD5 da mensagem normalizada + ``company_id`` → resultado de rota
  cacheado no Redis. **Task #1144** introduziu o componente ``company_id``
  obrigatório no key — duas empresas com a mesma mensagem produzem chaves
  distintas (sem cache poison cross-tenant).

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
from app.shared.security.tenant_redis_namespace import (
    normalize_company_id,
    tenant_namespaced_key,
)
from app.shared.value_objects.company_id import CompanyId

logger = logging.getLogger(__name__)

_KEY_PREFIX = "route_cache"


def _cache_key(company_id: str | CompanyId, message: str) -> str:
    """Return tenant-namespaced cache key.

    Task #1144: ``company_id`` is mandatory. The validated form is embedded
    between the static prefix and the MD5 hash of the normalized message, so
    ``Tenant A`` and ``Tenant B`` asking the same question never collide.
    """
    normalized = message.lower().strip()
    digest = hashlib.md5(normalized.encode()).hexdigest()
    return tenant_namespaced_key(_KEY_PREFIX, company_id, digest)


async def _get_redis():
    # Task #1144 — wrap the raw async client with TenantRedisProxy so every
    # keyed op is gated through assert_tenant_namespaced_key BEFORE the
    # network round-trip. The proxy fails loud in production.
    from app.shared.security.tenant_redis_proxy import wrap_redis_client

    try:
        import redis.asyncio as aioredis
        client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
    except ImportError:
        try:
            import aioredis
            client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
        except ImportError:
            return None
    return wrap_redis_client(client, module="semantic_cache")


class SemanticCache:
    """
    Cache Redis de resultados de rota por hash de mensagem + tenant.

    Uso (Task #1144 — ``company_id`` é obrigatório em todas as operações):
        cache = SemanticCache()
        hit = await cache.get(company_id, message)
        if hit is None:
            result = await route_via_llm(message)
            await cache.set(company_id, message, result)
    """

    def __init__(self, ttl: int = settings.ROUTER_CACHE_TTL):
        self.ttl = ttl

    async def get(self, company_id: str | CompanyId, message: str) -> dict[str, Any] | None:
        """Retorna resultado cacheado ou None se ausente."""
        key = _cache_key(company_id, message)
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

    async def set(
        self,
        company_id: str | CompanyId,
        message: str,
        result: dict[str, Any],
    ) -> None:
        """Armazena resultado com TTL configurado."""
        key = _cache_key(company_id, message)
        try:
            redis = await _get_redis()
            if redis is None:
                return
            async with redis:
                await redis.setex(key, self.ttl, json.dumps(result, default=str))
        except Exception as exc:
            logger.debug("[SemanticCache] set falhou: %s", exc)

    async def invalidate(self, company_id: str | CompanyId, message: str) -> None:
        """Remove entrada específica do cache."""
        key = _cache_key(company_id, message)
        try:
            redis = await _get_redis()
            if redis is None:
                return
            async with redis:
                await redis.delete(key)
        except Exception as exc:
            logger.debug("[SemanticCache] invalidate falhou: %s", exc)

    async def flush_all(
        self,
        company_id: str | CompanyId | None = None,
        pattern: str | None = None,
    ) -> int:
        """Remove entradas do cache de rota.

        * Quando ``company_id`` é fornecido (recomendado), apenas as chaves
          desse tenant são removidas — modo seguro padrão.
        * Quando ``pattern`` é fornecido explicitamente, o caller assume
          responsabilidade pelo escopo (uso restrito a scripts de manutenção).
        * Quando ambos são ``None``, levanta ``ValueError`` para forçar
          decisão explícita e evitar flush cross-tenant acidental.
        """
        if pattern is None:
            if company_id is None:
                raise ValueError(
                    "flush_all requires either company_id (tenant-scoped) or "
                    "an explicit pattern (operational override)."
                )
            cid = normalize_company_id(company_id)
            pattern = f"{_KEY_PREFIX}:{cid}:*"
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
