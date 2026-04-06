"""
Cache Configuration for LIA Response Caching

Environment Variables:
- REDIS_URL: Redis connection URL (optional)
- CACHE_ENABLED: Enable/disable caching (default: true)
- CACHE_TTL_DEFAULT: Default TTL in seconds (default: 300)
- CACHE_TTL_PIPELINE_STATS: TTL for pipeline stats (default: 60)
- CACHE_TTL_CANDIDATE_SEARCH: TTL for candidate search (default: 120)
"""

import os


class CacheSettings:
    """Cache configuration settings loaded from environment."""
    
    REDIS_URL: str | None = os.environ.get("REDIS_URL")
    CACHE_ENABLED: bool = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_DEFAULT: int = int(os.environ.get("CACHE_TTL_DEFAULT", "300"))
    CACHE_TTL_PIPELINE_STATS: int = int(os.environ.get("CACHE_TTL_PIPELINE_STATS", "60"))
    CACHE_TTL_CANDIDATE_SEARCH: int = int(os.environ.get("CACHE_TTL_CANDIDATE_SEARCH", "120"))
    CACHE_TTL_JOB_INSIGHTS: int = int(os.environ.get("CACHE_TTL_JOB_INSIGHTS", "180"))
    CACHE_TTL_ANALYTICS: int = int(os.environ.get("CACHE_TTL_ANALYTICS", "90"))
    CACHE_MAX_MEMORY_ENTRIES: int = int(os.environ.get("CACHE_MAX_MEMORY_ENTRIES", "1000"))
    
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
