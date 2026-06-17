"""
TDD Red → Green — rails_user_sync (Phase 1 Auth Decoupling).

Tests for DB-backed Rails user resolution cache that eliminates per-request
HTTP calls to Rails GET /v1/me.

Phase 1 goal: after first request, subsequent requests for same user
resolve company_id from FastAPI DB instead of calling Rails /v1/me.
"""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Test 1: DB miss returns None ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lookup_from_db_returns_none_when_user_not_in_db():
    """L2 DB lookup returns None when rails_user_id not found in users table."""
    with patch("app.auth.rails_user_sync.AsyncSessionLocal") as mock_session_cls:
        mock_ctx = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_ctx.execute = AsyncMock(return_value=mock_result)

        from app.auth.rails_user_sync import _lookup_from_db
        result = await _lookup_from_db(99999)
        assert result is None


# ── Test 2: DB hit returns cached payload ─────────────────────────────────────

@pytest.mark.asyncio
async def test_lookup_from_db_returns_payload_when_found():
    """L2 DB lookup returns synthetic payload dict when user row exists."""
    with patch("app.auth.rails_user_sync.AsyncSessionLocal") as mock_session_cls:
        mock_ctx = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_result = MagicMock()
        # Returns (email, company_id, role, is_active)
        mock_result.fetchone.return_value = ("recruiter@acme.com", "company-uuid-abc", "recruiter", True)
        mock_ctx.execute = AsyncMock(return_value=mock_result)

        from app.auth.rails_user_sync import _lookup_from_db
        result = await _lookup_from_db(42)
        assert result is not None
        assert result["email"] == "recruiter@acme.com"
        assert result["company_id"] == "company-uuid-abc"
        assert result["account_id"] == "company-uuid-abc"
        assert result["is_admin"] is False
        assert result["_source"] == "db_cache"


# ── Test 3: L1 cache prevents DB + HTTP calls on second request ───────────────

@pytest.mark.asyncio
async def test_get_or_sync_uses_l1_cache_on_second_call():
    """Second request for same rails_user_id hits L1 in-memory cache only."""
    import app.auth.rails_user_sync as mod

    user_id = 12345
    # Pre-warm L1 cache
    mod._L1_CACHE[user_id] = {
        "email": "cached@test.com",
        "company_id": "comp-111",
        "account_id": "comp-111",
        "is_admin": False,
        "fetched_at": time.time(),  # fresh — not expired
        "_source": "l1_cache",
    }

    try:
        with patch("app.auth.rails_user_sync._lookup_from_db", new_callable=AsyncMock) as mock_db, \
             patch("app.auth.rails_user_sync._fetch_from_rails_me", new_callable=AsyncMock) as mock_rails:

            result = await mod.get_or_sync_rails_user("bearer_token", user_id)

            assert result is not None
            assert result["email"] == "cached@test.com"
            mock_db.assert_not_called()
            mock_rails.assert_not_called()
    finally:
        mod._L1_CACHE.pop(user_id, None)


# ── Test 4: upsert writes to DB ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upsert_to_db_executes_upsert_sql():
    """_upsert_to_db calls DB execute + commit for valid user data."""
    with patch("app.auth.rails_user_sync.AsyncSessionLocal") as mock_session_cls:
        mock_ctx = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_ctx.execute = AsyncMock()
        mock_ctx.commit = AsyncMock()

        from app.auth.rails_user_sync import _upsert_to_db
        await _upsert_to_db(
            rails_user_id=77,
            info={
                "email": "newuser@company.com",
                "name": "New User",
                "account_id": "company-uuid-456",
                "is_admin": False,
            },
        )

        mock_ctx.execute.assert_called_once()
        mock_ctx.commit.assert_called_once()


# ── Test 5: upsert skips when email is missing ────────────────────────────────

@pytest.mark.asyncio
async def test_upsert_to_db_skips_when_email_missing():
    """_upsert_to_db does NOT hit DB if email is None — fail-safe, no partial writes."""
    with patch("app.auth.rails_user_sync.AsyncSessionLocal") as mock_session_cls:
        mock_ctx = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_ctx.execute = AsyncMock()

        from app.auth.rails_user_sync import _upsert_to_db
        await _upsert_to_db(
            rails_user_id=88,
            info={
                "email": None,  # missing email
                "name": "Ghost User",
                "account_id": "company-uuid-789",
                "is_admin": False,
            },
        )

        # No DB write allowed without email
        mock_ctx.execute.assert_not_called()
