"""TTL-based eviction for in-process fallback dicts (Task #871).

When Redis is unavailable, several services fall back to a process-local dict
to keep dev / single-process CI runs working. Without active eviction those
dicts grow until the process restarts, which is the same memory-leak pattern
Task #867 fixed in ``app.jobs.tasks.jd_upload._LOCAL_STAGE``.

These tests prove the fallback now mirrors the Redis ``setex`` semantics for:

* ``app.shared.session_bridge.SessionBridge``
* ``app.shared.memory.candidate_list_store.CandidateListStore``
* ``app.shared.observability.agent_health_alert_service.AgentHealthAlertService``
* ``app.middleware.rate_limiter.RateLimiter`` (empty bucket / expired block sweep)
* ``app.domains.ai.services.ai_cache_service.AICacheService`` (size cap)
* ``app.domains.ai.services.embedding_cache_service.EmbeddingCacheService``

Each test drives the module's monotonic clock indirection so it runs fast
and deterministically without sleeping.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest


# --------------------------------------------------------------------------- #
# SessionBridge — 7-day TTL, plaintext serialised JSON in fallback
# --------------------------------------------------------------------------- #


class TestSessionBridgeFallback:
    def test_expired_session_is_swept_on_load(self, monkeypatch):
        from app.shared import session_bridge as sb

        clock = {"value": 1000.0}
        monkeypatch.setattr(sb, "_now", lambda: clock["value"])

        bridge = sb.SessionBridge(ttl_seconds=60)
        bridge._get_redis_client = AsyncMock(return_value=None)

        # Task #1144: SessionContext carries company_id; keys are namespaced
        # as ``lia:session:<company_id>:<session_id>``.
        cid = "00000000-0000-4000-a000-000000000001"
        ctx = sb.SessionContext(
            session_id="sess-1", user_id="u1", domain="recruiting", company_id=cid
        )

        asyncio.run(bridge.save(ctx))
        assert f"lia:session:{cid}:sess-1" in bridge._memory_store

        # Jump just past the TTL so the entry must be swept.
        clock["value"] += 61
        loaded = asyncio.run(bridge.load("sess-1", company_id=cid))
        assert loaded is None
        assert f"lia:session:{cid}:sess-1" not in bridge._memory_store

    def test_save_sweeps_other_expired_entries(self, monkeypatch):
        from app.shared import session_bridge as sb

        clock = {"value": 5000.0}
        monkeypatch.setattr(sb, "_now", lambda: clock["value"])

        bridge = sb.SessionBridge(ttl_seconds=30)
        bridge._get_redis_client = AsyncMock(return_value=None)

        cid = "00000000-0000-4000-a000-000000000001"
        old = sb.SessionContext(session_id="old", user_id="u1", domain="x", company_id=cid)
        asyncio.run(bridge.save(old))

        clock["value"] += 31  # invalidate "old"
        new = sb.SessionContext(session_id="new", user_id="u2", domain="x", company_id=cid)
        asyncio.run(bridge.save(new))

        assert f"lia:session:{cid}:old" not in bridge._memory_store
        assert f"lia:session:{cid}:new" in bridge._memory_store

    def test_in_memory_load_returns_session_after_save(self, monkeypatch):
        """Without crypto Redis, plain JSON round-trips through the fallback."""
        from app.shared import session_bridge as sb

        bridge = sb.SessionBridge(ttl_seconds=3600)
        bridge._get_redis_client = AsyncMock(return_value=None)

        cid = "00000000-0000-4000-a000-000000000001"
        ctx = sb.SessionContext(
            session_id="sess-x", user_id="u1", domain="recruiting", company_id=cid
        )
        ctx.entity_cache["candidate_id"] = "42"

        asyncio.run(bridge.save(ctx))
        loaded = asyncio.run(bridge.load("sess-x", company_id=cid))
        assert loaded is not None
        assert loaded.session_id == "sess-x"
        assert loaded.entity_cache.get("candidate_id") == "42"


# --------------------------------------------------------------------------- #
# CandidateListStore — 30 min TTL
# --------------------------------------------------------------------------- #


class TestCandidateListStoreFallback:
    def test_expired_list_is_swept_on_get(self, monkeypatch):
        from app.shared.memory import candidate_list_store as cls_module

        clock = {"value": 0.0}
        monkeypatch.setattr(cls_module, "_now", lambda: clock["value"])

        store = cls_module.CandidateListStore()
        store._get_redis = AsyncMock(return_value=None)
        store._redis_available = False

        asyncio.run(store.set("conv-1", [{"id": 1}]))
        assert "conv-1" in store._memory

        clock["value"] += cls_module.LIST_TTL_SECONDS + 1
        result = asyncio.run(store.get("conv-1"))
        assert result is None
        assert "conv-1" not in store._memory

    def test_set_sweeps_unrelated_expired_entries(self, monkeypatch):
        from app.shared.memory import candidate_list_store as cls_module

        clock = {"value": 100.0}
        monkeypatch.setattr(cls_module, "_now", lambda: clock["value"])

        store = cls_module.CandidateListStore()
        store._get_redis = AsyncMock(return_value=None)
        store._redis_available = False

        asyncio.run(store.set("old", [{"id": 1}]))
        clock["value"] += cls_module.LIST_TTL_SECONDS + 1
        asyncio.run(store.set("new", [{"id": 2}]))

        assert "old" not in store._memory
        assert "new" in store._memory


# --------------------------------------------------------------------------- #
# AgentHealthAlertService — sliding-window WINDOW_MINUTES
# --------------------------------------------------------------------------- #


class TestAgentHealthAlertFallback:
    def test_failure_counter_expires_after_window(self, monkeypatch):
        from app.shared.observability import agent_health_alert_service as ahas

        clock = {"value": 0.0}
        monkeypatch.setattr(ahas, "_now", lambda: clock["value"])

        svc = ahas.AgentHealthAlertService()
        svc._get_redis = AsyncMock(return_value=None)

        first = asyncio.run(svc.record_failure("c1", "wizard", "boom"))
        assert first == 1

        # Sliding window has elapsed for the silent agent — the next failure
        # must not see the previous count, i.e. the entry was swept.
        clock["value"] += ahas.WINDOW_MINUTES * 60 + 1
        second = asyncio.run(svc.record_failure("c1", "wizard", "boom"))
        assert second == 1

    def test_unrelated_expired_keys_are_swept_on_increment(self, monkeypatch):
        from app.shared.observability import agent_health_alert_service as ahas

        clock = {"value": 0.0}
        monkeypatch.setattr(ahas, "_now", lambda: clock["value"])

        svc = ahas.AgentHealthAlertService()
        svc._get_redis = AsyncMock(return_value=None)

        asyncio.run(svc.record_failure("c1", "ghost", "x"))
        clock["value"] += ahas.WINDOW_MINUTES * 60 + 1
        asyncio.run(svc.record_failure("c1", "alive", "y"))

        assert svc._redis_key("c1", "ghost") not in svc._memory
        assert svc._redis_key("c1", "alive") in svc._memory


# --------------------------------------------------------------------------- #
# RateLimiter — fallback dicts
# --------------------------------------------------------------------------- #


class TestRateLimiterFallbackSweep:
    def _make(self):
        from app.middleware.rate_limiter import RateLimiter

        rl = RateLimiter()
        rl._redis = None
        rl._redis_available = False
        rl._redis_last_attempt = float("inf")
        return rl

    def test_empty_buckets_are_dropped_after_sweep_interval(self):
        rl = self._make()
        # Seed user/company entries that are already older than 1h.
        old = datetime.utcnow() - timedelta(hours=2)
        rl._fallback_user_requests["ghost-user"] = [old]
        rl._fallback_company_requests["ghost-company"] = [old]
        # Force a sweep on the next call.
        rl._fallback_last_sweep = None

        # Issuing a check for *another* user must trigger the sweep and drop
        # the stale outer keys instead of leaving them empty in the dict.
        allowed, _ = asyncio.run(rl.check_rate_limit("real-user", "real-co"))
        assert allowed is True
        assert "ghost-user" not in rl._fallback_user_requests
        assert "ghost-company" not in rl._fallback_company_requests

    def test_expired_blocks_are_dropped_on_sweep(self):
        rl = self._make()
        past = datetime.utcnow() - timedelta(seconds=120)
        rl._fallback_blocked_users["expired-user"] = past
        rl._fallback_blocked_companies["expired-co"] = past
        rl._fallback_last_sweep = None

        asyncio.run(rl.check_rate_limit("u", "c"))

        assert "expired-user" not in rl._fallback_blocked_users
        assert "expired-co" not in rl._fallback_blocked_companies


# --------------------------------------------------------------------------- #
# AICacheService — size cap
# --------------------------------------------------------------------------- #


class TestAICacheServiceMemoryCap:
    def test_memory_cache_is_bounded(self, monkeypatch):
        from app.domains.ai.services import ai_cache_service as ai_mod

        # Tighter cap so the test stays fast.
        monkeypatch.setattr(ai_mod, "_MEMORY_CACHE_MAX_ENTRIES", 5)

        svc = ai_mod.AICacheService()
        svc.redis_client = None  # force in-memory path

        # Insert 12 distinct entries; the cap (5) must be enforced after each set.
        for i in range(12):
            asyncio.run(
                svc.set_cached(
                    cache_type="jd_generation",
                    content=f"prompt-{i}",
                    company_id="co",
                    response_data={"answer": i},
                )
            )

        assert len(svc._memory_cache) <= 5

    def test_expired_entries_are_swept(self, monkeypatch):
        from datetime import datetime as real_dt

        from app.domains.ai.services import ai_cache_service as ai_mod

        svc = ai_mod.AICacheService()
        svc.redis_client = None

        # Seed an entry that is already expired.
        stale_key = "ai_cache:jd_generation:co:stale"
        svc._memory_cache[stale_key] = {
            "data": {"answer": "old"},
            "cached_at": (real_dt.utcnow() - timedelta(hours=10)).isoformat(),
            "expires_at": (real_dt.utcnow() - timedelta(hours=1)).isoformat(),
            "cache_type": "jd_generation",
            "company_id": "co",
        }

        asyncio.run(
            svc.set_cached(
                cache_type="jd_generation",
                content="fresh",
                company_id="co",
                response_data={"answer": "new"},
            )
        )

        assert stale_key not in svc._memory_cache


# --------------------------------------------------------------------------- #
# EmbeddingCacheService — TTL + size cap
# --------------------------------------------------------------------------- #


class TestEmbeddingCacheFallback:
    def test_expired_embedding_is_swept_on_get(self, monkeypatch):
        from app.domains.ai.services import embedding_cache_service as emb_mod

        clock = {"value": 1000.0}
        monkeypatch.setattr(emb_mod, "_now", lambda: clock["value"])

        svc = emb_mod.EmbeddingCacheService()
        svc._get_redis = AsyncMock(return_value=None)
        svc._redis_ok = False

        asyncio.run(svc.cache_embedding("hello", [0.1, 0.2], ttl=10))
        # Sanity: present immediately.
        assert asyncio.run(svc.get_embedding("hello")) == [0.1, 0.2]

        clock["value"] += 11
        result = asyncio.run(svc.get_embedding("hello"))
        assert result is None
        # And the entry is gone, not just hidden.
        key = svc._make_key("hello", "text-embedding-3-small")
        assert key not in svc._local

    def test_cache_size_is_capped(self, monkeypatch):
        from app.domains.ai.services import embedding_cache_service as emb_mod

        # Tight cap for the test.
        monkeypatch.setattr(emb_mod, "_LOCAL_MAX_ENTRIES", 4)

        svc = emb_mod.EmbeddingCacheService()
        svc._get_redis = AsyncMock(return_value=None)
        svc._redis_ok = False

        for i in range(10):
            asyncio.run(svc.cache_embedding(f"text-{i}", [float(i)], ttl=600))

        assert len(svc._local) <= 4
