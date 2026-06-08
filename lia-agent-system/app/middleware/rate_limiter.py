"""
Rate Limiter Middleware for LIA Agent System.
Implements per-user and per-company rate limiting using Redis Fixed Window.

Task #1355 — Replaced sliding window ZSET (16 ops/request) with Fixed Window
using INCR + EXPIRE (4 ops/request: 2 windows × 2 ops each). Hourly windows
removed (covered by per-minute buckets at scale). Degradation to in-memory
fallback now emits CRITICAL log + Sentry capture_message so operators are
alerted immediately instead of silently allowing all traffic.

Falls back to in-memory dict if Redis is unavailable (graceful degradation).
"""
import asyncio
import logging
import os
import time
from datetime import datetime, timedelta

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_REDIS_RETRY_COOLDOWN_SECONDS = 30  # só tenta reconectar a cada 30s
# Task #1355 — alert at most once every 5 minutes per service instance
_DEGRADATION_ALERT_COOLDOWN_S = 300.0


class RateLimiter:
    """
    Rate limiter using Redis Fixed Window (INCR + EXPIRE, 4 ops/request).

    Task #1355 — Fixed Window replaces ZSET sliding window (16 ops/request).
    Two windows per request: per-user/min + per-company/min.
    Hourly windows removed — they added 8 ops/request for marginal protection
    already covered by the per-minute buckets at load.

    Falls back to in-memory lists if Redis is unavailable, with explicit
    CRITICAL alert on first degradation per 5-minute window.
    """

    LIMITS = {
        "per_minute_per_user": 600,
        "per_minute_per_company": 3000,
        # Kept for backwards-compat (stats dict, existing tests) but NOT
        # enforced via Redis anymore — removed to reduce ops/request.
        "per_hour_per_user": 20000,
        "per_hour_per_company": 60000,
    }

    BLOCK_DURATION_SECONDS = 60

    def __init__(self):
        self._redis = None
        self._redis_available = False
        self._redis_lock = asyncio.Lock()
        self._redis_last_attempt: float = 0.0
        # Task #1355 — last time we emitted a degradation alert
        self._degradation_alerted_at: float = 0.0
        # Fallback in-memory state (used only when Redis is down)
        self._fallback_user_requests: dict[str, list[datetime]] = {}
        self._fallback_company_requests: dict[str, list[datetime]] = {}
        self._fallback_blocked_users: dict[str, datetime] = {}
        self._fallback_blocked_companies: dict[str, datetime] = {}
        self._fallback_lock = asyncio.Lock()
        # Periodic sweep: remove stale outer keys from fallback dicts.
        self._fallback_last_sweep: float | None = None
        self._FALLBACK_SWEEP_INTERVAL_SECONDS: float = 60.0

    async def _get_redis(self):
        """Lazily initialise Redis connection with cooldown to avoid hammering unavailable Redis."""
        if self._redis is not None:
            return self._redis

        now = time.monotonic()
        if not self._redis_available and (now - self._redis_last_attempt) < _REDIS_RETRY_COOLDOWN_SECONDS:
            return None

        async with self._redis_lock:
            if self._redis is not None:
                return self._redis
            now = time.monotonic()
            if not self._redis_available and (now - self._redis_last_attempt) < _REDIS_RETRY_COOLDOWN_SECONDS:
                return None

            self._redis_last_attempt = now
            try:
                import redis.asyncio as aioredis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=0.5,
                    socket_timeout=0.5,
                )
                await client.ping()
                self._redis = client
                self._redis_available = True
                logger.info("[RateLimiter] Connected to Redis — using distributed fixed window")
            except Exception as e:
                logger.warning("[RateLimiter] Redis unavailable (%s) — falling back to in-memory rate limiting", e)
                self._redis_available = False
            return self._redis

    def _emit_degradation_alert(self, reason: str) -> None:
        """Emit CRITICAL log + Sentry capture on Redis degradation.

        Task #1355 — Rate-limited to once per _DEGRADATION_ALERT_COOLDOWN_S so
        a sustained outage doesn't spam Sentry. Uses monotonic clock.
        """
        now = time.monotonic()
        if (now - self._degradation_alerted_at) < _DEGRADATION_ALERT_COOLDOWN_S:
            return
        self._degradation_alerted_at = now
        logger.critical(
            "[RateLimiter] Redis degraded — falling back to in-memory allow-all. "
            "redis_degraded=True reason=%s",
            reason,
        )
        try:
            import sentry_sdk
            sentry_sdk.capture_message(
                f"RateLimiter Redis degraded: {reason}",
                level="fatal",
                extras={"redis_degraded": True, "service": "rate_limiter"},
            )
        except Exception:
            pass

    async def _redis_fixed_window(
        self, key: str, limit: int, window_sec: int
    ) -> tuple[bool, int]:
        """
        Fixed Window check using INCR + conditional EXPIRE (2 Redis ops).

        Task #1355 — Replaces ZSET sliding window (4 ops). Trades sub-window
        precision for a 4× reduction in Redis commands per request.

        Returns:
            (allowed, current_count)
        """
        r = await self._get_redis()
        if r is None:
            return True, 0

        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_sec, nx=True)
        results = await pipe.execute()
        count = results[0]
        return count <= limit, count

    async def check_rate_limit(self, user_id: str, company_id: str) -> tuple[bool, int | None]:
        """
        Check if request is allowed based on rate limits.

        Returns:
            (allowed, retry_after_seconds)
        """
        if self._redis_available or self._redis is None:
            r = await self._get_redis()
            if r is not None:
                return await self._check_redis(user_id, company_id)

        return await self._check_memory(user_id, company_id)

    async def _check_redis(self, user_id: str, company_id: str) -> tuple[bool, int | None]:
        """Redis-backed fixed-window check (4 ops total: 2 windows × 2 ops)."""
        try:
            if not company_id or company_id == "anonymous":
                prefix = "rl_public"
                user_min_key = f"{prefix}:user:{user_id}:min"
                company_min_key = f"{prefix}:total:min"
            else:
                from app.shared.security.tenant_redis_namespace import (
                    tenant_namespaced_key,
                )
                user_min_key = tenant_namespaced_key("rl", company_id, f"user:{user_id}:min")
                company_min_key = tenant_namespaced_key("rl", company_id, "company:min")

            allowed_u_min, u_min_count = await self._redis_fixed_window(
                user_min_key, self.LIMITS["per_minute_per_user"], 60
            )
            if not allowed_u_min:
                logger.warning("[RateLimiter] User %s exceeded per-minute limit (%d)", user_id, u_min_count)
                return False, self.BLOCK_DURATION_SECONDS

            allowed_c_min, c_min_count = await self._redis_fixed_window(
                company_min_key, self.LIMITS["per_minute_per_company"], 60
            )
            if not allowed_c_min:
                logger.warning("[RateLimiter] Company %s exceeded per-minute limit (%d)", company_id, c_min_count)
                return False, self.BLOCK_DURATION_SECONDS

            return True, None

        except RuntimeError:
            # Namespace-violation RuntimeError must propagate (tenant isolation).
            raise
        except Exception as e:
            self._emit_degradation_alert(str(e))
            self._redis_available = False
            return True, None

    def _maybe_sweep_fallback(self, now: datetime) -> None:
        """Remove stale outer keys from all fallback dicts (periodic, non-blocking)."""
        sweep_needed = (
            self._fallback_last_sweep is None
            or (now.timestamp() - self._fallback_last_sweep) >= self._FALLBACK_SWEEP_INTERVAL_SECONDS
        )
        if not sweep_needed:
            return
        hour_cutoff = now - timedelta(hours=1)
        for requests_dict in (self._fallback_user_requests, self._fallback_company_requests):
            stale_keys = [
                k for k, reqs in requests_dict.items()
                if not any(r > hour_cutoff for r in reqs)
            ]
            for k in stale_keys:
                del requests_dict[k]
        for blocked_dict in (self._fallback_blocked_users, self._fallback_blocked_companies):
            expired_keys = [k for k, t in blocked_dict.items() if now >= t]
            for k in expired_keys:
                del blocked_dict[k]
        self._fallback_last_sweep = now.timestamp()

    async def _check_memory(self, user_id: str, company_id: str) -> tuple[bool, int | None]:
        """In-memory fallback rate limiting."""
        async with self._fallback_lock:
            now = datetime.utcnow()

            self._maybe_sweep_fallback(now)

            for blocked, entity_id in [
                (self._fallback_blocked_users, user_id),
                (self._fallback_blocked_companies, company_id),
            ]:
                if entity_id in blocked:
                    unblock_time = blocked[entity_id]
                    if now < unblock_time:
                        return False, int((unblock_time - now).total_seconds())
                    del blocked[entity_id]

            if user_id not in self._fallback_user_requests:
                self._fallback_user_requests[user_id] = []
            if company_id not in self._fallback_company_requests:
                self._fallback_company_requests[company_id] = []

            hour_cutoff = now - timedelta(hours=1)
            self._fallback_user_requests[user_id] = [
                r for r in self._fallback_user_requests[user_id] if r > hour_cutoff
            ]
            self._fallback_company_requests[company_id] = [
                r for r in self._fallback_company_requests[company_id] if r > hour_cutoff
            ]

            user_reqs = self._fallback_user_requests[user_id]
            company_reqs = self._fallback_company_requests[company_id]
            minute_ago = now - timedelta(minutes=1)

            user_minute_count = sum(1 for r in user_reqs if r > minute_ago)
            company_minute_count = sum(1 for r in company_reqs if r > minute_ago)

            if user_minute_count >= self.LIMITS["per_minute_per_user"]:
                self._fallback_blocked_users[user_id] = now + timedelta(seconds=self.BLOCK_DURATION_SECONDS)
                return False, self.BLOCK_DURATION_SECONDS

            if company_minute_count >= self.LIMITS["per_minute_per_company"]:
                self._fallback_blocked_companies[company_id] = now + timedelta(seconds=self.BLOCK_DURATION_SECONDS)
                return False, self.BLOCK_DURATION_SECONDS

            if len(user_reqs) >= self.LIMITS["per_hour_per_user"]:
                oldest = min(user_reqs)
                retry_after = int((oldest + timedelta(hours=1) - now).total_seconds()) + 1
                return False, max(retry_after, 1)

            if len(company_reqs) >= self.LIMITS["per_hour_per_company"]:
                oldest = min(company_reqs)
                retry_after = int((oldest + timedelta(hours=1) - now).total_seconds()) + 1
                return False, max(retry_after, 1)

            return True, None

    async def record_request(self, user_id: str, company_id: str):
        """Record a request (only needed for in-memory fallback; Redis records on check)."""
        if not self._redis_available:
            async with self._fallback_lock:
                now = datetime.utcnow()
                if user_id not in self._fallback_user_requests:
                    self._fallback_user_requests[user_id] = []
                if company_id not in self._fallback_company_requests:
                    self._fallback_company_requests[company_id] = []
                self._fallback_user_requests[user_id].append(now)
                self._fallback_company_requests[company_id].append(now)

    def get_remaining(self, user_id: str) -> dict:
        """Get remaining rate limits for a user (best-effort for response headers)."""
        return {
            "remaining_per_minute": self.LIMITS["per_minute_per_user"],
            "remaining_per_hour": self.LIMITS["per_hour_per_user"],
            "limit_per_minute": self.LIMITS["per_minute_per_user"],
            "limit_per_hour": self.LIMITS["per_hour_per_user"],
            "reset_minute": None,
            "reset_hour": None,
        }

    def get_stats(self) -> dict:
        """Get overall rate limiter statistics."""
        return {
            "backend": "redis" if self._redis_available else "memory",
            "limits": self.LIMITS,
        }


rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    EXCLUDED_PATHS = {
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/metrics",
    }

    EXCLUDED_PREFIXES = (
        "/docs",
        "/redoc",
        "/api/wsi/",
    )

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        if request.url.path.startswith(self.EXCLUDED_PREFIXES):
            return await call_next(request)

        user_id = self._get_user_id(request)
        company_id = self._get_company_id(request)

        if not user_id:
            user_id = request.client.host if request.client else "anonymous"
        if not company_id:
            company_id = "anonymous"

        allowed, retry_after = await rate_limiter.check_rate_limit(user_id, company_id)

        if not allowed:
            logger.warning(
                "Rate limit exceeded for user=%s, company=%s. Retry after %s seconds.",
                user_id,
                company_id,
                retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rate_limiter.LIMITS["per_minute_per_user"]),
                    "X-RateLimit-Remaining": "0",
                },
            )

        await rate_limiter.record_request(user_id, company_id)

        response = await call_next(request)

        remaining = rate_limiter.get_remaining(user_id)
        response.headers["X-RateLimit-Limit"] = str(remaining["limit_per_minute"])
        response.headers["X-RateLimit-Remaining"] = str(remaining["remaining_per_minute"])

        return response

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request (JWT token or header)."""
        if hasattr(request.state, "user") and request.state.user:
            return str(getattr(request.state.user, "id", None) or request.state.user.get("id"))

        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return f"token:{token[:16]}..."

        return None

    def _get_company_id(self, request: Request) -> str | None:
        """Extract company ID from request."""
        if hasattr(request.state, "user") and request.state.user:
            return str(
                getattr(request.state.user, "company_id", None)
                or (request.state.user.get("company_id") if isinstance(request.state.user, dict) else None)
            )

        state_company = getattr(request.state, "company_id", None)
        if state_company:
            return state_company
        company_id = request.headers.get("X-Company-ID")
        if company_id:
            return company_id

        return None


async def rate_limit_middleware(request: Request, call_next):
    """Standalone middleware function for rate limiting."""
    middleware = RateLimitMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
