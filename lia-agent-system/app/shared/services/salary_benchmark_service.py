"""
Salary Benchmark Service — D7 (Benchmark Salarial Real)

Busca dados salariais reais via Apify (Glassdoor/LinkedIn) com cache Redis 7 dias.
Fallback: dados setoriais estáticos de sector_benchmark_service.py.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

REDIS_TTL_SECONDS = 7 * 24 * 3600  # 7 days


@dataclass
class SalaryBenchmark:
    job_title: str
    seniority: str
    location: str
    p25: float  # 25th percentile
    p50: float  # median
    p75: float  # 75th percentile
    currency: str = "BRL"
    source: str = "fallback"  # "external" | "internal" | "fallback"
    fetched_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "job_title": self.job_title,
            "seniority": self.seniority,
            "location": self.location,
            "p25": self.p25,
            "p50": self.p50,
            "p75": self.p75,
            "currency": self.currency,
            "source": self.source,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }


# Static fallback data by seniority
_STATIC_SALARY_BENCHMARKS = {
    "junior": {"p25": 3500.0, "p50": 5000.0, "p75": 7000.0},
    "pleno": {"p25": 7000.0, "p50": 10000.0, "p75": 14000.0},
    "senior": {"p25": 12000.0, "p50": 18000.0, "p75": 25000.0},
    "especialista": {"p25": 15000.0, "p50": 22000.0, "p75": 30000.0},
    "gerente": {"p25": 18000.0, "p50": 28000.0, "p75": 45000.0},
}


class SalaryBenchmarkService:
    """
    Fornece benchmarks salariais reais via Apify com fallback setorial estático.
    Cache Redis TTL=7 dias por (job_title, seniority, location).
    """

    def _cache_key(self, job_title: str, seniority: str, location: str) -> str:
        slug = f"{job_title}:{seniority}:{location}".lower().replace(" ", "_")
        return f"salary_benchmark:{slug}"

    def _fallback_benchmark(
        self, job_title: str, seniority: str, location: str
    ) -> SalaryBenchmark:
        seniority_lower = seniority.lower()
        data = _STATIC_SALARY_BENCHMARKS.get(
            seniority_lower, _STATIC_SALARY_BENCHMARKS["pleno"]
        )
        return SalaryBenchmark(
            job_title=job_title,
            seniority=seniority,
            location=location,
            p25=data["p25"],
            p50=data["p50"],
            p75=data["p75"],
            source="fallback",
            fetched_at=datetime.utcnow(),
        )

    async def get_benchmark(
        self,
        job_title: str,
        seniority: str,
        location: str,
        company_id: str,
    ) -> SalaryBenchmark:
        """
        Retorna benchmark salarial. Tenta cache Redis → Apify → fallback estático.
        Fail-open: sempre retorna um resultado válido.
        """
        # 1. Cache check
        try:
            from app.core.redis_client import get_redis
            redis = await get_redis()
            cache_key = self._cache_key(job_title, seniority, location)
            cached = await redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                logger.info("[SalaryBenchmark] Cache hit: %s", cache_key)
                return SalaryBenchmark(
                    job_title=data["job_title"],
                    seniority=data["seniority"],
                    location=data["location"],
                    p25=data["p25"],
                    p50=data["p50"],
                    p75=data["p75"],
                    currency=data.get("currency", "BRL"),
                    source=data.get("source", "external"),
                    fetched_at=datetime.fromisoformat(data["fetched_at"]) if data.get("fetched_at") else None,
                )
        except Exception as exc:
            logger.warning("[SalaryBenchmark] Redis cache error (skip): %s", exc)

        # 2. Apify scraping
        try:
            benchmark = await self._fetch_from_apify(job_title, seniority, location)
            if benchmark:
                await self._cache_result(benchmark)
                return benchmark
        except Exception as exc:
            logger.warning("[SalaryBenchmark] Apify fetch failed (fallback): %s", exc)

        # 3. Static fallback
        logger.info("[SalaryBenchmark] Using static fallback for %s/%s", job_title, seniority)
        return self._fallback_benchmark(job_title, seniority, location)

    async def _fetch_from_apify(
        self, job_title: str, seniority: str, location: str
    ) -> SalaryBenchmark | None:
        """Scrapes salary data via Apify Glassdoor actor."""
        try:
            from app.domains.sourcing.services.apify_service import ApifyService
            apify = ApifyService()
            result = await apify.scrape_salary_data(
                job_title=f"{seniority} {job_title}",
                location=location,
            )
            if not result or not result.get("salaries"):
                return None

            salaries = sorted(result["salaries"])
            n = len(salaries)
            p25 = salaries[int(n * 0.25)] if n >= 4 else salaries[0]
            p50 = salaries[n // 2]
            p75 = salaries[int(n * 0.75)] if n >= 4 else salaries[-1]

            return SalaryBenchmark(
                job_title=job_title,
                seniority=seniority,
                location=location,
                p25=float(p25),
                p50=float(p50),
                p75=float(p75),
                source="external",
                fetched_at=datetime.utcnow(),
            )
        except Exception as exc:
            logger.warning("[SalaryBenchmark] Apify scrape error: %s", exc)
            return None

    async def _cache_result(self, benchmark: SalaryBenchmark) -> None:
        try:
            from app.core.redis_client import get_redis
            redis = await get_redis()
            key = self._cache_key(benchmark.job_title, benchmark.seniority, benchmark.location)
            await redis.setex(key, REDIS_TTL_SECONDS, json.dumps(benchmark.to_dict()))
        except Exception as exc:
            logger.warning("[SalaryBenchmark] Redis cache write error: %s", exc)


salary_benchmark_service = SalaryBenchmarkService()
