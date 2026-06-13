import asyncio
import json
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_CACHE_TTL = 300  # 5 min


def _cache_key(role: str, resource: str, action: str) -> str:
    return f"rbac:scope:{role}:{resource}:{action}"


async def _resolve_maybe_coro(obj):
    """
    Resolve obj if it is a coroutine (AsyncMock compat in tests).
    In real SQLAlchemy, scalars() and first() are sync.
    In test mocks using AsyncMock they return coroutines.
    """
    if asyncio.iscoroutine(obj):
        return await obj
    return obj


class ScopeFilterService:
    """
    Consulta role_scope_filters para verificar se (role, resource, action) e permitido.

    Fail-closed: qualquer duvida -> False.
    Cache Redis com TTL de 5 min.

    Sprint C 2026-06-13.
    """

    async def is_allowed(
        self,
        role: str,
        resource: str,
        action: str,
        db: "AsyncSession",
    ) -> bool:
        """
        Verifica se role pode executar action em resource.

        Returns:
            True se permitido explicitamente.
            False se negado explicitamente ou nao encontrado (fail-closed).
        """
        if not role or not resource or not action:
            return False

        # 1. Try Redis cache
        cached = await self._cache_get(_cache_key(role, resource, action))
        if cached is not None:
            return cached

        # 2. DB lookup
        try:
            from sqlalchemy import select, and_
            from lia_models.role_scope_filter import RoleScopeFilter

            stmt = select(RoleScopeFilter).where(
                and_(
                    RoleScopeFilter.role == role,
                    RoleScopeFilter.resource == resource,
                    RoleScopeFilter.action == action,
                )
            )
            exec_result = await db.execute(stmt)
            # _resolve_maybe_coro handles both sync SQLAlchemy and AsyncMock in tests
            scalars_obj = await _resolve_maybe_coro(exec_result.scalars())
            result = await _resolve_maybe_coro(scalars_obj.first())

            if result is None:
                allowed = False
            else:
                allowed = bool(result.allowed)

            await self._cache_set(_cache_key(role, resource, action), allowed)
            return allowed

        except Exception as exc:
            logger.warning(
                "[ScopeFilterService] DB lookup failed (fail-closed): %s", exc
            )
            return False

    async def invalidate_cache(self, role=None) -> None:
        """Invalida cache de um role (ou todo o cache RBAC)."""
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(_REDIS_URL, decode_responses=True)
            star = "*"
            pattern = f"rbac:scope:{role or star}:*"
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
            await client.aclose()
        except Exception as exc:
            logger.debug("[ScopeFilterService] cache invalidation failed: %s", exc)

    async def _cache_get(self, key: str):
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(_REDIS_URL, decode_responses=True)
            raw = await client.get(key)
            await client.aclose()
            if raw is not None:
                return json.loads(raw)
        except Exception:
            pass
        return None

    async def _cache_set(self, key: str, value: bool) -> None:
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(_REDIS_URL, decode_responses=True)
            await client.setex(key, _CACHE_TTL, json.dumps(value))
            await client.aclose()
        except Exception:
            pass


_scope_filter_service = None


def get_scope_filter_service() -> "ScopeFilterService":
    global _scope_filter_service
    if _scope_filter_service is None:
        _scope_filter_service = ScopeFilterService()
    return _scope_filter_service
