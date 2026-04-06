"""
Cache Invalidation Strategy - Standardized TTLs and invalidation helpers.

Provides domain-specific TTL configurations and cache invalidation utilities
to ensure consistent caching behavior across the platform.

Usage:
    from app.shared.cache_strategy import CacheStrategy, CacheDomain
    
    ttl = CacheStrategy.get_ttl(CacheDomain.CANDIDATE_SEARCH)
    key = CacheStrategy.build_key(CacheDomain.CANDIDATE_SEARCH, query="python", location="sp")
    CacheStrategy.invalidate(CacheDomain.JOB_VACANCY, job_id="123")
"""
import hashlib
import json
import logging
from enum import Enum, StrEnum
from typing import Any

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


class CacheStrategy:
    @staticmethod
    def get_ttl(domain: CacheDomain) -> int:
        config = DOMAIN_TTL_CONFIG.get(domain)
        return config["ttl_seconds"] if config else 300

    @staticmethod
    def build_key(domain: CacheDomain, **kwargs) -> str:
        sorted_params = json.dumps(kwargs, sort_keys=True, default=str)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        return f"lia:{domain.value}:{param_hash}"

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
