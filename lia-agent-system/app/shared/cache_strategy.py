"""
Cache Strategy — Single source of truth for ALL cache configuration.

Defines two enum registries consumed by different cache layers:

  CacheDomain   — endpoint/service-level caching with event-driven invalidation.
                  Used via ``CacheStrategy.get_ttl / .build_key / .invalidate``.

  CacheNamespace — multi-layer persistence (Session → Redis → PostgreSQL)
                   with semantic similarity matching.  Used by
                   ``app.shared.resilience.cache_manager_service.CacheManagerService``.

Every cache-related TTL, namespace, invalidation rule, and layer config is
defined HERE.  No other module should define cache configuration.

Usage:
    from app.shared.cache_strategy import CacheStrategy, CacheDomain
    from app.shared.cache_strategy import CacheNamespace, CacheTTL, CacheConfig, NAMESPACE_CACHE_CONFIGS

    ttl = CacheStrategy.get_ttl(CacheDomain.CANDIDATE_SEARCH)
    key = CacheStrategy.build_key(CacheDomain.CANDIDATE_SEARCH, company_id, query="python")
    CacheStrategy.invalidate(CacheDomain.JOB_VACANCY, job_id="123")
"""
import hashlib
import json
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)


class CacheDomain(StrEnum):
    CANDIDATE_SEARCH = "candidate_search"
    CANDIDATE_PROFILE = "candidate_profile"
    JOB_VACANCY = "job_vacancy"
    JOB_DESCRIPTION = "job_description"
    WSI_SCORE = "wsi_score"
    PIPELINE_STAGES = "pipeline_stages"
    COMPANY_CONFIG = "company_config"
    SKILL_CATALOG = "skill_catalog"
    LLM_RESPONSE = "llm_response"
    TEMPLATE = "template"
    ANALYTICS = "analytics"
    ROUTING = "routing"


DOMAIN_TTL_CONFIG: dict[CacheDomain, dict[str, Any]] = {
    CacheDomain.CANDIDATE_SEARCH: {
        "ttl_seconds": 300,
        "description": "Search results cache",
        "invalidate_on": ["candidate_update", "candidate_create"],
    },
    CacheDomain.CANDIDATE_PROFILE: {
        "ttl_seconds": 600,
        "description": "Individual candidate profile",
        "invalidate_on": ["candidate_update"],
    },
    CacheDomain.JOB_VACANCY: {
        "ttl_seconds": 300,
        "description": "Job vacancy data",
        "invalidate_on": ["job_update", "job_create", "job_close"],
    },
    CacheDomain.JOB_DESCRIPTION: {
        "ttl_seconds": 1800,
        "description": "Generated job descriptions",
        "invalidate_on": ["job_update", "jd_regenerate"],
    },
    CacheDomain.WSI_SCORE: {
        "ttl_seconds": 3600,
        "description": "WSI assessment scores",
        "invalidate_on": ["screening_complete", "candidate_update"],
    },
    CacheDomain.PIPELINE_STAGES: {
        "ttl_seconds": 1800,
        "description": "Pipeline stage configurations",
        "invalidate_on": ["stage_update", "company_config_update"],
    },
    CacheDomain.COMPANY_CONFIG: {
        "ttl_seconds": 3600,
        "description": "Company configuration and settings",
        "invalidate_on": ["company_config_update"],
    },
    CacheDomain.SKILL_CATALOG: {
        "ttl_seconds": 86400,
        "description": "Skill taxonomy catalog",
        "invalidate_on": ["skill_catalog_update"],
    },
    CacheDomain.LLM_RESPONSE: {
        "ttl_seconds": 900,
        "description": "Cached LLM responses (semantic cache)",
        "invalidate_on": ["prompt_update", "model_change"],
    },
    CacheDomain.TEMPLATE: {
        "ttl_seconds": 86400,
        "description": "Job and communication templates",
        "invalidate_on": ["template_update"],
    },
    CacheDomain.ANALYTICS: {
        "ttl_seconds": 600,
        "description": "Analytics and dashboard data",
        "invalidate_on": ["pipeline_change", "candidate_update"],
    },
    CacheDomain.ROUTING: {
        "ttl_seconds": 1800,
        "description": "Domain routing cache",
        "invalidate_on": ["routing_config_update"],
    },
}


