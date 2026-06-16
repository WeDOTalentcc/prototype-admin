"""
Orchestrator intents and scope constants.

Replaces magic strings used in orchestrator.py for intent classification,
caching decisions, and scope mapping.
"""
from enum import StrEnum


class CacheableIntent(StrEnum):
    """Intents whose responses are safe to cache."""
    PIPELINE_STATS = "pipeline_stats"
    JOB_STATUS = "job_status"
    CANDIDATE_COUNT = "candidate_count"
    STAGE_DISTRIBUTION = "stage_distribution"
    FUNNEL_ANALYSIS = "funnel_analysis"
    JOB_INSIGHTS = "job_insights"
    MARKET_DATA = "market_data"
    SALARY_BENCHMARK = "salary_benchmark"
    ANALYTICS = "analytics"
    RECOMMENDATIONS = "recommendations"
    SKILLS_ANALYSIS = "skills_analysis"
    CANDIDATE_SEARCH = "candidate_search"


class OrchestratorScope(StrEnum):
    """Frontend scope identifiers used for tool/prompt filtering."""
    TALENT_FUNNEL = "talent_funnel"
    JOB_TABLE = "job_table"
    IN_JOB = "in_job"
    GLOBAL = "global"
    PIPELINE = "pipeline"
    CANDIDATES = "candidates"
    JOBS = "jobs"
    VACANCIES = "vacancies"
