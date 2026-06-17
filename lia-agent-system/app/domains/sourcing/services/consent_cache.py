"""Consent cache for Apify candidate enrichment — 90-day TTL per candidate/company.

Compliance: LGPD Art. 7 / 18 — candidate data enrichment requires explicit consent.
Consent is cached for 90 days to avoid repeat confirmation on the same candidate.
"""
from __future__ import annotations

import logging

from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

_90_DAYS_INTERVAL = "90 days"


async def has_valid_consent(candidate_id: str, company_id: str) -> bool:
    """Return True if candidate has valid enrichment consent within last 90 days."""
    try:
        async with AsyncSessionLocal() as db:
            row = await db.execute(
                text("""
                    SELECT 1 FROM external_api_consumption
                    WHERE company_id = :cid
                      AND candidate_id = :kid
                      AND operation_type = 'consent_grant'
                      AND created_at > NOW() - INTERVAL :interval
                    LIMIT 1
                """),
                {"cid": str(company_id), "kid": str(candidate_id), "interval": _90_DAYS_INTERVAL},
            )
            return row.first() is not None
    except Exception as exc:
        logger.warning("[ConsentCache] check failed for candidate=%s: %s", candidate_id, exc)
        return False


async def record_consent(candidate_id: str, company_id: str, user_id: str) -> None:
    """Record enrichment consent grant — cached for 90 days."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    INSERT INTO external_api_consumption
                        (company_id, candidate_id, user_id, operation_type,
                         actor_id, cost_usd_cents, status, created_at)
                    VALUES
                        (:cid, :kid, :uid, 'consent_grant',
                         'consent_cache', 0, 'success', NOW())
                """),
                {"cid": str(company_id), "kid": str(candidate_id), "uid": str(user_id or "")},
            )
            await db.commit()
            logger.info(
                "[ConsentCache] consent recorded",
                extra={"candidate_id": candidate_id, "company_id": company_id},
            )
    except Exception as exc:
        logger.warning("[ConsentCache] record failed for candidate=%s: %s", candidate_id, exc)