class CacheNamespace(StrEnum):
    SALARY_BENCHMARK = "salary_benchmark"
    MARKET_DATA = "market_data"
    SKILLS_SUGGESTIONS = "skills_suggestions"
    JD_SUMMARY = "jd_summary"
    COMPANY_CONFIG = "company_config"
    LEARNING_PATTERNS = "learning_patterns"
    LLM_RESPONSE = "llm_response"
    EMBEDDINGS = "embeddings"


class CacheTTL:
    SESSION = 3600
    VOLATILE = 86400
    STANDARD = 604800
    STABLE = 2592000
    PERMANENT = 0


@dataclass
class CacheConfig:
    namespace: CacheNamespace
    redis_ttl: int = CacheTTL.STANDARD
    postgres_ttl: int = CacheTTL.STABLE
    use_redis: bool = True
    use_postgres: bool = True
    use_embeddings: bool = False
    similarity_threshold: float = 0.85


NAMESPACE_CACHE_CONFIGS: dict[CacheNamespace, CacheConfig] = {
    CacheNamespace.SALARY_BENCHMARK: CacheConfig(
        namespace=CacheNamespace.SALARY_BENCHMARK,
        redis_ttl=CacheTTL.STANDARD,
        postgres_ttl=CacheTTL.STABLE,
        use_embeddings=True,
        similarity_threshold=0.90,
    ),
    CacheNamespace.MARKET_DATA: CacheConfig(
        namespace=CacheNamespace.MARKET_DATA,
        redis_ttl=CacheTTL.STANDARD,
        postgres_ttl=CacheTTL.STABLE,
    ),
    CacheNamespace.SKILLS_SUGGESTIONS: CacheConfig(
        namespace=CacheNamespace.SKILLS_SUGGESTIONS,
        redis_ttl=CacheTTL.STABLE,
        postgres_ttl=CacheTTL.STABLE,
        use_embeddings=True,
    ),
    CacheNamespace.JD_SUMMARY: CacheConfig(
        namespace=CacheNamespace.JD_SUMMARY,
        redis_ttl=CacheTTL.VOLATILE,
        postgres_ttl=CacheTTL.STANDARD,
    ),
    CacheNamespace.COMPANY_CONFIG: CacheConfig(
        namespace=CacheNamespace.COMPANY_CONFIG,
        redis_ttl=CacheTTL.VOLATILE,
        postgres_ttl=CacheTTL.STABLE,
    ),
    CacheNamespace.LEARNING_PATTERNS: CacheConfig(
        namespace=CacheNamespace.LEARNING_PATTERNS,
        redis_ttl=CacheTTL.STABLE,
        postgres_ttl=CacheTTL.STABLE,
        use_redis=False,
    ),
    CacheNamespace.LLM_RESPONSE: CacheConfig(
        namespace=CacheNamespace.LLM_RESPONSE,
        redis_ttl=CacheTTL.VOLATILE,
        postgres_ttl=CacheTTL.STANDARD,
        use_embeddings=True,
        similarity_threshold=0.95,
    ),
    CacheNamespace.EMBEDDINGS: CacheConfig(
        namespace=CacheNamespace.EMBEDDINGS,
        redis_ttl=CacheTTL.STABLE,
        postgres_ttl=CacheTTL.STABLE,
        use_redis=False,
    ),
}

DEFAULT_CACHE_CONFIGS = NAMESPACE_CACHE_CONFIGS


