"""
AI Cache Service with TTL and Similarity Matching

Provides intelligent caching for AI-generated content to reduce redundant LLM calls
and improve response times. Supports semantic similarity matching to reuse cached
responses for similar inputs.

Architecture:
- Uses Redis for distributed caching with configurable TTL
- Hash-based cache keys for efficient lookup
- Similarity scoring for finding related cached entries
- Metrics tracking for cache performance monitoring
- Graceful fallback to in-memory cache when Redis unavailable
"""

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Max entries in the in-memory fallback cache (injectable for tests).
_MEMORY_CACHE_MAX_ENTRIES: int = 1000

import logging

logger = logging.getLogger(__name__)


class AICacheService:
    """
    Intelligent cache service for AI-generated content.
    
    Features:
    - Exact match caching using content hashes
    - Similarity matching for related queries
    - Configurable TTL per cache type
    - Performance metrics tracking
    - Multi-tenant support via company_id scoping
    """
    
    CACHE_TYPES = {
        "jd_generation": {"ttl_hours": 24, "similarity_threshold": 0.85},
        "wsi_questions": {"ttl_hours": 48, "similarity_threshold": 0.90},
        "skills_extraction": {"ttl_hours": 72, "similarity_threshold": 0.80},
        "salary_analysis": {"ttl_hours": 12, "similarity_threshold": 0.75},
        "competency_mapping": {"ttl_hours": 48, "similarity_threshold": 0.85},
    }
    
    def __init__(self):
        self.redis_client: Any | None = None
        self._memory_cache: dict[str, dict[str, Any]] = {}
        self._similarity_index: dict[str, list[tuple[str, str]]] = {}
        self._hits = 0
        self._misses = 0
        self._similarity_hits = 0
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection if available."""
        if not REDIS_AVAILABLE:
            logger.info("Redis not installed, AI cache using in-memory fallback")
            return
            
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Redis connected for AI caching")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory cache")
                self.redis_client = None
        else:
            logger.info("No Redis URL configured, AI cache using in-memory fallback")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent hashing and comparison."""
        if not text:
            return ""
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def _generate_cache_key(
        self, 
        cache_type: str, 
        content: str, 
        company_id: str,
        extra_params: dict[str, Any] | None = None
    ) -> str:
        """Generate a unique cache key based on content and parameters."""
        normalized = self._normalize_text(content)
        params_str = json.dumps(extra_params or {}, sort_keys=True)
        content_hash = hashlib.sha256(
            f"{normalized}:{params_str}".encode()
        ).hexdigest()[:32]
        return f"ai_cache:{cache_type}:{company_id}:{content_hash}"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two texts using SequenceMatcher."""
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    async def get_cached(
        self,
        cache_type: str,
        content: str,
        company_id: str,
        extra_params: dict[str, Any] | None = None,
        use_similarity: bool = True
    ) -> dict[str, Any] | None:
        """
        Get cached AI response if available.
        
        Args:
            cache_type: Type of cache (jd_generation, wsi_questions, etc.)
            content: The input content to look up
            company_id: Company identifier for multi-tenant isolation
            extra_params: Additional parameters that affect the response
            use_similarity: Whether to try similarity matching if exact match fails
            
        Returns:
            Cached response data or None if not found
        """
        cache_key = self._generate_cache_key(cache_type, content, company_id, extra_params)
        
        result = await self._get_from_cache(cache_key)
        if result:
            self._hits += 1
            logger.debug(f"AI cache hit for {cache_type}: {cache_key[:50]}...")
            return result
        
        if use_similarity:
            config = self.CACHE_TYPES.get(cache_type, {"similarity_threshold": 0.85})
            threshold = config.get("similarity_threshold", 0.85)
            
            similar_result = await self._find_similar(
                cache_type, content, company_id, threshold
            )
            if similar_result:
                self._similarity_hits += 1
                logger.debug(f"AI cache similarity hit for {cache_type}")
                return similar_result
        
        self._misses += 1
        return None
    
    async def _get_from_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Get data from Redis or memory cache. Always returns response_data only."""
        if self.redis_client:
            try:
                data = self.redis_client.get(cache_key)
                if data:
                    parsed = json.loads(data)
                    return parsed.get("data") if isinstance(parsed, dict) else parsed
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            expires_at = entry.get("expires_at", "")
            if expires_at and datetime.fromisoformat(expires_at) > datetime.utcnow():
                return entry.get("data")
            else:
                del self._memory_cache[cache_key]
        
        return None
    
    async def _find_similar(
        self,
        cache_type: str,
        content: str,
        company_id: str,
        threshold: float
    ) -> dict[str, Any] | None:
        """Find a similar cached entry above the similarity threshold."""
        index_key = f"{cache_type}:{company_id}"
        stale_entries = []
        
        if index_key in self._similarity_index:
            for i, (original_content, cache_key) in enumerate(self._similarity_index[index_key]):
                similarity = self._calculate_similarity(content, original_content)
                if similarity >= threshold:
                    result = await self._get_from_cache(cache_key)
                    if result:
                        return result
                    else:
                        stale_entries.append(i)
            
            if stale_entries:
                self._similarity_index[index_key] = [
                    entry for i, entry in enumerate(self._similarity_index[index_key])
                    if i not in stale_entries
                ]
        
        return None
    
    async def set_cached(
        self,
        cache_type: str,
        content: str,
        company_id: str,
        response_data: dict[str, Any],
        extra_params: dict[str, Any] | None = None,
        ttl_hours: int | None = None
    ) -> bool:
        """
        Store AI response in cache.
        
        Args:
            cache_type: Type of cache (jd_generation, wsi_questions, etc.)
            content: The input content that generated the response
            company_id: Company identifier for multi-tenant isolation
            response_data: The AI-generated response to cache
            extra_params: Additional parameters used in generation
            ttl_hours: Override default TTL for this cache type
            
        Returns:
            True if successfully cached, False otherwise
        """
        from datetime import timedelta
        
        cache_key = self._generate_cache_key(cache_type, content, company_id, extra_params)
        
        config = self.CACHE_TYPES.get(cache_type, {"ttl_hours": 24})
        ttl = ttl_hours or config.get("ttl_hours", 24)
        ttl_seconds = ttl * 3600
        
        now = datetime.utcnow()
        expires_at = (now + timedelta(hours=ttl)).isoformat()
        
        cache_data = {
            "data": response_data,
            "cached_at": now.isoformat(),
            "expires_at": expires_at,
            "cache_type": cache_type,
            "company_id": company_id
        }
        
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    ttl_seconds,
                    json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        
        # Sweep expired entries from memory cache before adding new one
        now_dt = datetime.utcnow()
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if v.get("expires_at") and datetime.fromisoformat(v["expires_at"]) <= now_dt
        ]
        for k in expired_keys:
            del self._memory_cache[k]

        self._memory_cache[cache_key] = cache_data

        # Enforce size cap: evict oldest entries when over limit
        if len(self._memory_cache) > _MEMORY_CACHE_MAX_ENTRIES:
            # Sort by cached_at and remove oldest
            sorted_keys = sorted(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].get("cached_at", ""),
            )
            for k in sorted_keys[: len(self._memory_cache) - _MEMORY_CACHE_MAX_ENTRIES]:
                del self._memory_cache[k]

        index_key = f"{cache_type}:{company_id}"
        if index_key not in self._similarity_index:
            self._similarity_index[index_key] = []
        
        max_index_size = 100
        if len(self._similarity_index[index_key]) >= max_index_size:
            self._similarity_index[index_key] = self._similarity_index[index_key][-50:]
        
        self._similarity_index[index_key].append((content, cache_key))
        
        logger.debug(f"AI cache stored for {cache_type}: {cache_key[:50]}...")
        return True
    
    async def invalidate(
        self,
        cache_type: str,
        content: str,
        company_id: str,
        extra_params: dict[str, Any] | None = None
    ) -> bool:
        """Invalidate a specific cache entry."""
        cache_key = self._generate_cache_key(cache_type, content, company_id, extra_params)
        
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
        
        index_key = f"{cache_type}:{company_id}"
        if index_key in self._similarity_index:
            self._similarity_index[index_key] = [
                (c, k) for c, k in self._similarity_index[index_key]
                if k != cache_key
            ]
        
        return True
    
    async def invalidate_company(self, company_id: str) -> int:
        """Invalidate all cache entries for a company."""
        pattern = f"ai_cache:*:{company_id}:*"
        deleted_count = 0
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis pattern delete failed: {e}")
        
        keys_to_delete = [
            k for k in self._memory_cache.keys()
            if f":{company_id}:" in k
        ]
        for key in keys_to_delete:
            del self._memory_cache[key]
            deleted_count += 1
        
        self._similarity_index = {
            k: v for k, v in self._similarity_index.items()
            if not k.endswith(f":{company_id}")
        }
        
        logger.info(f"Invalidated {deleted_count} cache entries for company {company_id}")
        return deleted_count
    
    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self._hits,
            "similarity_hits": self._similarity_hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self._memory_cache),
            "similarity_index_size": sum(len(v) for v in self._similarity_index.values()),
            "redis_available": self.redis_client is not None
        }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self._hits = 0
        self._similarity_hits = 0
        self._misses = 0


ai_cache_service = AICacheService()
