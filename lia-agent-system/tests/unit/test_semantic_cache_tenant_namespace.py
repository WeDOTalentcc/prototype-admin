"""
Sentinel test for Task #1144 — Redis tenant-namespace contract.

Guards every Redis-touching module against regressing to a non-namespaced
key. The single most important guarantee: the SAME message routed from two
different ``company_id`` values MUST produce two distinct Redis keys.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.orchestrator.memory.semantic_cache import _cache_key as semantic_cache_key
from app.shared.cache_strategy import CacheDomain, CacheStrategy
from app.shared.exceptions.tenant_errors import InvalidCompanyIdError
from app.shared.prompt_experiment import PromptExperiment, PromptVariant
from app.shared.security.tenant_redis_namespace import (
    normalize_company_id,
    tenant_namespaced_key,
)
from app.shared.session_bridge import SessionBridge

_TENANT_A = "00000000-0000-4000-a000-000000000001"
_TENANT_B = "00000000-0000-4000-a000-000000000002"


# ---------------------------------------------------------------------------
# Canonical helper
# ---------------------------------------------------------------------------


def test_helper_rejects_invalid_company_id() -> None:
    for bad in (None, "", "default", "none", "null", "undefined", "system", "anonymous"):
        with pytest.raises(InvalidCompanyIdError):
            normalize_company_id(bad)


def test_helper_builds_canonical_shape() -> None:
    key = tenant_namespaced_key("prefix", _TENANT_A, "suffix")
    assert key == f"prefix:{_TENANT_A}:suffix"
    parts = key.split(":")
    assert len(parts) >= 3
    assert parts[1] == _TENANT_A


# ---------------------------------------------------------------------------
# SemanticCache — Tier 2 route cache (the original cross-tenant poison path)
# ---------------------------------------------------------------------------


def test_semantic_cache_key_includes_company_id() -> None:
    key = semantic_cache_key(_TENANT_A, "criar uma vaga de backend pleno")
    assert key.startswith("route_cache:")
    assert f":{_TENANT_A}:" in key


def test_semantic_cache_same_message_different_tenants_distinct_keys() -> None:
    """The critical no-cache-poison invariant."""
    msg = "quantos candidatos temos no funil?"
    key_a = semantic_cache_key(_TENANT_A, msg)
    key_b = semantic_cache_key(_TENANT_B, msg)
    assert key_a != key_b, (
        "Same message from two tenants produced identical Redis key — "
        "Task #1144 contract violated (cross-tenant cache poisoning)."
    )


def test_semantic_cache_rejects_missing_company_id() -> None:
    with pytest.raises(InvalidCompanyIdError):
        semantic_cache_key("", "hello")
    with pytest.raises(InvalidCompanyIdError):
        semantic_cache_key(None, "hello")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SessionBridge
# ---------------------------------------------------------------------------


def test_session_bridge_key_is_tenant_namespaced() -> None:
    bridge = SessionBridge()
    key = bridge._key("sess-xyz", company_id=_TENANT_A)
    assert key == f"lia:session:{_TENANT_A}:sess-xyz"

    key_b = bridge._key("sess-xyz", company_id=_TENANT_B)
    assert key != key_b


# ---------------------------------------------------------------------------
# PromptExperiment
# ---------------------------------------------------------------------------


def test_prompt_experiment_key_includes_company_id() -> None:
    exp = PromptExperiment(
        experiment_id="wsi_summary",
        variants=[PromptVariant("control", "ctrl"), PromptVariant("v2", "v2")],
    )
    key = exp._redis_key("control", date(2026, 5, 16), company_id=_TENANT_A)
    assert key == f"prompt_exp:{_TENANT_A}:wsi_summary:control:2026-05-16"

    key_b = exp._redis_key("control", date(2026, 5, 16), company_id=_TENANT_B)
    assert key != key_b


# ---------------------------------------------------------------------------
# CacheStrategy
# ---------------------------------------------------------------------------


def test_cache_strategy_build_key_includes_company_id() -> None:
    key_a = CacheStrategy.build_key(
        CacheDomain.CANDIDATE_SEARCH, _TENANT_A, query="python"
    )
    key_b = CacheStrategy.build_key(
        CacheDomain.CANDIDATE_SEARCH, _TENANT_B, query="python"
    )
    assert key_a.startswith(f"lia:{CacheDomain.CANDIDATE_SEARCH.value}:{_TENANT_A}:")
    assert key_a != key_b


# ---------------------------------------------------------------------------
# CascadedRouter Tier-1 LRU — must also carry the tenant dimension
# ---------------------------------------------------------------------------


def test_cascaded_router_tier1_lru_key_includes_company_id() -> None:
    """In-process LRU cache must not collide across tenants either."""
    from app.orchestrator.routing.cascaded_router import CascadedRouter

    router = CascadedRouter.__new__(CascadedRouter)  # avoid __init__ side effects
    msg = "criar uma vaga de backend pleno"
    key_a = router._cache_key(msg, _TENANT_A)
    key_b = router._cache_key(msg, _TENANT_B)
    assert key_a != key_b
    assert key_a.startswith(f"{_TENANT_A}:")
    assert key_b.startswith(f"{_TENANT_B}:")


# ---------------------------------------------------------------------------
# Central key-shape gate (assert_tenant_namespaced_key)
# ---------------------------------------------------------------------------


def test_assert_tenant_namespaced_key_passes_for_valid_shapes() -> None:
    from app.shared.security.tenant_redis_namespace import (
        assert_tenant_namespaced_key,
    )
    # Should NOT raise nor record a violation. Crucially, the second case
    # uses a multi-segment prefix ("lia:session") — proves the validator
    # is no longer fooled by colonised prefixes (review fix).
    assert_tenant_namespaced_key(
        f"rl:{_TENANT_A}:user:u1:min",
        module="test", company_id=_TENANT_A, prefix="rl",
    )
    assert_tenant_namespaced_key(
        f"lia:session:{_TENANT_A}:sess-1",
        module="test", company_id=_TENANT_A, prefix="lia:session",
    )


def test_assert_tenant_namespaced_key_records_violation_for_bad_shape(monkeypatch) -> None:
    from app.shared.security import tenant_redis_namespace as trn

    seen: list[str] = []
    monkeypatch.setattr(
        trn,
        "record_namespace_violation",
        lambda module: seen.append(module),
    )
    # 2-segment legacy key (route_cache:<md5>) — missing tenant dimension.
    trn.assert_tenant_namespaced_key(
        "route_cache:deadbeef",
        module="legacy", company_id=_TENANT_A, prefix="route_cache",
    )
    # Wrong tenant — key embeds a DIFFERENT company_id than the caller expects.
    trn.assert_tenant_namespaced_key(
        f"lia:session:{_TENANT_B}:sess-1",
        module="wrong_tenant", company_id=_TENANT_A, prefix="lia:session",
    )
    assert seen == ["legacy", "wrong_tenant"]


# ---------------------------------------------------------------------------
# Scope coverage — modules out of scope must NOT emit raw Redis SET/GET.
# (scheduled_reports + tracing flagged in the Task #1144 spec for sweep.)
# ---------------------------------------------------------------------------


def test_no_raw_redis_set_in_out_of_scope_modules() -> None:
    """Belt-and-braces: scheduled_reports + tracing must stay key-free."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / "app"
    targets = [
        root / "jobs" / "scheduled_reports.py",
        root / "shared" / "tracing.py",
    ]
    for path in targets:
        if not path.exists():
            continue
        src = path.read_text(encoding="utf-8")
        for needle in (".set(", ".setex(", ".get(", ".hset("):
            # We tolerate the strings appearing inside comments/docstrings,
            # but they must not be invoked on a Redis client. Heuristic: a
            # Redis client variable is conventionally `redis_client`,
            # `_redis`, or `r = await self._get_redis()`. Assert none of
            # those patterns coincide with a key-emitting call.
            assert f"redis_client{needle}" not in src, (
                f"{path} emits a Redis op {needle!r} — must be tenant-namespaced"
            )
            assert f"self._redis{needle}" not in src, (
                f"{path} emits a Redis op {needle!r} on self._redis"
            )