class CacheStrategy:
    @staticmethod
    def get_ttl(domain: CacheDomain) -> int:
        config = DOMAIN_TTL_CONFIG.get(domain)
        return config["ttl_seconds"] if config else 300

    @staticmethod
    def build_key(domain: CacheDomain, company_id: str | None = None, **kwargs) -> str:
        """Build a tenant-namespaced cache key.

        Task #1144: ``company_id`` is required. Shape:
        ``lia:<domain>:<company_id>:<md5(sorted_kwargs)[:12]>``. Missing
        ``company_id`` records a namespace violation and falls back to the
        ``__unknown__`` tenant (sentinel S9 will flag the leak).
        """
        sorted_params = json.dumps(kwargs, sort_keys=True, default=str)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        from app.shared.security.tenant_redis_namespace import (
            record_namespace_violation,
            tenant_namespaced_key,
        )
        if not company_id:
            # Task #1144 — fail-loud: in production record_namespace_violation
            # raises RuntimeError; in dev/test it logs CRITICAL and we keep
            # going with a clearly-marked unknown bucket so the test suite
            # can observe the violation without crashing.
            record_namespace_violation(f"cache_strategy.{domain.value}")
            return f"lia:{domain.value}:__unknown__:{param_hash}"
        # Let any helper failure propagate — no broad except / no fallback
        # f-string that could leak a malformed key past the central gate.
        return tenant_namespaced_key(f"lia:{domain.value}", company_id, param_hash)

    @staticmethod
    def get_invalidation_events(domain: CacheDomain) -> list[str]:
        config = DOMAIN_TTL_CONFIG.get(domain)
        return config.get("invalidate_on", []) if config else []

    @staticmethod
    def get_domains_for_event(event: str) -> list[CacheDomain]:
        affected = []
        for domain, config in DOMAIN_TTL_CONFIG.items():
            if event in config.get("invalidate_on", []):
                affected.append(domain)
        return affected

    @staticmethod
    def get_all_ttls() -> dict[str, dict[str, Any]]:
        return {
            domain.value: {
                "ttl_seconds": config["ttl_seconds"],
                "ttl_human": _format_ttl(config["ttl_seconds"]),
                "description": config["description"],
                "invalidate_on": config.get("invalidate_on", []),
            }
            for domain, config in DOMAIN_TTL_CONFIG.items()
        }


def _format_ttl(seconds: int) -> str:
    if seconds >= 86400:
        return f"{seconds // 86400}d"
    if seconds >= 3600:
        return f"{seconds // 3600}h"
    if seconds >= 60:
        return f"{seconds // 60}m"
    return f"{seconds}s"


import os as _os

# Fase 7: Moved from app.config.cache_config (LIA-D05 consolidation)
class CacheSettings:
    """Cache configuration settings loaded from environment."""
    
    REDIS_URL: str | None = _os.environ.get("REDIS_URL")
    CACHE_ENABLED: bool = _os.environ.get("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_DEFAULT: int = int(_os.environ.get("CACHE_TTL_DEFAULT", "300"))
    CACHE_TTL_PIPELINE_STATS: int = int(_os.environ.get("CACHE_TTL_PIPELINE_STATS", "60"))
    CACHE_TTL_CANDIDATE_SEARCH: int = int(_os.environ.get("CACHE_TTL_CANDIDATE_SEARCH", "120"))
    CACHE_TTL_JOB_INSIGHTS: int = int(_os.environ.get("CACHE_TTL_JOB_INSIGHTS", "180"))
    CACHE_TTL_ANALYTICS: int = int(_os.environ.get("CACHE_TTL_ANALYTICS", "90"))
    CACHE_MAX_MEMORY_ENTRIES: int = int(_os.environ.get("CACHE_MAX_MEMORY_ENTRIES", "1000"))
    
    @classmethod
    def get_ttl_for_intent(cls, intent: str) -> int:
        """Get the appropriate TTL for a given intent."""
        intent_ttl_mapping = {
            "pipeline_stats": cls.CACHE_TTL_PIPELINE_STATS,
            "candidate_search": cls.CACHE_TTL_CANDIDATE_SEARCH,
            "job_insights": cls.CACHE_TTL_JOB_INSIGHTS,
            "analytics": cls.CACHE_TTL_ANALYTICS,
            "job_status": 60,
            "candidate_count": 60,
            "stage_distribution": 60,
            "funnel_analysis": 120,
            "market_data": 300,
            "salary_benchmark": 600,
            "recommendations": 180,
            "skills_analysis": 240,
        }
        return intent_ttl_mapping.get(intent, cls.CACHE_TTL_DEFAULT)
    
    @classmethod
    def to_dict(cls) -> dict:
        """Return settings as dictionary."""
        return {
            "redis_url": cls.REDIS_URL is not None,
            "cache_enabled": cls.CACHE_ENABLED,
            "cache_ttl_default": cls.CACHE_TTL_DEFAULT,
            "cache_ttl_pipeline_stats": cls.CACHE_TTL_PIPELINE_STATS,
            "cache_ttl_candidate_search": cls.CACHE_TTL_CANDIDATE_SEARCH,
            "cache_ttl_job_insights": cls.CACHE_TTL_JOB_INSIGHTS,
            "cache_ttl_analytics": cls.CACHE_TTL_ANALYTICS,
            "cache_max_memory_entries": cls.CACHE_MAX_MEMORY_ENTRIES,
        }


cache_settings = CacheSettings()
