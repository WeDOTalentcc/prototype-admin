"""
Cache Manager Service - 3-layer intelligent caching system.

Provides token economy through intelligent caching:
- Layer 1: Session cache (in-memory, per conversation)
- Layer 2: Redis cache (short TTL, 7 days default)
- Layer 3: PostgreSQL cache (long TTL, 30+ days for stable data)

Features:
- Automatic cache key generation with semantic similarity
- TTL management per data type
- Cache hit tracking for optimization
- Graceful degradation when Redis unavailable

All cache configuration (CacheNamespace, CacheTTL, CacheConfig,
NAMESPACE_CACHE_CONFIGS) is defined in app.shared.cache_strategy —
the single source of truth for cache settings.
"""
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.cache_strategy import (
    CacheConfig,
    CacheNamespace,
    CacheTTL,
    DEFAULT_CACHE_CONFIGS,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheResult(Generic[T]):
    """Result from cache lookup."""
    hit: bool
    value: T | None
    source: str | None = None
    key: str | None = None
    age_seconds: int | None = None
    confidence: float | None = None


class SessionCache:
    """
    In-memory session-level cache.
    
    Stores data for the duration of a conversation session.
    Fast access, no network calls, automatically cleared when session ends.
    """
    
    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
    
    def get(self, session_id: str, key: str) -> CacheResult:
        """Get value from session cache."""
        session_data = self._cache.get(session_id, {})
        entry = session_data.get(key)
        
        if entry:
            if entry.get("expires_at") and datetime.utcnow() > entry["expires_at"]:
                del session_data[key]
                return CacheResult(hit=False, value=None)
            
            return CacheResult(
                hit=True,
                value=entry["value"],
                source="session",
                key=key,
                age_seconds=int((datetime.utcnow() - entry["created_at"]).total_seconds())
            )
        
        return CacheResult(hit=False, value=None)
    
    def set(
        self, 
        session_id: str, 
        key: str, 
        value: Any, 
        ttl_seconds: int = CacheTTL.SESSION
    ) -> None:
        """Store value in session cache."""
        if session_id not in self._cache:
            self._cache[session_id] = {}
        
        expires_at = None
        if ttl_seconds > 0:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        self._cache[session_id][key] = {
            "value": value,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at
        }
    
    def delete(self, session_id: str, key: str) -> None:
        """Delete a specific key from session cache."""
        if session_id in self._cache and key in self._cache[session_id]:
            del self._cache[session_id][key]
    
    def clear_session(self, session_id: str) -> None:
        """Clear all cache for a session."""
        if session_id in self._cache:
            del self._cache[session_id]
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from all sessions. Returns count of removed entries."""
        removed = 0
        now = datetime.utcnow()
        
        for session_id in list(self._cache.keys()):
            session_data = self._cache[session_id]
            expired_keys = [
                key for key, entry in session_data.items()
                if entry.get("expires_at") and now > entry["expires_at"]
            ]
            for key in expired_keys:
                del session_data[key]
                removed += 1
            
            if not session_data:
                del self._cache[session_id]
        
        return removed


class RedisCache:
    """
    Redis L1 cache layer.
    
    Short to medium TTL for frequently accessed but volatile data.
    Falls back gracefully if Redis is unavailable.
    """
    
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._available = False
        self._last_check = None
    
    async def _get_client(self):
        """Lazy initialization of Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                await self._client.ping()
                self._available = True
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis not available, falling back to PostgreSQL: {e}")
                self._available = False
                self._client = None
        return self._client
    
    async def is_available(self) -> bool:
        """Check if Redis is available."""
        now = datetime.utcnow()
        if self._last_check and (now - self._last_check).seconds < 60:
            return self._available
        
        self._last_check = now
        await self._get_client()
        return self._available
    
    async def get(self, key: str) -> CacheResult:
        """Get value from Redis cache."""
        if not await self.is_available():
            return CacheResult(hit=False, value=None)
        
        try:
            data = await self._client.get(key)
            if data:
                entry = json.loads(data)
                return CacheResult(
                    hit=True,
                    value=entry.get("value"),
                    source="redis",
                    key=key,
                    confidence=entry.get("confidence")
                )
        except Exception as e:
            logger.warning(f"Redis get error for {key}: {e}")
        
        return CacheResult(hit=False, value=None)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: int = CacheTTL.STANDARD,
        confidence: float | None = None,
        source: str | None = None
    ) -> bool:
        """Store value in Redis cache."""
        if not await self.is_available():
            return False
        
        try:
            entry = {
                "value": value,
                "confidence": confidence,
                "source": source,
                "created_at": datetime.utcnow().isoformat()
            }
            await self._client.setex(key, ttl_seconds, json.dumps(entry, default=str))
            return True
        except Exception as e:
            logger.warning(f"Redis set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis cache."""
        if not await self.is_available():
            return False
        
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete error for {key}: {e}")
            return False
    
    async def increment_hit_count(self, key: str) -> None:
        """Increment hit count for analytics."""
        if await self.is_available():
            try:
                await self._client.hincrby(f"hits:{key}", "count", 1)
            except Exception:
                pass


class PostgresCache:
    """
    PostgreSQL L2 cache layer.
    
    Long TTL for stable, expensive-to-compute data.
    Always available (part of main database).
    """
    
    async def get(self, db: AsyncSession, key: str) -> CacheResult:
        """Get value from PostgreSQL cache."""
        try:
            from app.models.intelligent_cache import CacheEntry
            
            result = await db.execute(
                select(CacheEntry)
                .where(
                    and_(
                        CacheEntry.cache_key == key,
                        CacheEntry.expires_at > datetime.utcnow()
                    )
                )
            )
            entry = result.scalar_one_or_none()
            
            if entry:
                entry.hit_count += 1
                entry.last_hit_at = datetime.utcnow()
                await db.commit()
                
                age = int((datetime.utcnow() - entry.created_at).total_seconds())
                return CacheResult(
                    hit=True,
                    value=entry.value,
                    source="postgres",
                    key=key,
                    age_seconds=age,
                    confidence=entry.confidence
                )
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"PostgreSQL cache get error for {key}: {e}")
        
        return CacheResult(hit=False, value=None)
    
    async def set(
        self,
        db: AsyncSession,
        key: str,
        namespace: str,
        value: Any,
        company_id: str | None = None,
        ttl_seconds: int = CacheTTL.STABLE,
        confidence: float | None = None,
        source: str | None = None,
        tags: list[str] | None = None
    ) -> bool:
        """Store value in PostgreSQL cache."""
        try:
            from app.models.intelligent_cache import CacheEntry
            
            result = await db.execute(
                select(CacheEntry).where(CacheEntry.cache_key == key)
            )
            existing = result.scalar_one_or_none()
            
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            
            if existing:
                existing.value = value
                existing.expires_at = expires_at
                existing.confidence = confidence
                existing.source = source
                existing.tags = tags or []
                existing.updated_at = datetime.utcnow()
            else:
                entry = CacheEntry(
                    cache_key=key,
                    namespace=namespace,
                    company_id=company_id,
                    value=value,
                    ttl_seconds=ttl_seconds,
                    expires_at=expires_at,
                    confidence=confidence,
                    source=source,
                    tags=tags or []
                )
                db.add(entry)
            
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL cache set error for {key}: {e}")
            await db.rollback()
            return False
    
    async def delete(self, db: AsyncSession, key: str) -> bool:
        """Delete a key from PostgreSQL cache."""
        try:
            from app.models.intelligent_cache import CacheEntry
            
            await db.execute(
                delete(CacheEntry).where(CacheEntry.cache_key == key)
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL cache delete error for {key}: {e}")
            await db.rollback()
            return False
    
    async def cleanup_expired(self, db: AsyncSession) -> int:
        """Remove expired entries from PostgreSQL cache."""
        try:
            from app.models.intelligent_cache import CacheEntry
            
            result = await db.execute(
                delete(CacheEntry).where(CacheEntry.expires_at < datetime.utcnow())
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            logger.error(f"PostgreSQL cache cleanup error: {e}")
            await db.rollback()
            return 0


class CacheManagerService:
    """
    Unified cache manager orchestrating all 3 cache layers.
    
    Lookup order: Session → Redis → PostgreSQL
    Write policy: Write to all enabled layers for the namespace
    
    Features:
    - Intelligent key generation
    - Namespace-based configuration
    - Automatic TTL management
    - Cache hit tracking
    - Semantic similarity matching (optional)
    """
    
    def __init__(self, redis_url: str | None = None):
        self.session_cache = SessionCache()
        self.redis_cache = RedisCache(redis_url)
        self.postgres_cache = PostgresCache()
        self.configs = DEFAULT_CACHE_CONFIGS
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _generate_key(
        self,
        namespace: CacheNamespace,
        company_id: str | None,
        identifiers: dict[str, Any]
    ) -> str:
        """Generate a unique cache key from namespace and identifiers."""
        parts = [namespace.value]
        
        if company_id:
            parts.append(company_id)
        
        sorted_ids = sorted(identifiers.items())
        id_str = ":".join(f"{k}={v}" for k, v in sorted_ids if v is not None)
        
        if len(id_str) > 100:
            id_hash = hashlib.md5(id_str.encode()).hexdigest()[:16]
            parts.append(id_hash)
        else:
            parts.append(id_str)
        
        return ":".join(parts)
    
    async def get(
        self,
        namespace: CacheNamespace,
        company_id: str | None,
        identifiers: dict[str, Any],
        session_id: str | None = None,
        db: AsyncSession | None = None
    ) -> CacheResult:
        """
        Look up a value in the cache hierarchy.
        
        Args:
            namespace: Cache namespace for configuration
            company_id: Tenant ID for multi-tenancy
            identifiers: Key-value pairs that identify the cached item
            session_id: Optional session ID for session-level cache
            db: Database session for PostgreSQL layer
        
        Returns:
            CacheResult with hit status and value if found
        """
        config = self.configs.get(namespace, CacheConfig(namespace=namespace))
        key = self._generate_key(namespace, company_id, identifiers)
        
        if session_id:
            result = self.session_cache.get(session_id, key)
            if result.hit:
                self.logger.debug(f"Cache HIT (session): {key}")
                return result
        
        if config.use_redis:
            result = await self.redis_cache.get(key)
            if result.hit:
                self.logger.debug(f"Cache HIT (redis): {key}")
                if session_id:
                    self.session_cache.set(session_id, key, result.value)
                return result
        
        if config.use_postgres and db:
            result = await self.postgres_cache.get(db, key)
            if result.hit:
                self.logger.debug(f"Cache HIT (postgres): {key}")
                if session_id:
                    self.session_cache.set(session_id, key, result.value)
                if config.use_redis:
                    await self.redis_cache.set(
                        key, result.value, 
                        config.redis_ttl,
                        result.confidence
                    )
                return result
        
        self.logger.debug(f"Cache MISS: {key}")
        return CacheResult(hit=False, value=None, key=key)
    
    async def set(
        self,
        namespace: CacheNamespace,
        company_id: str | None,
        identifiers: dict[str, Any],
        value: Any,
        session_id: str | None = None,
        db: AsyncSession | None = None,
        confidence: float | None = None,
        source: str | None = None,
        tags: list[str] | None = None
    ) -> str:
        """
        Store a value in all appropriate cache layers.
        
        Returns the generated cache key.
        """
        config = self.configs.get(namespace, CacheConfig(namespace=namespace))
        key = self._generate_key(namespace, company_id, identifiers)
        
        if session_id:
            self.session_cache.set(session_id, key, value)
        
        if config.use_redis:
            await self.redis_cache.set(
                key, value, config.redis_ttl, confidence, source
            )
        
        if config.use_postgres and db:
            await self.postgres_cache.set(
                db, key, namespace.value, value,
                company_id=company_id,
                ttl_seconds=config.postgres_ttl,
                confidence=confidence,
                source=source,
                tags=tags
            )
        
        self.logger.debug(f"Cache SET: {key}")
        return key
    
    async def invalidate(
        self,
        namespace: CacheNamespace,
        company_id: str | None,
        identifiers: dict[str, Any],
        session_id: str | None = None,
        db: AsyncSession | None = None
    ) -> None:
        """Invalidate a cached value across all layers."""
        config = self.configs.get(namespace, CacheConfig(namespace=namespace))
        key = self._generate_key(namespace, company_id, identifiers)
        
        if session_id:
            self.session_cache.delete(session_id, key)
        
        if config.use_redis:
            await self.redis_cache.delete(key)
        
        if config.use_postgres and db:
            await self.postgres_cache.delete(db, key)
        
        self.logger.debug(f"Cache INVALIDATED: {key}")
    
    def clear_session(self, session_id: str) -> None:
        """Clear all session-level cache for a session."""
        self.session_cache.clear_session(session_id)
    
    async def cleanup_expired(self, db: AsyncSession | None = None) -> dict[str, int]:
        """Clean up expired entries from all layers."""
        results = {
            "session": self.session_cache.cleanup_expired()
        }
        
        if db:
            results["postgres"] = await self.postgres_cache.cleanup_expired(db)
        
        return results
    
    async def get_or_compute(
        self,
        namespace: CacheNamespace,
        company_id: str | None,
        identifiers: dict[str, Any],
        compute_fn,
        session_id: str | None = None,
        db: AsyncSession | None = None,
        confidence: float | None = None,
        source: str | None = None
    ) -> CacheResult:
        """
        Get from cache or compute and cache the result.
        
        This is the primary method for cache-aside pattern.
        """
        result = await self.get(namespace, company_id, identifiers, session_id, db)
        
        if result.hit:
            return result
        
        try:
            computed_value = await compute_fn()
            
            key = await self.set(
                namespace, company_id, identifiers, computed_value,
                session_id, db, confidence, source
            )
            
            return CacheResult(
                hit=False,
                value=computed_value,
                source="computed",
                key=key,
                confidence=confidence
            )
        except Exception as e:
            self.logger.error(f"Cache compute error: {e}")
            raise


cache_manager_service = CacheManagerService()


def get_cache_manager_service() -> "CacheManagerService":
    """Returns the shared CacheManagerService singleton."""
    return cache_manager_service
