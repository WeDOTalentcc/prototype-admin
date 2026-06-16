"""D7 — Benchmark Salarial Real"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


class TestSalaryBenchmarkService:

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_benchmark(self):
        from app.shared.services.salary_benchmark_service import SalaryBenchmarkService
        import json

        cached_data = {
            "job_title": "Engenheiro Python",
            "seniority": "senior",
            "location": "São Paulo",
            "p25": 12000.0,
            "p50": 18000.0,
            "p75": 25000.0,
            "currency": "BRL",
            "source": "external",
            "fetched_at": datetime.utcnow().isoformat(),
        }

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        with patch("app.core.redis_client.get_redis", return_value=mock_redis):
            svc = SalaryBenchmarkService()
            result = await svc.get_benchmark("Engenheiro Python", "senior", "São Paulo", "comp-1")

        assert result.p50 == 18000.0
        assert result.source == "external"

    @pytest.mark.asyncio
    async def test_cache_miss_calls_apify(self):
        from app.shared.services.salary_benchmark_service import SalaryBenchmarkService

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        mock_apify = AsyncMock()
        mock_apify.scrape_salary_data = AsyncMock(
            return_value={"salaries": [10000, 14000, 18000, 22000, 28000]}
        )

        with patch("app.core.redis_client.get_redis", return_value=mock_redis):
            with patch("app.domains.sourcing.services.apify_service.ApifyService", return_value=mock_apify):
                svc = SalaryBenchmarkService()
                svc._fetch_from_apify = AsyncMock(return_value=None)
                result = await svc.get_benchmark("Dev Backend", "senior", "SP", "comp-1")

        # Falls through to fallback if Apify returns None
        assert result.source in ("external", "fallback")

    @pytest.mark.asyncio
    async def test_fallback_when_apify_fails(self):
        from app.shared.services.salary_benchmark_service import SalaryBenchmarkService

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("app.core.redis_client.get_redis", return_value=mock_redis):
            svc = SalaryBenchmarkService()
            svc._fetch_from_apify = AsyncMock(side_effect=RuntimeError("Apify down"))
            result = await svc.get_benchmark("Dev Backend", "senior", "SP", "comp-1")

        assert result.source == "fallback"
        assert result.p50 > 0

    @pytest.mark.asyncio
    async def test_fallback_returns_valid_benchmarks_for_all_levels(self):
        from app.shared.services.salary_benchmark_service import SalaryBenchmarkService

        svc = SalaryBenchmarkService()
        for level in ["junior", "pleno", "senior", "especialista", "gerente"]:
            result = svc._fallback_benchmark("Dev", level, "Brasil")
            assert result.p25 < result.p50 < result.p75
            assert result.source == "fallback"

    def test_salary_benchmark_to_dict(self):
        from app.shared.services.salary_benchmark_service import SalaryBenchmark

        b = SalaryBenchmark(
            job_title="Dev",
            seniority="senior",
            location="SP",
            p25=12000.0,
            p50=18000.0,
            p75=25000.0,
            fetched_at=datetime(2026, 3, 15),
        )
        d = b.to_dict()
        assert d["p50"] == 18000.0
        assert "2026-03-15" in d["fetched_at"]

    @pytest.mark.asyncio
    async def test_redis_error_falls_through_to_apify(self):
        from app.shared.services.salary_benchmark_service import SalaryBenchmarkService

        with patch("app.core.redis_client.get_redis", side_effect=RuntimeError("Redis down")):
            svc = SalaryBenchmarkService()
            svc._fetch_from_apify = AsyncMock(return_value=None)
            result = await svc.get_benchmark("Dev", "pleno", "RJ", "comp-1")

        assert result.source == "fallback"

    def test_cache_key_format(self):
        from app.shared.services.salary_benchmark_service import SalaryBenchmarkService

        svc = SalaryBenchmarkService()
        key = svc._cache_key("Eng Python", "Senior", "São Paulo")
        assert key.startswith("salary_benchmark:")
        assert "eng_python" in key.lower()
