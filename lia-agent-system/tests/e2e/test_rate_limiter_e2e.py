"""
Testes E2E — Rate Limiter (per-tenant fixed window).

Task #1355 — Atualizado para Fixed Window (INCR + EXPIRE, 4 ops/request).
A implementação anterior usava ZSET sliding window (16 ops/request).

Cenários cobertos:
1. Requisição dentro dos limites → permitida
2. Usuário excede limite por minuto → 429 retornado
3. Company excede limite por minuto → 429 retornado
4. Retry-after correto retornado
5. Fallback in-memory quando Redis indisponível
6. Reset após janela de tempo
7. Limites independentes por user_id e company_id
8. Verificação dos stats do backend

Camada: E2E com mocks Redis (sem Redis real).
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rate_limiter_with_memory_backend():
    """Cria RateLimiter forçando modo in-memory (sem Redis)."""
    from app.middleware.rate_limiter import RateLimiter
    rl = RateLimiter()
    rl._redis = None
    rl._redis_available = False
    rl._redis_last_attempt = float("inf")
    return rl


def _make_rate_limiter_with_mock_redis(
    fixed_window_results=None,
    always_allow=True,
):
    """
    Cria RateLimiter com Redis mockado.

    Task #1355 — atualizado para Fixed Window (_redis_fixed_window).
    A implementação anterior mockava _redis_sliding_window (ZSET, 16 ops).
    A nova usa _redis_fixed_window (INCR+EXPIRE, 4 ops).

    Args:
        fixed_window_results: lista de (allowed, count) por chamada de fixed window
        always_allow: se True, todas as janelas retornam allowed=True, count=1
    """
    from app.middleware.rate_limiter import RateLimiter

    rl = RateLimiter()

    call_count = [0]
    results = fixed_window_results or []

    async def _mock_fixed_window(key, limit, window_sec):
        if results:
            idx = min(call_count[0], len(results) - 1)
            call_count[0] += 1
            return results[idx]
        return (True, 1) if always_allow else (False, limit + 1)

    mock_redis = MagicMock()
    mock_redis.pipeline = MagicMock(return_value=MagicMock())
    rl._redis = mock_redis
    rl._redis_available = True
    rl._redis_fixed_window = _mock_fixed_window

    return rl


# ---------------------------------------------------------------------------
# Seção 1 — Requisições dentro dos limites
# ---------------------------------------------------------------------------

class TestRateLimiterAllowed:

    @pytest.mark.asyncio
    async def test_first_request_always_allowed(self):
        """Primeiro request de um usuário novo deve ser permitido."""
        rl = _make_rate_limiter_with_memory_backend()
        allowed, retry_after = await rl.check_rate_limit("user-001", "company-001")
        assert allowed is True
        assert retry_after is None

    @pytest.mark.asyncio
    async def test_requests_below_per_minute_limit_allowed(self):
        """Requests abaixo do limite por minuto são todos permitidos."""
        rl = _make_rate_limiter_with_memory_backend()

        for i in range(5):
            allowed, _ = await rl.check_rate_limit(f"user-{i}", "company-001")
            assert allowed is True

    @pytest.mark.asyncio
    async def test_different_users_independent_limits(self):
        """Usuários diferentes têm limites independentes."""
        rl = _make_rate_limiter_with_memory_backend()

        allowed1, _ = await rl.check_rate_limit("user-alpha", "company-001")
        allowed2, _ = await rl.check_rate_limit("user-beta", "company-001")

        assert allowed1 is True
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_redis_backed_allows_within_limits(self):
        """Redis-backed: request dentro do limite é permitido."""
        rl = _make_rate_limiter_with_mock_redis(always_allow=True)

        allowed, retry_after = await rl.check_rate_limit("user-redis", "company-redis")
        assert allowed is True
        assert retry_after is None


# ---------------------------------------------------------------------------
# Seção 2 — Limite por minuto por usuário excedido
# ---------------------------------------------------------------------------

class TestRateLimiterUserMinuteLimit:

    @pytest.mark.asyncio
    async def test_user_blocked_after_per_minute_limit(self):
        """Usuário é bloqueado quando excede o limite por minuto."""
        rl = _make_rate_limiter_with_memory_backend()

        per_minute_limit = rl.LIMITS["per_minute_per_user"]
        user_id = "user-overloaded"
        company_id = "company-001"

        for _ in range(per_minute_limit):
            rl._fallback_user_requests.setdefault(user_id, [])
            rl._fallback_user_requests[user_id].append(datetime.utcnow())

        rl._fallback_company_requests.setdefault(company_id, [])

        allowed, retry_after = await rl.check_rate_limit(user_id, company_id)

        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_user_blocked_gets_retry_after_equal_to_block_duration(self):
        """Usuário bloqueado recebe retry_after = BLOCK_DURATION_SECONDS."""
        rl = _make_rate_limiter_with_memory_backend()
        user_id = "user-rate-limited"
        company_id = "company-001"

        per_minute_limit = rl.LIMITS["per_minute_per_user"]
        rl._fallback_user_requests[user_id] = [datetime.utcnow()] * per_minute_limit
        rl._fallback_company_requests.setdefault(company_id, [])

        allowed, retry_after = await rl.check_rate_limit(user_id, company_id)

        assert not allowed
        assert retry_after == rl.BLOCK_DURATION_SECONDS

    @pytest.mark.asyncio
    async def test_redis_backed_user_blocked_when_fixed_window_denied(self):
        """Redis-backed: usuário bloqueado quando fixed window retorna denied."""
        rl = _make_rate_limiter_with_mock_redis(
            fixed_window_results=[(False, 601)]
        )

        allowed, retry_after = await rl.check_rate_limit("user-denied", "company-001")

        assert allowed is False
        assert retry_after == rl.BLOCK_DURATION_SECONDS


# ---------------------------------------------------------------------------
# Seção 3 — Limite por minuto por company excedido
# ---------------------------------------------------------------------------

class TestRateLimiterCompanyMinuteLimit:

    @pytest.mark.asyncio
    async def test_company_blocked_after_per_minute_limit(self):
        """Company é bloqueada quando excede o limite por minuto."""
        rl = _make_rate_limiter_with_memory_backend()

        per_minute_limit = rl.LIMITS["per_minute_per_company"]
        company_id = "company-overloaded"
        user_id = "user-innocent"

        rl._fallback_company_requests.setdefault(company_id, [])
        rl._fallback_company_requests[company_id] = [datetime.utcnow()] * per_minute_limit
        rl._fallback_user_requests.setdefault(user_id, [])

        allowed, retry_after = await rl.check_rate_limit(user_id, company_id)

        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_company_rate_limit_blocks_all_users_in_company(self):
        """Quando company é bloqueada, todos os usuários dela são bloqueados."""
        rl = _make_rate_limiter_with_memory_backend()

        company_id = "company-shared-limit"
        per_minute_limit = rl.LIMITS["per_minute_per_company"]
        rl._fallback_company_requests[company_id] = [datetime.utcnow()] * per_minute_limit

        for user_suffix in ["alice", "bob", "carol"]:
            user_id = f"user-{user_suffix}"
            rl._fallback_user_requests.setdefault(user_id, [])
            allowed, _ = await rl.check_rate_limit(user_id, company_id)
            assert allowed is False, f"Usuário {user_id} deveria estar bloqueado pela quota da company"


# ---------------------------------------------------------------------------
# Seção 4 — Retry-After correto
# ---------------------------------------------------------------------------

class TestRateLimiterRetryAfter:

    @pytest.mark.asyncio
    async def test_retry_after_positive_when_blocked(self):
        """retry_after deve ser positivo quando usuário está bloqueado."""
        rl = _make_rate_limiter_with_memory_backend()
        user_id = "user-retry"
        company_id = "company-001"

        per_minute_limit = rl.LIMITS["per_minute_per_user"]
        rl._fallback_user_requests[user_id] = [datetime.utcnow()] * per_minute_limit
        rl._fallback_company_requests.setdefault(company_id, [])

        allowed, retry_after = await rl.check_rate_limit(user_id, company_id)

        assert not allowed
        assert isinstance(retry_after, int)
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_retry_after_none_when_allowed(self):
        """retry_after deve ser None quando request é permitido."""
        rl = _make_rate_limiter_with_memory_backend()

        allowed, retry_after = await rl.check_rate_limit("user-ok", "company-ok")

        assert allowed is True
        assert retry_after is None

    @pytest.mark.asyncio
    async def test_previously_blocked_unblocked_after_duration(self):
        """Usuário bloqueado é desbloqueado após expiração do bloco."""
        rl = _make_rate_limiter_with_memory_backend()
        user_id = "user-block-expiry"
        company_id = "company-001"

        expired_block_time = datetime.utcnow() - timedelta(seconds=rl.BLOCK_DURATION_SECONDS + 1)
        rl._fallback_blocked_users[user_id] = expired_block_time
        rl._fallback_company_requests.setdefault(company_id, [])
        rl._fallback_user_requests.setdefault(user_id, [])

        allowed, retry_after = await rl.check_rate_limit(user_id, company_id)

        assert allowed is True
        assert retry_after is None


# ---------------------------------------------------------------------------
# Seção 5 — Fallback in-memory quando Redis indisponível
# ---------------------------------------------------------------------------

class TestRateLimiterFallback:

    @pytest.mark.asyncio
    async def test_falls_back_to_memory_when_redis_unavailable(self):
        """Quando Redis não está disponível, cai para in-memory."""
        rl = _make_rate_limiter_with_memory_backend()

        assert rl._redis is None
        assert not rl._redis_available

        allowed, _ = await rl.check_rate_limit("user-mem", "company-mem")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_memory_backend_still_enforces_limits(self):
        """Fallback in-memory ainda reforça os limites de rate limiting."""
        rl = _make_rate_limiter_with_memory_backend()
        user_id = "user-mem-limited"
        company_id = "company-001"

        per_minute_limit = rl.LIMITS["per_minute_per_user"]
        rl._fallback_user_requests[user_id] = [datetime.utcnow()] * per_minute_limit
        rl._fallback_company_requests.setdefault(company_id, [])

        allowed, retry_after = await rl.check_rate_limit(user_id, company_id)

        assert allowed is False
        assert retry_after is not None

    @pytest.mark.asyncio
    async def test_redis_error_degrades_to_allow_all(self):
        """Quando Redis levanta erro durante check, degrada para allow-all (fail-open)."""
        rl = _make_rate_limiter_with_memory_backend()

        async def _broken_fixed_window(*args, **kwargs):
            raise ConnectionError("Redis connection refused")

        rl._redis = MagicMock()
        rl._redis_available = True
        rl._redis_fixed_window = _broken_fixed_window

        allowed, _ = await rl._check_redis("user-redis-error", "company-001")

        assert allowed is True


# ---------------------------------------------------------------------------
# Seção 6 — Limites independentes entre usuários
# ---------------------------------------------------------------------------

class TestRateLimiterTenantIsolation:

    @pytest.mark.asyncio
    async def test_user_limits_are_per_user_not_shared(self):
        """Limites por usuário são individuais — não compartilhados entre usuários."""
        rl = _make_rate_limiter_with_memory_backend()

        user1 = "user-isolated-1"
        user2 = "user-isolated-2"
        company_id = "company-multi"

        per_minute_limit = rl.LIMITS["per_minute_per_user"]

        rl._fallback_user_requests[user1] = [datetime.utcnow()] * per_minute_limit
        rl._fallback_company_requests.setdefault(company_id, [])
        rl._fallback_user_requests.setdefault(user2, [])

        allowed_u1, _ = await rl.check_rate_limit(user1, company_id)
        allowed_u2, _ = await rl.check_rate_limit(user2, company_id)

        assert allowed_u1 is False
        assert allowed_u2 is True

    @pytest.mark.asyncio
    async def test_companies_have_independent_rate_limits(self):
        """Diferentes companies têm limites independentes."""
        rl = _make_rate_limiter_with_memory_backend()

        company1 = "company-limit-test-1"
        company2 = "company-limit-test-2"
        user_id = "user-multi-company"

        per_minute_limit = rl.LIMITS["per_minute_per_company"]
        rl._fallback_company_requests[company1] = [datetime.utcnow()] * per_minute_limit
        rl._fallback_company_requests.setdefault(company2, [])
        rl._fallback_user_requests.setdefault(user_id, [])

        allowed_c1, _ = await rl.check_rate_limit(user_id, company1)
        allowed_c2, _ = await rl.check_rate_limit(user_id, company2)

        assert allowed_c1 is False
        assert allowed_c2 is True


# ---------------------------------------------------------------------------
# Seção 7 — Stats do rate limiter
# ---------------------------------------------------------------------------

class TestRateLimiterStats:

    def test_get_stats_returns_dict(self):
        """get_stats() retorna dicionário com configuração."""
        rl = _make_rate_limiter_with_memory_backend()
        stats = rl.get_stats()
        assert isinstance(stats, dict)
        assert "backend" in stats
        assert "limits" in stats

    def test_get_stats_backend_memory_when_redis_unavailable(self):
        """Backend é 'memory' quando Redis não está disponível."""
        rl = _make_rate_limiter_with_memory_backend()
        stats = rl.get_stats()
        assert stats["backend"] == "memory"

    def test_get_stats_limits_include_required_keys(self):
        """Stats incluem os limites por minuto (os relevantes para Fixed Window)."""
        rl = _make_rate_limiter_with_memory_backend()
        stats = rl.get_stats()
        expected_keys = {
            "per_minute_per_user",
            "per_minute_per_company",
        }
        assert expected_keys.issubset(set(stats["limits"].keys()))

    def test_limits_have_correct_values(self):
        """Limites configurados têm os valores corretos."""
        from app.middleware.rate_limiter import RateLimiter
        rl = RateLimiter()
        assert rl.LIMITS["per_minute_per_user"] == 600
        assert rl.LIMITS["per_minute_per_company"] == 3000