# ---------------------------------------------------------------------------
# Task #1144 — TenantRedisProxy interceptor sentinel
# ---------------------------------------------------------------------------


class _FakeRedis:
    """Minimal duck-typed async Redis stub for proxy validation tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    async def set(self, key, value, **kw):
        self.calls.append(("set", (key, value), kw))
        return True

    async def get(self, key):
        self.calls.append(("get", (key,), {}))
        return None

    async def hset(self, key, *a, **kw):
        self.calls.append(("hset", (key, *a), kw))
        return 1

    async def rpush(self, key, *vals):
        self.calls.append(("rpush", (key, *vals), {}))
        return len(vals)


def test_proxy_blocks_legacy_2segment_key_in_prod(monkeypatch) -> None:
    """The proxy must reject ``route_cache:<md5>`` (2 segments) loudly."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.shared.security.tenant_redis_proxy import wrap_redis_client

    proxy = wrap_redis_client(_FakeRedis(), module="sentinel_test")

    import asyncio
    with pytest.raises(RuntimeError):
        asyncio.run(
            proxy.set("route_cache:deadbeef", "v")
        )


def test_proxy_allows_canonical_tenant_key(monkeypatch) -> None:
    """Canonical ``<prefix>:<cid>:<suffix>`` must pass through unchanged."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.shared.security.tenant_redis_proxy import wrap_redis_client

    fake = _FakeRedis()
    proxy = wrap_redis_client(fake, module="sentinel_test")
    key = tenant_namespaced_key("route_cache", _TENANT_A, "deadbeef")

    import asyncio
    asyncio.run(proxy.set(key, "v"))
    assert fake.calls == [("set", (key, "v"), {})]


def test_proxy_blocks_well_known_non_tenant_label_at_cid_position(
    monkeypatch,
) -> None:
    """Keys whose cid position is a forbidden literal must be rejected."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.shared.security.tenant_redis_proxy import wrap_redis_client

    proxy = wrap_redis_client(_FakeRedis(), module="sentinel_test")

    import asyncio
    with pytest.raises(RuntimeError):
        asyncio.run(
            proxy.set("route_cache:default:deadbeef", "v")
        )


def test_proxy_allows_slug_tenant_cid(monkeypatch) -> None:
    """Per CompanyId.parse, slug tenants (e.g. ``acme-corp``) are valid."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.shared.security.tenant_redis_proxy import wrap_redis_client

    fake = _FakeRedis()
    proxy = wrap_redis_client(fake, module="sentinel_test")

    import asyncio
    asyncio.run(
        proxy.set("route_cache:acme-corp:deadbeef", "v")
    )
    # Slug must pass through to the underlying client without raising.
    assert fake.calls == [("set", ("route_cache:acme-corp:deadbeef", "v"), {})]


def test_proxy_allows_slug_tenant_at_2segment_prefix(monkeypatch) -> None:
    """Slug tenants at parts[2] (e.g. ``lia:session:<slug>:<sid>``) pass."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.shared.security.tenant_redis_proxy import wrap_redis_client

    fake = _FakeRedis()
    proxy = wrap_redis_client(fake, module="sentinel_test")

    import asyncio
    asyncio.run(
        proxy.set("lia:session:acme-corp:sess-1", "v")
    )
    assert fake.calls == [
        ("set", ("lia:session:acme-corp:sess-1", "v"), {})
    ]
