"""Service: CandidateStatusService — token validation + rate limiting."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_MESSAGES_PER_HOUR = 10
MAX_MESSAGES_PER_DAY = 30


class CandidateStatusService:
    """Validates candidate portal tokens and enforces rate limits via Redis."""

    async def validate_token(self, token: str, secret: str) -> dict[str, Any] | None:
        """Decode and validate JWT candidate token.

        Returns: {candidate_id, vacancy_id, company_id, channel} or None if invalid.
        Validates: signature, expiry, scope fields present.
        """
        try:
            import jwt
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            required = {"candidate_id", "vacancy_id", "company_id"}
            if not required.issubset(payload.keys()):
                logger.warning("[CSS Service] Token missing required fields")
                return None
            return payload
        except Exception as exc:
            logger.warning("[CSS Service] Token validation failed: %s", type(exc).__name__)
            return None

    async def check_rate_limit(self, candidate_id: str) -> dict[str, bool | int]:
        """Check per-candidate rate limits using Redis.

        Returns: {allowed: bool, remaining_hour: int, remaining_day: int}
        """
        try:
            from app.core.redis_client import get_redis
            redis = await get_redis()

            key_hour = f"css_rate:{candidate_id}:hour"
            key_day = f"css_rate:{candidate_id}:day"

            hour_count = int(await redis.get(key_hour) or 0)
            day_count = int(await redis.get(key_day) or 0)

            if hour_count >= MAX_MESSAGES_PER_HOUR or day_count >= MAX_MESSAGES_PER_DAY:
                logger.info("[CSS Service] Rate limit hit candidate_id=%s", candidate_id)
                return {
                    "allowed": False,
                    "remaining_hour": max(0, MAX_MESSAGES_PER_HOUR - hour_count),
                    "remaining_day": max(0, MAX_MESSAGES_PER_DAY - day_count),
                }

            # Increment counters
            pipe = redis.pipeline()
            pipe.incr(key_hour)
            pipe.expire(key_hour, 3600)
            pipe.incr(key_day)
            pipe.expire(key_day, 86400)
            await pipe.execute()

            return {
                "allowed": True,
                "remaining_hour": MAX_MESSAGES_PER_HOUR - hour_count - 1,
                "remaining_day": MAX_MESSAGES_PER_DAY - day_count - 1,
            }
        except Exception as exc:
            logger.error("[CSS Service] Rate limit check failed (fail-open): %s", exc)
            return {"allowed": True, "remaining_hour": -1, "remaining_day": -1}
