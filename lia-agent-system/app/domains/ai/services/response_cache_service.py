"""
Response Cache Service for LIA Responses

Provides intelligent caching for LIA agent responses to reduce redundant processing
and improve response times for frequent queries.

Features:
- Redis caching with configurable TTL per intent type
- In-memory fallback when Redis is unavailable
- Metrics tracking (hits, misses, hit_rate)
- Pattern-based cache invalidation
- Intent-aware cache key generation
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any


try:
    import redis.asyncio as aioredis
    AIOREDIS_AVAILABLE = True
except ImportError:
    try:
        import aioredis
        AIOREDIS_AVAILABLE = True
    except ImportError:
        aioredis = None
        AIOREDIS_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration settings."""
    REDIS_URL: str | None = os.environ.get("REDIS_URL")
    CACHE_ENABLED: bool = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_DEFAULT: int = int(os.environ.get("CACHE_TTL_DEFAULT", "300"))
    CACHE_TTL_PIPELINE_STATS: int = int(os.environ.get("CACHE_TTL_PIPELINE_STATS", "60"))
    CACHE_TTL_CANDIDATE_SEARCH: int = int(os.environ.get("CACHE_TTL_CANDIDATE_SEARCH", "120"))
    CACHE_TTL_JOB_INSIGHTS: int = int(os.environ.get("CACHE_TTL_JOB_INSIGHTS", "180"))
    CACHE_TTL_ANALYTICS: int = int(os.environ.get("CACHE_TTL_ANALYTICS", "90"))
    
    INTENT_TTL_MAPPING: dict[str, int] = {
        "pipeline_stats": CACHE_TTL_PIPELINE_STATS,
        "candidate_search": CACHE_TTL_CANDIDATE_SEARCH,
        "job_insights": CACHE_TTL_JOB_INSIGHTS,
        "analytics": CACHE_TTL_ANALYTICS,
        "job_status": 60,
        "candidate_count": 60,
        "stage_distribution": 60,
        "funnel_analysis": 120,
        "market_data": 300,
        "salary_benchmark": 600,
    }


