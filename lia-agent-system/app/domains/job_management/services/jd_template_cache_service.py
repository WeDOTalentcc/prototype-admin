"""
JD Template Cache Service for Token Optimization

Provides caching for job description extractions to avoid redundant LLM calls.
When the same or similar JD is processed multiple times, returns cached results
instead of consuming tokens on repeated extractions.

Architecture:
- Uses Redis for distributed caching (24h TTL default)
- Hash-based cache keys for efficient lookup
- Metrics tracking for cache performance monitoring
- Graceful fallback when Redis unavailable
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Any

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
import logging

logger = logging.getLogger(__name__)


class JDTemplateCacheService:
    """
    Cache service for job description extractions.
    
    Stores processed JD templates (extracted requirements, structured data)
    to avoid redundant LLM calls for similar job descriptions.
    """
    
    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.default_ttl_hours = 24
        self._hits = 0
        self._misses = 0
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection following semantic_search_service pattern."""
        if not REDIS_AVAILABLE:
            logger.info("redis not installed, JD cache using in-memory fallback")
            self._memory_cache: dict[str, dict[str, Any]] = {}
            return
            
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Redis connected for JD template caching")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory cache")
                self.redis_client = None
                self._memory_cache: dict[str, dict[str, Any]] = {}
        else:
            logger.info("No Redis URL, JD cache using in-memory fallback")
            self._memory_cache: dict[str, dict[str, Any]] = {}
    
    def _normalize_jd_text(self, jd_text: str) -> str:
        """
        Normalize JD text for consistent hashing.
        Removes extra whitespace and normalizes case for comparison.
        """
        import re
        text = jd_text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _generate_cache_key(self, jd_text: str, company_id: str) -> str:
        """
        Generate a unique cache key based on JD content and company.
        
        Args:
            jd_text: The job description text
            company_id: The company identifier
            
        Returns:
            A unique cache key string
        """
        normalized_text = self._normalize_jd_text(jd_text)
        content = f"{company_id}:{normalized_text}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:32]
        return f"jd_cache:{company_id}:{hash_value}"
    
    async def get_cached_extraction(
        self, 
        jd_text: str, 
        company_id: str
    ) -> dict[str, Any] | None:
        """
        Get cached JD extraction if available.
        
        Args:
            jd_text: The job description text
            company_id: The company identifier
            
        Returns:
            Cached extraction dict or None if not found
        """
        cache_key = self._generate_cache_key(jd_text, company_id)
        
        try:
            if self.redis_client:
                data = self.redis_client.get(cache_key)
                if data:
                    self._hits += 1
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    result = json.loads(data)
                    result['_cache_metadata'] = {
                        'cached': True,
                        'cache_key': cache_key,
                        'retrieved_at': datetime.utcnow().isoformat()
                    }
                    logger.debug(f"JD cache hit for key: {cache_key}")
                    return result
                else:
                    self._misses += 1
                    logger.debug(f"JD cache miss for key: {cache_key}")
                    return None
            else:
                # ORCHESTRATOR-GHOST-EXEMPT: _memory_cache lazy-init in _init_redis() called from __init__ (guarded by hasattr above)
                if hasattr(self, '_memory_cache') and cache_key in self._memory_cache:
                    self._hits += 1
                    result = self._memory_cache[cache_key].copy()
                    result['_cache_metadata'] = {
                        'cached': True,
                        'cache_key': cache_key,
                        'retrieved_at': datetime.utcnow().isoformat()
                    }
                    return result
                else:
                    self._misses += 1
                    return None
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            self._misses += 1
            return None
    
    async def cache_extraction(
        self, 
        jd_text: str, 
        company_id: str, 
        extraction: dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache a JD extraction result.
        
        Args:
            jd_text: The original job description text
            company_id: The company identifier
            extraction: The extracted data to cache
            ttl_hours: Time-to-live in hours (default 24)
            
        Returns:
            True if cached successfully, False otherwise
        """
        cache_key = self._generate_cache_key(jd_text, company_id)
        ttl_seconds = ttl_hours * 3600
        
        cache_data = {
            **extraction,
            '_cache_metadata': {
                'cached_at': datetime.utcnow().isoformat(),
                'company_id': company_id,
                'ttl_hours': ttl_hours,
                'jd_hash': cache_key.split(':')[-1]
            }
        }
        
        try:
            if self.redis_client:
                self.redis_client.setex(
                    cache_key, 
                    ttl_seconds, 
                    json.dumps(cache_data, ensure_ascii=False)
                )
                logger.debug(f"JD extraction cached: {cache_key} (TTL: {ttl_hours}h)")
                return True
            else:
                if hasattr(self, '_memory_cache'):
                    self._memory_cache[cache_key] = cache_data
                    logger.debug(f"JD extraction cached in memory: {cache_key}")
                    return True
                return False
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
            return False
    
    async def invalidate(self, company_id: str) -> int:
        """
        Invalidate all cached extractions for a company.
        
        Args:
            company_id: The company identifier
            
        Returns:
            Number of keys invalidated
        """
        pattern = f"jd_cache:{company_id}:*"
        count = 0
        
        try:
            if self.redis_client:
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor, 
                        match=pattern, 
                        count=100
                    )
                    if keys:
                        count += self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
                logger.info(f"Invalidated {count} JD cache entries for company: {company_id}")
            else:
                if hasattr(self, '_memory_cache'):
                    keys_to_delete = [
                        k for k in self._memory_cache.keys() 
                        if k.startswith(f"jd_cache:{company_id}:")
                    ]
                    for key in keys_to_delete:
                        del self._memory_cache[key]
                        count += 1
                    logger.info(f"Invalidated {count} in-memory JD cache entries for company: {company_id}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
        
        return count
    
    async def invalidate_by_key(self, jd_text: str, company_id: str) -> bool:
        """
        Invalidate a specific cached extraction.
        
        Args:
            jd_text: The job description text
            company_id: The company identifier
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        cache_key = self._generate_cache_key(jd_text, company_id)
        
        try:
            if self.redis_client:
                deleted = self.redis_client.delete(cache_key)
                return deleted > 0
            else:
                if hasattr(self, '_memory_cache') and cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                    return True
                return False
        except Exception as e:
            logger.warning(f"Cache key invalidation error: {e}")
            return False
    
    def get_metrics(self) -> dict[str, Any]:
        """
        Get cache performance metrics.
        
        Returns:
            Dict with hits, misses, hit_rate, and cache info
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        
        cache_size = 0
        if self.redis_client:
            try:
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor, 
                        match="jd_cache:*", 
                        count=100
                    )
                    cache_size += len(keys)
                    if cursor == 0:
                        break
            except Exception:
                pass
        elif hasattr(self, '_memory_cache'):
            cache_size = len(self._memory_cache)
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'total_requests': total,
            'hit_rate': round(hit_rate, 2),
            'hit_rate_formatted': f"{hit_rate:.1f}%",
            'cache_size': cache_size,
            'backend': 'redis' if self.redis_client else 'memory',
            'default_ttl_hours': self.default_ttl_hours
        }
    
    def reset_metrics(self):
        """Reset hit/miss counters."""
        self._hits = 0
        self._misses = 0
        logger.info("JD cache metrics reset")


jd_template_cache_service = JDTemplateCacheService()
