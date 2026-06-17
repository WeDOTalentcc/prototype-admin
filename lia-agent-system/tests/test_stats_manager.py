import pytest
import asyncio
import time
import threading
from app.shared.resilience.stats_manager import StatsManager, CachedStats


class TestCachedStats:
    def test_not_expired(self):
        now = time.time()
        entry = CachedStats(
            data={"count": 10},
            created_at=now,
            expires_at=now + 300,
        )
        assert not entry.is_expired

    def test_expired(self):
        now = time.time()
        entry = CachedStats(
            data={"count": 10},
            created_at=now - 400,
            expires_at=now - 100,
        )
        assert entry.is_expired

    def test_touch(self):
        now = time.time()
        entry = CachedStats(
            data={"count": 10},
            created_at=now,
            expires_at=now + 300,
            hit_count=0,
            last_accessed=now,
        )
        old_accessed = entry.last_accessed
        old_hits = entry.hit_count
        time.sleep(0.01)
        entry.touch()
        assert entry.hit_count == old_hits + 1
        assert entry.last_accessed > old_accessed


class TestStatsManager:
    def setup_method(self):
        StatsManager.reset_instance()
        self.manager = StatsManager(max_entries=10, default_ttl=60)

    def teardown_method(self):
        StatsManager.reset_instance()

    def test_set_and_get(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85})
        result = self.manager.get_stats("analytics", "job_1")
        assert result is not None
        assert result["score"] == 85

    def test_get_nonexistent(self):
        result = self.manager.get_stats("analytics", "missing")
        assert result is None

    def test_get_returns_copy(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85})
        result = self.manager.get_stats("analytics", "job_1")
        result["score"] = 999
        cached = self.manager.get_stats("analytics", "job_1")
        assert cached["score"] == 85

    def test_set_stores_copy(self):
        data = {"score": 85}
        self.manager.set_stats("analytics", "job_1", data)
        data["score"] = 999
        cached = self.manager.get_stats("analytics", "job_1")
        assert cached["score"] == 85

    def test_overwrite(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85})
        self.manager.set_stats("analytics", "job_1", {"score": 95})
        result = self.manager.get_stats("analytics", "job_1")
        assert result["score"] == 95

    def test_ttl_expiry(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85}, ttl_seconds=1)
        assert self.manager.get_stats("analytics", "job_1") is not None
        time.sleep(1.1)
        assert self.manager.get_stats("analytics", "job_1") is None

    def test_custom_ttl(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85}, ttl_seconds=3600)
        result = self.manager.get_stats("analytics", "job_1")
        assert result is not None

    def test_default_ttl(self):
        manager = StatsManager(max_entries=10, default_ttl=1)
        manager.set_stats("analytics", "job_1", {"score": 85})
        assert manager.get_stats("analytics", "job_1") is not None
        time.sleep(1.1)
        assert manager.get_stats("analytics", "job_1") is None

    def test_lru_eviction(self):
        for i in range(10):
            self.manager.set_stats("ns", f"key_{i}", {"val": i})
        self.manager.set_stats("ns", "key_new", {"val": "new"})
        info = self.manager.get_cache_info()
        assert info["size"] <= 10
        assert info["total_evictions"] >= 1

    def test_lru_evicts_least_accessed(self):
        for i in range(10):
            self.manager.set_stats("ns", f"key_{i}", {"val": i})
            time.sleep(0.01)
        for i in range(1, 10):
            self.manager.get_stats("ns", f"key_{i}")
        self.manager.set_stats("ns", "key_new", {"val": "new"})
        assert self.manager.get_stats("ns", "key_0") is None
        assert self.manager.get_stats("ns", "key_new") is not None

    def test_evict_expired_first(self):
        self.manager.set_stats("ns", "expire_me", {"val": 0}, ttl_seconds=1)
        for i in range(1, 10):
            self.manager.set_stats("ns", f"key_{i}", {"val": i})
        time.sleep(1.1)
        self.manager.set_stats("ns", "key_new", {"val": "new"})
        assert self.manager.get_stats("ns", "key_new") is not None
        for i in range(1, 10):
            assert self.manager.get_stats("ns", f"key_{i}") is not None

    def test_invalidate_single(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85})
        self.manager.invalidate("analytics", "job_1")
        assert self.manager.get_stats("analytics", "job_1") is None

    def test_invalidate_namespace(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85})
        self.manager.set_stats("analytics", "job_2", {"score": 90})
        self.manager.set_stats("sourcing", "s_1", {"count": 10})
        count = self.manager.invalidate("analytics")
        assert count == 2
        assert self.manager.get_stats("analytics", "job_1") is None
        assert self.manager.get_stats("analytics", "job_2") is None
        assert self.manager.get_stats("sourcing", "s_1") is not None

    def test_invalidate_nonexistent(self):
        count = self.manager.invalidate("analytics", "missing")
        assert count == 0

    def test_invalidate_returns_count(self):
        self.manager.set_stats("analytics", "job_1", {"score": 85})
        self.manager.set_stats("analytics", "job_2", {"score": 90})
        count = self.manager.invalidate("analytics")
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_or_compute_miss(self):
        called = False

        async def compute_fn():
            nonlocal called
            called = True
            return {"computed": True}

        result = await self.manager.get_or_compute("analytics", "job_1", compute_fn)
        assert called
        assert result["computed"] is True
        assert self.manager.get_stats("analytics", "job_1") is not None

    @pytest.mark.asyncio
    async def test_get_or_compute_hit(self):
        self.manager.set_stats("analytics", "job_1", {"cached": True})
        called = False

        async def compute_fn():
            nonlocal called
            called = True
            return {"computed": True}

        result = await self.manager.get_or_compute("analytics", "job_1", compute_fn)
        assert not called
        assert result["cached"] is True

    def test_get_or_compute_sync_miss(self):
        called = False

        def compute_fn():
            nonlocal called
            called = True
            return {"computed": True}

        result = self.manager.get_or_compute_sync("analytics", "job_1", compute_fn)
        assert called
        assert result["computed"] is True

    def test_get_or_compute_sync_hit(self):
        self.manager.set_stats("analytics", "job_1", {"cached": True})
        called = False

        def compute_fn():
            nonlocal called
            called = True
            return {"computed": True}

        result = self.manager.get_or_compute_sync("analytics", "job_1", compute_fn)
        assert not called
        assert result["cached"] is True

    def test_cleanup_expired(self):
        self.manager.set_stats("ns", "expire_1", {"val": 1}, ttl_seconds=1)
        self.manager.set_stats("ns", "expire_2", {"val": 2}, ttl_seconds=1)
        self.manager.set_stats("ns", "keep", {"val": 3}, ttl_seconds=3600)
        time.sleep(1.1)
        removed = self.manager.cleanup_expired()
        assert removed == 2
        assert self.manager.get_stats("ns", "keep") is not None

    def test_cleanup_returns_count(self):
        self.manager.set_stats("ns", "e1", {"v": 1}, ttl_seconds=1)
        self.manager.set_stats("ns", "e2", {"v": 2}, ttl_seconds=1)
        time.sleep(1.1)
        count = self.manager.cleanup_expired()
        assert count == 2

    def test_cache_info(self):
        self.manager.set_stats("analytics", "j1", {"s": 1})
        info = self.manager.get_cache_info()
        assert info["size"] == 1
        assert info["max_entries"] == 10
        assert "total_hits" in info
        assert "total_misses" in info
        assert "hit_rate" in info
        assert "total_evictions" in info
        assert "total_invalidations" in info
        assert "namespaces" in info

    def test_cache_info_hit_rate(self):
        self.manager.set_stats("ns", "k1", {"v": 1})
        self.manager.get_stats("ns", "k1")
        self.manager.get_stats("ns", "k1")
        self.manager.get_stats("ns", "missing")
        info = self.manager.get_cache_info()
        assert info["total_hits"] == 2
        assert info["total_misses"] == 1
        assert abs(info["hit_rate"] - 2 / 3) < 0.01

    def test_namespace_counts(self):
        self.manager.set_stats("analytics", "j1", {"s": 1})
        self.manager.set_stats("analytics", "j2", {"s": 2})
        self.manager.set_stats("sourcing", "s1", {"c": 1})
        info = self.manager.get_cache_info()
        assert info["namespaces"]["analytics"] == 2
        assert info["namespaces"]["sourcing"] == 1

    def test_concurrent_access(self):
        errors = []

        def writer(tid):
            try:
                for i in range(50):
                    self.manager.set_stats("thread", f"t{tid}_k{i}", {"tid": tid, "i": i})
            except Exception as e:
                errors.append(e)

        def reader(tid):
            try:
                for i in range(50):
                    self.manager.get_stats("thread", f"t{tid}_k{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for t in range(4):
            threads.append(threading.Thread(target=writer, args=(t,)))
            threads.append(threading.Thread(target=reader, args=(t,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_singleton(self):
        a = StatsManager.get_instance(max_entries=100)
        b = StatsManager.get_instance(max_entries=200)
        assert a is b

    def test_reset_singleton(self):
        a = StatsManager.get_instance()
        StatsManager.reset_instance()
        b = StatsManager.get_instance()
        assert a is not b

    def test_clear(self):
        self.manager.set_stats("ns", "k1", {"v": 1})
        self.manager.set_stats("ns", "k2", {"v": 2})
        self.manager.clear()
        assert self.manager.get_stats("ns", "k1") is None
        assert self.manager.get_stats("ns", "k2") is None
        info = self.manager.get_cache_info()
        assert info["size"] == 0

    def test_repr(self):
        r = repr(self.manager)
        assert "StatsManager" in r
        assert "entries=" in r
        assert "max=" in r
