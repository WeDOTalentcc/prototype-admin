"""
Rails User Sync — Phase 1 Auth Decoupling (2026-06-10).

DB-backed cache for Rails user resolution. Eliminates per-request synchronous
HTTP calls to Rails GET /v1/me by caching resolution in the FastAPI users table.

Architecture (3-tier cache):
  L1: in-memory dict (5-min TTL) — fastest, per-process
  L2: FastAPI users table (persistent, survives restarts) — rails_user_id column
  L3: Rails GET /v1/me (original path, only for first-ever request per user)

Flow:
  1. Rails JWT arrives → middleware extracts rails_user_id (integer)
  2. L1 check → L2 DB check → L3 Rails /v1/me (stop at first hit)
  3. On L3 hit: upsert user to DB (background task, non-blocking)
  4. Future requests for same user: L1 or L2 hit, zero HTTP to Rails

Feature flag:
  FASTAPI_RAILS_DB_CACHE=true (default) → enable L2 DB cache
  FASTAPI_RAILS_DB_CACHE=false → L1 in-memory only (same as before this migration)

Rollback: set FASTAPI_RAILS_DB_CACHE=false in env → instant, no deploy needed.

Author: Phase 1 Rails elimination (ADR-AUTH-001)
"""
import asyncio
import logging
import time

from sqlalchemy import text

# Module-level import for patchability in tests (no circular import risk).
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# L1: in-memory cache — keyed by rails_user_id (integer)
# TTL matches the original _RAILS_ME_CACHE_TTL_SECONDS in rails_jwt.py
_L1_CACHE: dict[int, dict] = {}
_L1_CACHE_TTL_SECONDS = 300  # 5 minutes


async def get_or_sync_rails_user(token: str, rails_user_id: int) -> dict | None:
    """
    Resolve user info for a Rails integer user_id.

    Returns a synthetic payload dict compatible with auth_enforcement.py:
        {email, company_id, account_id, is_admin, fetched_at, _source}

    Priority: L1 in-memory → L2 DB → L3 Rails /v1/me.
    Triggers a background DB upsert after L3 hit.
    """
    # L1: in-memory cache (fastest path)
    cached = _L1_CACHE.get(rails_user_id)
    if cached and (time.time() - cached["fetched_at"]) < _L1_CACHE_TTL_SECONDS:
        return cached

    # L2: DB cache (persistent across restarts)
    from app.core.config import settings
    db_cache_enabled = getattr(settings, "FASTAPI_RAILS_DB_CACHE", True)

    if db_cache_enabled:
        db_info = await _lookup_from_db(rails_user_id)
        if db_info:
            _L1_CACHE[rails_user_id] = db_info  # warm L1 from DB
            return db_info

    # L3: Rails /v1/me (original fallback)
    rails_info = await _fetch_from_rails_me(token, rails_user_id)
    if rails_info:
        _L1_CACHE[rails_user_id] = rails_info
        # Background DB upsert — do NOT await, never block the request
        if db_cache_enabled:
            asyncio.create_task(_upsert_to_db(rails_user_id, rails_info))

    return rails_info


async def _lookup_from_db(rails_user_id: int) -> dict | None:
    """
    L2: look up user in FastAPI users table by rails_user_id.

    Returns synthetic payload or None if not found / inactive / error.
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text(
                    """
                    SELECT email, company_id, role, is_active
                    FROM users
                    WHERE rails_user_id = :rid
                    LIMIT 1
                    """
                ),
                {"rid": rails_user_id},
            )
            row = result.fetchone()
            if not row:
                return None
            email, company_id, role, is_active = row
            if not is_active:
                logger.warning("[RailsSync] User rails_user_id=%s found in DB but is_active=False", rails_user_id)
                return None
            return {
                "email": email,
                "account_id": company_id,
                "company_id": company_id,
                "is_admin": role in ("admin", "wedotalent_admin"),
                "fetched_at": time.time(),
                "_source": "db_cache",
            }
    except Exception as exc:
        logger.warning("[RailsSync] DB lookup failed for rails_user_id=%s: %s", rails_user_id, exc)
        return None


async def _fetch_from_rails_me(token: str, user_id: int) -> dict | None:
    """
    L3: call Rails GET /v1/me with the original Bearer token.

    Equivalent to the original fetch_rails_user_info in rails_jwt.py,
    but without the in-memory cache (caching is handled by this module).
    """
    import os

    import httpx

    rails_url = os.environ.get("RAILS_API_URL", "").rstrip("/")
    if not rails_url:
        logger.warning("[RailsSync] RAILS_API_URL not configured — cannot resolve user")
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{rails_url}/v1/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                logger.warning("[RailsSync] /v1/me returned status=%s for user_id=%s", resp.status_code, user_id)
                return None
            data = resp.json()
    except Exception as exc:
        logger.error("[RailsSync] /v1/me call failed for user_id=%s: %s", user_id, exc)
        return None

    user = data.get("user") or data
    return {
        "email": user.get("email"),
        "name": user.get("name"),
        "account_id": user.get("account_id"),
        "company_id": str(user.get("account_id") or ""),
        "is_admin": bool(user.get("is_admin")),
        "fetched_at": time.time(),
        "_source": "rails_me",
    }


async def _upsert_to_db(rails_user_id: int, info: dict) -> None:
    """
    Background: upsert Rails user into FastAPI users table.

    ON CONFLICT (email_hash): update rails_user_id, company_id, name.
    This ensures future requests resolve from DB (L2 cache) instead of calling Rails.

    Never blocks the request — always called via asyncio.create_task().
    """
    email = info.get("email")
    company_id = info.get("account_id") or info.get("company_id")
    name = info.get("name") or email
    is_admin = info.get("is_admin", False)

    if not email:
        logger.warning("[RailsSync] Skipping DB upsert: no email for rails_user_id=%s", rails_user_id)
        return
    if not company_id:
        logger.warning("[RailsSync] Skipping DB upsert: no company_id for rails_user_id=%s", rails_user_id)
        return

    role = "admin" if is_admin else "recruiter"

    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text(
                    """
                    INSERT INTO users (
                        id, email, name, role, company_id, rails_user_id,
                        is_active, permissions, is_scim_managed, email_verified,
                        created_at, updated_at
                    )
                    VALUES (
                        gen_random_uuid(), :email, :name, :role::userrole,
                        :company_id, :rails_user_id,
                        true, '{}', false, true,
                        NOW(), NOW()
                    )
                    ON CONFLICT (email) DO UPDATE SET
                        rails_user_id = EXCLUDED.rails_user_id,
                        company_id    = EXCLUDED.company_id,
                        name          = EXCLUDED.name,
                        updated_at    = NOW()
                    """
                ),
                {
                    "email": email,
                    "name": name or email,
                    "role": role,
                    "company_id": str(company_id),
                    "rails_user_id": rails_user_id,
                },
            )
            await db.commit()
            logger.info(
                "[RailsSync] Upserted rails_user_id=%s (source=%s)",
                rails_user_id,
                info.get("_source", "unknown"),
            )
    except Exception as exc:
        logger.error("[RailsSync] DB upsert failed for rails_user_id=%s: %s", rails_user_id, exc)
