"""
Job Management schemas — TypedDict definitions for typed returns.

R-026: replaces top-3 `dict[str, Any]` returns with typed structures.
- SearchCriteriaResult  — extract_search_criteria (vacancy_search_service.py)
- StageConfig           — get_stage_config (job_stage_config.py)
- AlertSummary          — get_alert_summary (job_alert_service.py)

These are TypedDicts (not Pydantic) to remain transparent at runtime —
no behavior change, only static type checking via mypy/pyright.
"""
from typing import TypedDict


class SearchCriteriaResult(TypedDict, total=False):
    """
    Criteria extracted from a natural language vacancy search message.

    Keys mirror both the LLM extraction prompt output and the regex fallback
    in VacancySearchService._extract_criteria_fallback().
    total=False because any subset of keys may be present.
    """
    cargo: str
    area: str
    senioridade: str
    modelo_trabalho: str
    ano: int


class StageConfig(TypedDict, total=False):
    """
    Configuration for a single stage of the Job Creation Wizard.

    Maps to entries in JOB_CREATION_STAGES (job_stage_config.py).
    total=False because get_stage_config() returns {} when stage not found,
    and optional keys (min_criteria, skip_message, use_skills_deduplication)
    only appear on specific stages.
    """
    stage: int
    name: str
    panel: str
    skip_if_confident: bool
    skippable_fields: list[str]
    confidence_threshold: float
    # Optional — stage-specific keys
    min_criteria: int
    use_skills_deduplication: bool
    skip_message: str


class AlertSummary(TypedDict):
    """
    Summary counts of active alerts by severity.

    All fields guaranteed present (total=True default).
    Returned by JobAlertService.get_alert_summary().
    """
    critical: int
    high: int
    medium: int
    low: int
    info: int
    total: int
