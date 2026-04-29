"""
Wizard stage validators — computacional sensor (Frente D).
Each validator: validate_<stage>(job_draft: dict) -> list[str]
Returns list of missing_fields (empty = all good).
Fail-open: exceptions are caught and logged, never propagate.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

STAGE_VALIDATORS: dict[str, Any] = {}  # populated at bottom


def validate_stage(stage_name: str, job_draft: dict) -> list[str]:
    """Dispatch to the correct stage validator. Returns [] if stage unknown."""
    validator = STAGE_VALIDATORS.get(stage_name)
    if not validator:
        return []
    try:
        return validator(job_draft)
    except Exception as exc:
        logger.warning("Stage validator error for stage '%s': %s", stage_name, exc)
        return []


def _validate_description(job_draft: dict) -> list[str]:
    missing = []
    if not (job_draft or {}).get("job_title", "").strip():
        missing.append("job_title")
    if not (job_draft or {}).get("seniority", "").strip():
        missing.append("seniority")
    return missing


def _validate_basic_info(job_draft: dict) -> list[str]:
    missing = []
    d = job_draft or {}
    if not d.get("num_positions") and not d.get("department"):
        missing.append("num_positions_or_department")
    return missing


def _validate_competencies(job_draft: dict) -> list[str]:
    missing = []
    d = job_draft or {}
    skills = d.get("detected_skills") or d.get("competenciasTecnicas") or []
    if not skills:
        missing.append("detected_skills")
    return missing


def _validate_salary(job_draft: dict) -> list[str]:
    missing = []
    d = job_draft or {}
    if not d.get("salary_min") and not d.get("salary_disclosed"):
        missing.append("salary_min_or_salary_disclosed")
    return missing


def _validate_wsi(job_draft: dict) -> list[str]:
    missing = []
    d = job_draft or {}
    questions = d.get("wsi_questions") or []
    if len(questions) < 3:
        missing.append("wsi_questions_min_3")
    return missing


def _validate_review(job_draft: dict) -> list[str]:
    missing = []
    d = job_draft or {}
    jd = d.get("job_description") or d.get("enriched_jd") or ""
    if len(str(jd)) < 150:
        missing.append("job_description_min_150_chars")
    return missing


STAGE_VALIDATORS = {
    "description": _validate_description,
    "basic-info": _validate_basic_info,
    "competencies": _validate_competencies,
    "salary": _validate_salary,
    "wsi-questions": _validate_wsi,
    "review": _validate_review,
}
