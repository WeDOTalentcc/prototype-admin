"""
Centralized interview stage defaults — single source of truth.

Derives canonical interview-relevant stages from DEFAULT_RECRUITMENT_STAGES
and exposes helpers that convert them to the two InterviewStage schemas used
across the platform:
  - job_description.InterviewStage  (JD generation)
  - job_vacancy_state.InterviewStage  (vacancy creation via wizard)
"""
import logging
from typing import Any

from lia_models.recruitment_stages import DEFAULT_RECRUITMENT_STAGES

logger = logging.getLogger(__name__)

INTERVIEW_RELEVANT_NAMES = frozenset({
    "screening",
    "interview_hr",
    "interview_technical",
    "interview_manager",
    "offer",
})

_BEHAVIOR_JD_FORMAT = {
    "screening": "WhatsApp",
    "scheduling": "Vídeo",
    "evaluation": "Online/Presencial",
    "offer": "-",
}

_BEHAVIOR_JD_DURATION = {
    "screening": "~10 min",
    "scheduling": "45 min",
    "evaluation": "60 min",
    "offer": "5-7 dias úteis",
}

_BEHAVIOR_VACANCY_FORMAT = {
    "screening": "Triagem",
    "scheduling": "Comportamental",
    "evaluation": "Técnica",
    "offer": "Proposta",
}

_BEHAVIOR_VACANCY_DURATION = {
    "screening": 10,
    "scheduling": 45,
    "evaluation": 60,
    "offer": 30,
}


def _canonical_stage_defs() -> list[dict[str, Any]]:
    return [
        s for s in DEFAULT_RECRUITMENT_STAGES
        if s["name"] in INTERVIEW_RELEVANT_NAMES
    ]


def get_default_jd_interview_stages():
    from app.schemas.job_description import InterviewStage

    result = []
    for i, s in enumerate(_canonical_stage_defs(), 1):
        behavior = s.get("action_behavior", "passive")
        result.append(InterviewStage(
            order=i,
            name=s["display_name"],
            format=_BEHAVIOR_JD_FORMAT.get(behavior, "-"),
            duration=_BEHAVIOR_JD_DURATION.get(behavior, "-"),
            description=s.get("description") or s["display_name"],
        ))
    return result


def get_default_vacancy_interview_stages():
    from app.schemas.job_vacancy_state import InterviewStage

    result = []
    for s in _canonical_stage_defs():
        behavior = s.get("action_behavior", "passive")
        result.append(InterviewStage(
            stage_name=s["display_name"],
            interviewers=[],
            format=_BEHAVIOR_VACANCY_FORMAT.get(behavior, "Informativa"),
            duration=_BEHAVIOR_VACANCY_DURATION.get(behavior, 30),
            scheduling_window="A definir",
        ))
    return result


def map_pipeline_to_jd_stages(stages) -> list:
    from app.schemas.job_description import InterviewStage

    result = []
    for stage in stages:
        behavior = getattr(stage, "action_behavior", "passive") or "passive"
        if behavior == "terminal":
            continue
        if any(getattr(stage, f, False) for f in ("is_rejection", "is_hired", "is_final")):
            continue
        result.append(InterviewStage(
            order=stage.stage_order,
            name=stage.display_name,
            format=_BEHAVIOR_JD_FORMAT.get(behavior, "-"),
            duration=_BEHAVIOR_JD_DURATION.get(behavior, "-"),
            description=stage.description or stage.display_name,
        ))
    return result


def map_pipeline_to_vacancy_stages(stages) -> list:
    from app.schemas.job_vacancy_state import InterviewStage

    result = []
    for stage in stages:
        behavior = getattr(stage, "action_behavior", "passive") or "passive"
        if behavior == "terminal":
            continue
        if any(getattr(stage, f, False) for f in ("is_rejection", "is_hired", "is_final")):
            continue
        result.append(InterviewStage(
            stage_name=stage.display_name,
            interviewers=[],
            format=_BEHAVIOR_VACANCY_FORMAT.get(behavior, "Informativa"),
            duration=_BEHAVIOR_VACANCY_DURATION.get(behavior, 30),
            scheduling_window="A definir",
        ))
    return result
