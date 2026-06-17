"""Centralised Redis operation interceptor for Task #1144.

Wraps a ``redis.asyncio`` client (or any duck-typed equivalent) so that every
key-bearing call (``get``, ``set``, ``setex``, ``delete``, ``hset``, ``hget``,
``rpush``, ``lrange``, ``expire``, ``pexpire``, ``zadd``, ``zcard``, ...) is
gated through :func:`assert_tenant_namespaced_key` BEFORE it touches the
network.

Why a wrapper instead of monkey-patching ``redis.asyncio``:
* Importing ``redis.asyncio`` is lazy in many callsites; monkey-patching
  would race with import order.
* The wrapper preserves every other method via ``__getattr__`` delegation.
* The wrapper is opt-in per callsite (``wrap_redis_client(client, module)``)
  so legacy modules can be migrated incrementally without breaking startup.

Production semantics:
* Each violation increments
  ``lia_redis_tenant_namespace_violation_total{module}`` and (in production)
  raises ``RuntimeError`` via :func:`record_namespace_violation`. The wrapper
  does NOT swallow that exception — the underlying op is never executed.
* Pipeline support: ``pipeline()`` returns a wrapped pipeline whose queued
  commands are validated when the operation is queued (not at ``execute``).
"""
from __future__ import annotations

import logging
from typing import Any

from app.shared.exceptions.tenant_errors import InvalidCompanyIdError
from app.shared.security.tenant_redis_namespace import (
    assert_tenant_namespaced_key,
)
from app.shared.value_objects.company_id import CompanyId

logger = logging.getLogger(__name__)

# Methods whose first positional arg is a Redis key (Task #1144 enforced set).
_KEY_METHODS: frozenset[str] = frozenset({
    "get", "set", "setex", "psetex", "getset",
    "delete", "unlink",
    "expire", "pexpire", "expireat", "ttl", "persist",
    "incr", "decr", "incrby", "decrby",
    "hset", "hget", "hgetall", "hdel", "hincrby", "hmset", "hmget",
    "rpush", "lpush", "lrange", "lpop", "rpop", "llen",
    "sadd", "srem", "smembers", "sismember",
    "zadd", "zrem", "zcard", "zrange", "zremrangebyscore", "zrangebyscore",
})


class TenantRedisProxy:
    """Validates every keyed Redis op before delegating to the real client.

    Construct via :func:`wrap_redis_client`. The proxy enforces that the
    first positional argument of any method in :data:`_KEY_METHODS` matches
    the canonical ``<prefix>:<company_id>:<suffix>`` shape — when it does
    not, the central gate records a Prometheus violation and (in production)
    raises ``RuntimeError`` BEFORE the op is dispatched.
    """

    __slots__ = ("_client", "_module")

    def __init__(self, client: Any, *, module: str) -> None:
        self._client = client
        self._module = module

    def _validate(self, method_name: str, key: Any) -> None:
        if not isinstance(key, (str, bytes)):
            return
        k = key.decode() if isinstance(key, bytes) else key
        # We don't know the tenant at the call site; use a substring check
        # that requires at least one ``:`` after the first segment AND a
        # 2nd segment that is not one of the well-known non-tenant labels.
        # The canonical helper (`tenant_namespaced_key`) is the path of
        # truth; this is a defence-in-depth net for keys built ad hoc.
        parts = k.split(":")
        if len(parts) < 3:
            # 2-segment legacy shape (e.g. route_cache:<md5>) — no room for
            # a cid segment. Reject via the canonical helper.
            assert_tenant_namespaced_key(
                k,
                module=f"{self._module}.{method_name}",
                company_id=parts[0] if parts else "",
            )
            return

        # Canonical contract (CompanyId.parse): cid may be a UUID v4 OR a
        # slug (``^[a-z][a-z0-9_-]{2,63}$``), and MUST NOT be a forbidden
        # literal (``default``/``none``/``null``/``undefined``/``system``/
        # ``anonymous``). cid lives at parts[1] for short prefixes
        # (``route_cache:<cid>:<sfx>``) OR at parts[2] for 2-segment
        # prefixes (``lia:session:<cid>:<sid>``, ``lia:<domain>:<cid>:<hash>``).
        cid_positions = [parts[1]]
        if len(parts) >= 4:
            cid_positions.append(parts[2])

        def _is_valid_cid(s: str) -> bool:
            try:
                CompanyId.parse(s)
            except InvalidCompanyIdError:
                return False
            return True

        if not any(_is_valid_cid(p) for p in cid_positions):
            assert_tenant_namespaced_key(
                k,
                module=f"{self._module}.{method_name}",
                company_id=parts[1],
            )

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._client, name)
        if name not in _KEY_METHODS:
            return attr

        def _wrapped(*args, **kwargs):
            if args:
                self._validate(name, args[0])
            return attr(*args, **kwargs)

        return _wrapped

    # Pipelines need their own proxy so queued ops are validated too.
    def pipeline(self, *args, **kwargs):
        pipe = self._client.pipeline(*args, **kwargs)
        return TenantRedisProxy(pipe, module=f"{self._module}.pipeline")

    # Async-context-manager passthrough — redis.asyncio clients are
    # commonly used as ``async with redis: ...`` (auto-closes on exit).
    # Delegate to the underlying client's hooks so callers that wrap the
    # raw client work unchanged.
    async def __aenter__(self) -> "TenantRedisProxy":
        aenter = getattr(self._client, "__aenter__", None)
        if aenter is not None:
            await aenter()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        aexit = getattr(self._client, "__aexit__", None)
        if aexit is not None:
            await aexit(exc_type, exc, tb)

    async def aclose(self) -> None:
        close = getattr(self._client, "aclose", None) or getattr(
            self._client, "close", None
        )
        if close is not None:
            res = close()
            if hasattr(res, "__await__"):
                await res


def wrap_redis_client(client: Any, *, module: str) -> TenantRedisProxy:
    """Return a :class:`TenantRedisProxy` wrapping ``client``.

    Always pass a stable ``module`` label — it becomes the Prometheus
    ``{module}`` dimension on
    ``lia_redis_tenant_namespace_violation_total``.
    """
    return TenantRedisProxy(client, module=module)


__all__ = ["TenantRedisProxy", "wrap_redis_client"]