class InMemoryCache:
    """
    In-memory cache with TTL support for environments without Redis.
    
    Features:
    - Automatic expiration of entries based on TTL
    - Pattern-based key matching for invalidation
    - Bounded size with LRU-like eviction
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, dict[str, Any]] = {}
        self._access_times: dict[str, float] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> str | None:
        """Get value from cache if not expired."""
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        expires_at = entry.get("expires_at")
        
        if expires_at and datetime.fromisoformat(expires_at) < datetime.utcnow():
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
            self._misses += 1
            return None
        
        self._access_times[key] = time.time()
        self._hits += 1
        return entry.get("data")
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        self._cache[key] = {
            "data": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow().isoformat()
        }
        self._access_times[key] = time.time()
        return True
    
    async def delete(self, key: str) -> int:
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return 1
        return 0
    
    async def keys(self, pattern: str) -> list[str]:
        """Get keys matching a pattern (simple wildcard support)."""
        import fnmatch
        pattern = pattern.replace("*", ".*") if ".*" not in pattern else pattern
        try:
            import re
            regex = re.compile(pattern.replace("*", ".*"))
            return [k for k in self._cache.keys() if regex.match(k)]
        except Exception:
            return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
    
    def _evict_oldest(self):
        """Evict the least recently accessed entries."""
        if not self._access_times:
            return
        
        sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
        evict_count = max(1, len(self._cache) // 10)
        
        for key, _ in sorted_keys[:evict_count]:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self._cache.items():
            expires_at = entry.get("expires_at")
            if expires_at and datetime.fromisoformat(expires_at) < now:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
        
        return len(expired_keys)
    
    @property
    def hits(self) -> int:
        return self._hits
    
    @property
    def misses(self) -> int:
        return self._misses
    
    def reset_stats(self):
        self._hits = 0
        self._misses = 0


class ResponseCacheService:
    """
    Response cache service for LIA agent responses.
    
    Features:
    - Redis caching with automatic fallback to in-memory
    - Intent-aware TTL configuration
    - Cache key generation based on intent + context + message
    - Pattern-based invalidation for related entries
    - Comprehensive metrics tracking
    
    Usage:
        cache = ResponseCacheService()
        
        # Generate cache key
        key = cache.generate_cache_key("pipeline_stats", {"job_id": "123"}, "show pipeline")
        
        # Check cache
        cached = await cache.get_cached_response(key)
        if cached:
            return cached
        
        # Process and cache result
        result = await process_query()
        await cache.cache_response(key, result, ttl=60)
    """
    
    def __init__(self, redis_url: str = None, default_ttl: int = 300):
        """
        Initialize the response cache service.
        
        Args:
            redis_url: Redis connection URL (optional, defaults to env var)
            default_ttl: Default TTL in seconds (default: 300)
        """
        self._redis_url = redis_url or CacheConfig.REDIS_URL
        self._default_ttl = default_ttl or CacheConfig.CACHE_TTL_DEFAULT
        self._redis_client: Any | None = None
        self._sync_redis_client: Any | None = None
        self._memory_cache = InMemoryCache()
        self._hits = 0
        self._misses = 0
        self._enabled = CacheConfig.CACHE_ENABLED
        
        self._init_redis()
        
        logger.info(f"ResponseCacheService initialized (enabled={self._enabled}, redis={self._redis_client is not None})")
    
    def _init_redis(self):
        """Initialize Redis connection if available."""
        if not self._redis_url:
            logger.info("No Redis URL configured, using in-memory cache fallback")
            return
        
        if REDIS_AVAILABLE:
            try:
                self._sync_redis_client = redis.from_url(self._redis_url)
                self._sync_redis_client.ping()
                logger.info("Redis sync client connected for response caching")
            except Exception as e:
                logger.warning(f"Redis sync connection failed: {e}")
                self._sync_redis_client = None
        
        if AIOREDIS_AVAILABLE:
            try:
                self._redis_client = aioredis.from_url(self._redis_url)
                logger.info("Redis async client initialized for response caching")
            except Exception as e:
                logger.warning(f"Redis async initialization failed: {e}")
                self._redis_client = None
    
    def generate_cache_key(
        self, 
        intent: str, 
        context: dict[str, Any], 
        user_message: str,
        company_id: str = None
    ) -> str:
        """
        Generate a unique cache key based on intent, context, and message.
        
        Args:
            intent: The detected intent (e.g., "pipeline_stats")
            context: Context dictionary (job_id, candidate_id, etc.)
            user_message: The user's original message
            company_id: Optional company ID for multi-tenant isolation
            
        Returns:
            A unique cache key string
        """
        normalized_message = user_message.strip().lower()
        
        context_keys = ["job_id", "candidate_id", "stage", "filter", "date_range"]
        relevant_context = {k: v for k, v in context.items() if k in context_keys and v}
        context_str = json.dumps(relevant_context, sort_keys=True)
        
        content_to_hash = f"{intent}:{context_str}:{normalized_message}"
        content_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()[:16]
        
        prefix = f"lia_response:{company_id}:" if company_id else "lia_response:"
        return f"{prefix}{intent}:{content_hash}"
    
    async def get_cached_response(self, cache_key: str) -> dict[str, Any] | None:
        """
        Get a cached response by key.
        
        Args:
            cache_key: The cache key to look up
            
        Returns:
            Cached response dict or None if not found/expired
        """
        if not self._enabled:
            return None
        
        try:
            data = None
            
            if self._redis_client:
                try:
                    data = await self._redis_client.get(cache_key)
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                except Exception as e:
                    logger.warning(f"Redis async get failed: {e}")
            elif self._sync_redis_client:
                try:
                    data = self._sync_redis_client.get(cache_key)
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                except Exception as e:
                    logger.warning(f"Redis sync get failed: {e}")
            
            if not data:
                data = await self._memory_cache.get(cache_key)
            
            if data:
                self._hits += 1
                try:
                    from app.shared.security.redis_crypto import get_redis_crypto
                    decrypted = get_redis_crypto().decrypt(data) if isinstance(data, str) else data
                    return json.loads(decrypted) if isinstance(decrypted, str) else decrypted
                except json.JSONDecodeError:
                    return {"message": data}
            
            self._misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._misses += 1
            return None
    
    async def cache_response(
        self, 
        cache_key: str, 
        response: dict[str, Any], 
        ttl: int = None,
        intent: str = None
    ) -> bool:
        """
        Cache a response with TTL.
        
        Args:
            cache_key: The cache key
            response: The response dict to cache
            ttl: TTL in seconds (optional, uses intent-based or default)
            intent: Intent for TTL lookup (optional)
            
        Returns:
            True if cached successfully
        """
        if not self._enabled:
            return False
        
        try:
            if ttl is None:
                if intent and intent in CacheConfig.INTENT_TTL_MAPPING:
                    ttl = CacheConfig.INTENT_TTL_MAPPING[intent]
                else:
                    ttl = self._default_ttl
            
            from app.shared.security.redis_crypto import get_redis_crypto
            data = get_redis_crypto().encrypt(json.dumps(response))

            if self._redis_client:
                try:
                    await self._redis_client.setex(cache_key, ttl, data)
                    return True
                except Exception as e:
                    logger.warning(f"Redis async set failed: {e}")
            elif self._sync_redis_client:
                try:
                    self._sync_redis_client.setex(cache_key, ttl, data)
                    return True
                except Exception as e:
                    logger.warning(f"Redis sync set failed: {e}")
            
            return await self._memory_cache.set(cache_key, data, ttl)
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "lia_response:*:job:123:*")
            
        Returns:
            Number of keys deleted
        """
        deleted_count = 0
        
        try:
            if self._redis_client:
                try:
                    keys = []
                    async for key in self._redis_client.scan_iter(match=pattern):
                        keys.append(key)
                    if keys:
                        deleted_count = await self._redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis async pattern delete failed: {e}")
            elif self._sync_redis_client:
                try:
                    keys = self._sync_redis_client.keys(pattern)
                    if keys:
                        deleted_count = self._sync_redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis sync pattern delete failed: {e}")
            
            memory_keys = await self._memory_cache.keys(pattern)
            for key in memory_keys:
                await self._memory_cache.delete(key)
                deleted_count += 1
            
            logger.info(f"Invalidated {deleted_count} cache entries for pattern: {pattern}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    async def invalidate_for_job(self, job_id: str) -> int:
        """Invalidate all cache entries related to a job."""
        return await self.invalidate_by_pattern(f"*job*{job_id}*")
    
    async def invalidate_for_candidate(self, candidate_id: str) -> int:
        """Invalidate all cache entries related to a candidate."""
        return await self.invalidate_by_pattern(f"*candidate*{candidate_id}*")
    
    async def invalidate_for_company(self, company_id: str) -> int:
        """Invalidate all cache entries for a company."""
        return await self.invalidate_by_pattern(f"lia_response:{company_id}:*")
    
    # R-050: cache hit/miss metric -- _hits/_misses tracked in get_cached_response() and cache_response()
    def get_stats(self) -> dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dict with hits, misses, hit_rate, and other metrics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        memory_stats = {
            "memory_hits": self._memory_cache.hits,
            "memory_misses": self._memory_cache.misses,
            "memory_size": len(self._memory_cache._cache),
        }
        
        return {
            "cache_hits_total": self._hits,
            "cache_misses_total": self._misses,
            "cache_hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "redis_available": self._redis_client is not None or self._sync_redis_client is not None,
            "cache_enabled": self._enabled,
            "default_ttl": self._default_ttl,
            **memory_stats
        }
    
    def reset_stats(self):
        """Reset all statistics counters."""
        self._hits = 0
        self._misses = 0
        self._memory_cache.reset_stats()
    
    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled
    
    def enable(self):
        """Enable caching."""
        self._enabled = True
        logger.info("Response cache enabled")
    
    def disable(self):
        """Disable caching."""
        self._enabled = False
        logger.info("Response cache disabled")


def cached_response(ttl: int = None, intent: str = None):
    """
    Decorator for caching async function responses.
    
    Usage:
        @cached_response(ttl=60, intent="pipeline_stats")
        async def get_pipeline_stats(self, job_id: str, context: Dict):
            ...
    
    Args:
        ttl: Time-to-live in seconds
        intent: Intent type for TTL lookup
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache_service = getattr(self, '_response_cache', None)
            if not cache_service:
                cache_service = response_cache_service
            
            if not cache_service.is_enabled():
                return await func(self, *args, **kwargs)
            
            message = kwargs.get('message', '') or kwargs.get('user_message', '') or ''
            context = kwargs.get('context', {}) or {}
            detected_intent = intent or kwargs.get('intent', 'unknown')
            
            if args:
                if isinstance(args[0], str):
                    message = message or args[0]
                elif isinstance(args[0], dict):
                    context = context or args[0]
            
            cache_key = cache_service.generate_cache_key(
                detected_intent,
                context,
                message
            )
            
            cached = await cache_service.get_cached_response(cache_key)
            if cached:
                logger.debug(f"Cache hit for {detected_intent}: {cache_key[:50]}...")
                cached["_from_cache"] = True
                return cached
            
            result = await func(self, *args, **kwargs)
            
            if result and isinstance(result, dict):
                await cache_service.cache_response(
                    cache_key,
                    result,
                    ttl=ttl,
                    intent=detected_intent
                )
            
            return result
        
        return wrapper
    return decorator


response_cache_service = ResponseCacheService()
