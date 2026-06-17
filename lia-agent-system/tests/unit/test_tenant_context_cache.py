"""
Sensor: TenantContextService module-level cache TTL=60s.
Harness: computacional (deterministic unit tests, no inference).
Refs: P0-1 perf audit 2026-06-15.
"""
import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_tenant_context_cache_hit_avoids_db():
    """Cache hit on 2nd call within TTL must not call DB again."""
    from app.shared.services.tenant_context_service import (
        TenantContextService,
        _tenant_ctx_cache,
        invalidate_tenant_context_cache,
    )
    company_id = "test-company-cache-hit"
    invalidate_tenant_context_cache(company_id)

    svc = TenantContextService.__new__(TenantContextService)
    mock_ctx = MagicMock()
    _tenant_ctx_cache[company_id] = (mock_ctx, time.time())

    with patch.object(svc, "_fetch_from_db", new_callable=AsyncMock) as mock_db:
        result = await svc.get_context(company_id=company_id, db=AsyncMock())
        mock_db.assert_not_called()

    assert result is mock_ctx


@pytest.mark.asyncio
async def test_tenant_context_cache_expired_hits_db():
    """Expired cache entry (age>60s) must call DB."""
    from app.shared.services.tenant_context_service import (
        TenantContextService,
        _tenant_ctx_cache,
        invalidate_tenant_context_cache,
    )
    company_id = "test-company-expired"
    invalidate_tenant_context_cache(company_id)
    _tenant_ctx_cache[company_id] = (MagicMock(), time.time() - 61)  # expired

    fresh_ctx = MagicMock()
    svc = TenantContextService.__new__(TenantContextService)
    with patch.object(svc, "_fetch_from_db", new_callable=AsyncMock, return_value=fresh_ctx) as mock_db:
        result = await svc.get_context(company_id=company_id, db=AsyncMock())
        mock_db.assert_called_once()

    assert result is fresh_ctx


@pytest.mark.asyncio
async def test_tenant_context_cache_miss_cold():
    """No cache entry → hits DB and stores result."""
    from app.shared.services.tenant_context_service import (
        TenantContextService,
        _tenant_ctx_cache,
        invalidate_tenant_context_cache,
    )
    company_id = "test-company-cold"
    invalidate_tenant_context_cache(company_id)
    assert company_id not in _tenant_ctx_cache

    fresh_ctx = MagicMock()
    svc = TenantContextService.__new__(TenantContextService)
    with patch.object(svc, "_fetch_from_db", new_callable=AsyncMock, return_value=fresh_ctx) as mock_db:
        result = await svc.get_context(company_id=company_id, db=AsyncMock())
        mock_db.assert_called_once()

    assert result is fresh_ctx
    assert company_id in _tenant_ctx_cache


@pytest.mark.asyncio
async def test_tenant_context_with_job_id_bypasses_cache():
    """When job_id is provided, cache is bypassed (per-job pipeline stages vary)."""
    from app.shared.services.tenant_context_service import (
        TenantContextService,
        _tenant_ctx_cache,
        invalidate_tenant_context_cache,
    )
    company_id = "test-company-job-bypass"
    invalidate_tenant_context_cache(company_id)
    cached_ctx = MagicMock()
    _tenant_ctx_cache[company_id] = (cached_ctx, time.time())  # fresh cache

    fresh_ctx = MagicMock()
    svc = TenantContextService.__new__(TenantContextService)
    with patch.object(svc, "_fetch_from_db", new_callable=AsyncMock, return_value=fresh_ctx) as mock_db:
        result = await svc.get_context(company_id=company_id, db=AsyncMock(), job_id="job-123")
        mock_db.assert_called_once()

    # Result is fresh, not cached
    assert result is fresh_ctx
    # Cache not updated when job_id was present
    assert _tenant_ctx_cache[company_id][0] is cached_ctx


@pytest.mark.asyncio
async def test_invalidate_tenant_context_cache_removes_entry():
    """invalidate_tenant_context_cache removes entry; next call hits DB."""
    from app.shared.services.tenant_context_service import (
        TenantContextService,
        _tenant_ctx_cache,
        invalidate_tenant_context_cache,
    )
    company_id = "test-company-invalidate"
    _tenant_ctx_cache[company_id] = (MagicMock(), time.time())
    assert company_id in _tenant_ctx_cache

    invalidate_tenant_context_cache(company_id)
    assert company_id not in _tenant_ctx_cache
