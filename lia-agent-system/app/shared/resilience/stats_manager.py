import logging
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CachedStats:
    data: dict[str, Any]
    created_at: float
    expires_at: float
    hit_count: int = 0
    last_accessed: float = 0.0
    namespace: str = ""
    key: str = ""

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.hit_count += 1


class StatsManager:
    """
    Thread-safe in-memory stats cache with TTL and LRU eviction.

    Sits on top of CacheManagerService for fast domain statistics.
    Uses threading.RLock for thread safety (supports reentrant locking).

    Namespaces:
    - "sourcing:{id}" — sourcing stats
    - "analytics:{job_id}" — KPI stats
    - "screening:{job_id}" — screening stats
    - "global:dashboard" — global dashboard metrics

    Usage:
        stats = StatsManager.get_instance()
        data = stats.get_stats("analytics", "job_123")
        if not data:
            data = compute_stats()
            stats.set_stats("analytics", "job_123", data, ttl_seconds=300)

        # Or use get_or_compute:
        data = await stats.get_or_compute("analytics", "job_123", compute_fn, ttl=300)
    """

    _instance: Optional["StatsManager"] = None
    _init_lock = threading.Lock()

    @classmethod
    def get_instance(cls, max_entries: int = 500, default_ttl: int = 300) -> "StatsManager":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls(max_entries=max_entries, default_ttl=default_ttl)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._init_lock:
            cls._instance = None

    def __init__(self, max_entries: int = 500, default_ttl: int = 300):
        self._cache: dict[str, CachedStats] = {}
        self._lock = threading.RLock()
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._total_hits = 0
        self._total_misses = 0
        self._total_evictions = 0
        self._total_invalidations = 0

    def _make_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

    def get_stats(self, namespace: str, key: str) -> dict[str, Any] | None:
        with self._lock:
            cache_key = self._make_key(namespace, key)
            entry = self._cache.get(cache_key)
            if entry is None:
                self._total_misses += 1
                return None
            if entry.is_expired:
                del self._cache[cache_key]
                self._total_misses += 1
                return None
            entry.touch()
            self._total_hits += 1
            return dict(entry.data)

    def set_stats(
        self, namespace: str, key: str, data: dict[str, Any], ttl_seconds: int | None = None
    ) -> None:
        with self._lock:
            if len(self._cache) >= self._max_entries:
                self._evict_lru()

            cache_key = self._make_key(namespace, key)
            now = time.time()
            ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl

            self._cache[cache_key] = CachedStats(
                data=dict(data),
                created_at=now,
                expires_at=now + ttl,
                hit_count=0,
                last_accessed=now,
                namespace=namespace,
                key=key,
            )

    def invalidate(self, namespace: str, key: str | None = None) -> int:
        with self._lock:
            count = 0
            if key is not None:
                cache_key = self._make_key(namespace, key)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    count = 1
            else:
                prefix = f"{namespace}:"
                keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
                for k in keys_to_remove:
                    del self._cache[k]
                count = len(keys_to_remove)

            self._total_invalidations += count
            return count

    async def get_or_compute(
        self,
        namespace: str,
        key: str,
        compute_fn: Callable[[], Awaitable[dict[str, Any]]],
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        cached = self.get_stats(namespace, key)
        if cached is not None:
            return cached

        data = await compute_fn()
        self.set_stats(namespace, key, data, ttl_seconds)
        return data

    def get_or_compute_sync(
        self,
        namespace: str,
        key: str,
        compute_fn: Callable[[], dict[str, Any]],
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        cached = self.get_stats(namespace, key)
        if cached is not None:
            return cached

        data = compute_fn()
        self.set_stats(namespace, key, data, ttl_seconds)
        return data

    def cleanup_expired(self) -> int:
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for k in expired_keys:
                del self._cache[k]
            return len(expired_keys)

    def _evict_lru(self) -> None:
        if not self._cache:
            return

        expired = [k for k, v in self._cache.items() if v.is_expired]
        if expired:
            for k in expired:
                del self._cache[k]
                self._total_evictions += 1
            return

        lru_key = min(self._cache, key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self._total_evictions += 1

    def get_cache_info(self) -> dict[str, Any]:
        with self._lock:
            total_requests = self._total_hits + self._total_misses
            return {
                "size": len(self._cache),
                "max_entries": self._max_entries,
                "total_hits": self._total_hits,
                "total_misses": self._total_misses,
                "hit_rate": self._total_hits / total_requests if total_requests > 0 else 0.0,
                "total_evictions": self._total_evictions,
                "total_invalidations": self._total_invalidations,
                "namespaces": self._get_namespace_counts(),
            }

    def _get_namespace_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self._cache.values():
            ns = entry.namespace
            counts[ns] = counts.get(ns, 0) + 1
        return counts

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __repr__(self) -> str:
        return f"<StatsManager entries={len(self._cache)} max={self._max_entries}>"
