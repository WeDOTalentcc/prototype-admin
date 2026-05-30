"""
RoutingLearningService — learns from routing corrections to improve future routing.

Records when users redirect conversations (implicit correction signal).
Computes per-company domain confidence adjustments from correction history.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

USE_ADAPTIVE_ROUTING = os.getenv("USE_ADAPTIVE_ROUTING", "true").lower() == "true"
_LOOKBACK_DAYS = 30
_MIN_SAMPLES = 10


class RoutingLearningService:
    """Records and learns from routing corrections."""

    async def record_correction(
        self,
        session_id: str,
        routed_domain: str,
        actual_domain: str,
        company_id: str,
        db,
        message: str = "",
    ) -> bool:
        """Record a routing correction. Fail-open."""
        # Check flag dynamically to support monkeypatching in tests
        import app.domains.analytics.services.routing_learning_service as _svc_mod
        _flag = getattr(_svc_mod, 'USE_ADAPTIVE_ROUTING', USE_ADAPTIVE_ROUTING)
        if not _flag:
            return False
        try:
            from lia_models.routing_feedback import RoutingFeedback
            feedback = RoutingFeedback(
                company_id=company_id,
                session_id=session_id,
                message_hash=RoutingFeedback.hash_message(message) if message else "",
                routed_domain=routed_domain,
                actual_domain=actual_domain,
                corrected="true" if routed_domain != actual_domain else "false",
                corrected_at=datetime.utcnow(),
            )
            db.add(feedback)
            await db.commit()
            logger.info(
                "[RoutingLearning] correction recorded: %s → %s (company=%s)",
                routed_domain, actual_domain, company_id,
            )
            return True
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning("[RoutingLearning] record_correction failed (fail-open): %s", exc)
            return False

    async def compute_domain_confidence_adjustments(
        self, company_id: str, db=None
    ) -> dict[str, float]:
        """Compute confidence adjustments per domain from recent corrections.

        Returns dict mapping domain → adjustment factor (0.8 to 1.2).
        """
        if not USE_ADAPTIVE_ROUTING or db is None:
            return {}
        try:
            from sqlalchemy import case, func, select

            from lia_models.routing_feedback import RoutingFeedback
            cutoff = datetime.utcnow() - timedelta(days=_LOOKBACK_DAYS)

            result = await db.execute(
                select(
                    RoutingFeedback.routed_domain,
                    func.count().label("total"),
                    func.sum(
                        case((RoutingFeedback.corrected == "true", 1), else_=0)
                    ).label("corrections"),
                ).where(
                    RoutingFeedback.company_id == company_id,
                    RoutingFeedback.corrected_at >= cutoff,
                ).group_by(RoutingFeedback.routed_domain)
            )
            rows = result.all()

            adjustments: dict[str, float] = {}
            for row in rows:
                domain, total, corrections = row.routed_domain, row.total, (row.corrections or 0)
                if total < _MIN_SAMPLES:
                    continue
                error_rate = corrections / total
                # High error rate → reduce confidence; low error rate → slight boost
                if error_rate > 0.3:
                    adjustments[domain] = max(0.8, 1.0 - error_rate * 0.5)
                elif error_rate < 0.05:
                    adjustments[domain] = min(1.2, 1.0 + (0.05 - error_rate) * 2)

            logger.info(
                "[RoutingLearning] adjustments for company=%s: %s",
                company_id, adjustments,
            )
            return adjustments
        except Exception as exc:
            logger.warning(
                "[RoutingLearning] compute_domain_confidence_adjustments failed: %s", exc
            )
            return {}

    async def get_cached_adjustments(self, company_id: str) -> dict[str, float]:
        """Get pre-computed adjustments from Redis. Fail-open → empty dict."""
        try:
            from app.core.redis_client import get_redis
            redis = await get_redis()
            import json
            cached = await redis.get(f"routing_adj:{company_id}")
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return {}

    async def cache_adjustments(self, company_id: str, adjustments: dict[str, float]) -> None:
        """Cache adjustments to Redis (TTL=24h). Fail-silent."""
        try:
            import json

            from app.core.redis_client import get_redis
            redis = await get_redis()
            await redis.setex(
                f"routing_adj:{company_id}", 86400, json.dumps(adjustments)
            )
        except Exception:
            pass


routing_learning_service = RoutingLearningService()
