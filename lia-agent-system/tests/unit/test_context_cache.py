"""
Unit tests for ContextCache (LOTE-006 / DIM-02).
TDD: 12 tests covering get/set/invalidate/stale/missing.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache.context_cache import ContextCache, DEFAULT_TTL


# ── helpers ───────────────────────────────────────────────────────────────

def _make_cache() -> tuple[ContextCache, AsyncMock]:
    redis = AsyncMock()
    return ContextCache(redis), redis


def _ts(offset_seconds: float = 0.0) -> str:
    return str((datetime.utcnow().timestamp()) + offset_seconds)


# ── get_with_ttl ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_fresh_returns_value():
    cache, redis = _make_cache()
    redis.get.return_value = json.dumps({"k": "v"})
    redis.hgetall.return_value = {"created_at": _ts(-10), "ttl": "300", "version": "1"}

    result = await cache.get_with_ttl("key1")
    assert result == {"k": "v"}


@pytest.mark.asyncio
async def test_get_missing_returns_none():
    cache, redis = _make_cache()
    redis.get.return_value = None

    assert await cache.get_with_ttl("key_missing") is None


@pytest.mark.asyncio
async def test_get_stale_deletes_and_returns_none():
    cache, redis = _make_cache()
    redis.get.return_value = json.dumps({"k": "v"})
    redis.hgetall.return_value = {"created_at": _ts(-400), "ttl": "300"}  # 400s old

    result = await cache.get_with_ttl("key_stale", ttl_seconds=300)
    assert result is None
    redis.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_corrupt_meta_deletes_and_returns_none():
    cache, redis = _make_cache()
    redis.get.return_value = json.dumps({"k": "v"})
    redis.hgetall.return_value = {}  # missing created_at

    result = await cache.get_with_ttl("key_corrupt")
    assert result is None
    redis.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_invalid_json_deletes_and_returns_none():
    cache, redis = _make_cache()
    redis.get.return_value = "not-json"
    redis.hgetall.return_value = {"created_at": _ts(-10), "ttl": "300"}

    result = await cache.get_with_ttl("key_badjson")
    assert result is None
    redis.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_respects_custom_ttl():
    cache, redis = _make_cache()
    redis.get.return_value = json.dumps({"k": "v"})
    # 70 seconds old, but custom TTL = 60 → stale
    redis.hgetall.return_value = {"created_at": _ts(-70), "ttl": "60"}

    result = await cache.get_with_ttl("key_custom", ttl_seconds=60)
    assert result is None


@pytest.mark.asyncio
async def test_get_within_custom_ttl_returns_value():
    cache, redis = _make_cache()
    redis.get.return_value = json.dumps({"k": "v"})
    # 30 seconds old, TTL = 60 → fresh
    redis.hgetall.return_value = {"created_at": _ts(-30), "ttl": "60"}

    result = await cache.get_with_ttl("key_custom2", ttl_seconds=60)
    assert result == {"k": "v"}


# ── set_with_ttl ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_calls_setex_hset_expire():
    cache, redis = _make_cache()
    redis.setex = AsyncMock()
    redis.hset = AsyncMock()
    redis.expire = AsyncMock()

    await cache.set_with_ttl("key_set", {"data": 42}, ttl_seconds=300)

    redis.setex.assert_awaited_once()
    args = redis.setex.await_args[0]
    assert args[0] == "ctx:key_set"
    assert args[1] == 300
    assert json.loads(args[2]) == {"data": 42}

    redis.hset.assert_awaited_once()
    redis.expire.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_meta_contains_created_at():
    cache, redis = _make_cache()
    redis.setex = AsyncMock()
    redis.hset = AsyncMock()
    redis.expire = AsyncMock()

    before = datetime.utcnow().timestamp()
    await cache.set_with_ttl("key_meta", {"x": 1})
    after = datetime.utcnow().timestamp()

    mapping = redis.hset.await_args[1]["mapping"]
    ts = float(mapping["created_at"])
    assert before <= ts <= after


# ── invalidate_for_recruiter ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalidate_deletes_matching_keys():
    cache, redis = _make_cache()
    redis.scan = AsyncMock(
        side_effect=[
            (0, ["ctx:recruiter:r1:context", "ctx:recruiter:r1:dashboard:stats"]),
            (0, ["ctx:meta:recruiter:r1:context"]),
        ]
    )
    redis.delete = AsyncMock()

    deleted = await cache.invalidate_for_recruiter("r1")

    assert redis.delete.await_count == 2
    assert deleted == 3


@pytest.mark.asyncio
async def test_invalidate_no_keys_returns_zero():
    cache, redis = _make_cache()
    redis.scan = AsyncMock(return_value=(0, []))
    redis.delete = AsyncMock()

    deleted = await cache.invalidate_for_recruiter("nobody")
    assert deleted == 0
    redis.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalidate_multi_page_scan():
    cache, redis = _make_cache()
    # first pattern: two scan pages; second pattern: one page
    redis.scan = AsyncMock(
        side_effect=[
            (42, ["ctx:recruiter:r2:k1"]),   # page 1 of pattern 1
            (0,  ["ctx:recruiter:r2:k2"]),   # page 2 of pattern 1
            (0,  []),                          # pattern 2 empty
        ]
    )
    redis.delete = AsyncMock()

    deleted = await cache.invalidate_for_recruiter("r2")
    assert deleted == 2
