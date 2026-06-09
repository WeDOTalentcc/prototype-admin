"""WSI typed structures (UC-P2-06).

TypedDicts for wsi_repository return types and wsi_screening_pipeline results.
All fields derived from the actual SQL queries executed in wsi_repository.py.
"""
from __future__ import annotations

from typing import TypedDict


# ---------------------------------------------------------------------------
# wsi_sessions
# ---------------------------------------------------------------------------


class WsiSessionRow(TypedDict):
    """Row returned by WsiRepository.get_session().

    Maps columns from:
      SELECT id, candidate_id, job_vacancy_id, screening_type, mode,
             status, started_at, completed_at
      FROM wsi_sessions
    """

    id: str
    candidate_id: str
    job_vacancy_id: str
    screening_type: str
    mode: str
    status: str
    started_at: str | None
    completed_at: str | None


# ---------------------------------------------------------------------------
# wsi_results
# ---------------------------------------------------------------------------


class WsiResultRow(TypedDict):
    """Row returned by WsiRepository.get_result_with_session().

    Maps columns from wsi_results JOIN wsi_sessions.
    """

    id: str
    session_id: str
    candidate_id: str
    job_vacancy_id: str
    technical_wsi: float
    behavioral_wsi: float
    overall_wsi: float
    classification: str
    percentile: int | None
    created_at: str
    screening_type: str
    mode: str
    started_at: str | None
    completed_at: str | None


class WsiVacancyAveragesRow(TypedDict):
    """Row returned by WsiRepository.get_vacancy_averages().

    Three ROUND(AVG(...)) columns — overall, technical, behavioral.
    """

    avg_overall_wsi: float | None
    avg_technical_wsi: float | None
    avg_behavioral_wsi: float | None


class WsiCandidateRankRow(TypedDict):
    """Row returned by WsiRepository.get_candidate_rank_in_vacancy().

    From the ranked CTE: rank_position, total_candidates, overall_wsi.
    """

    rank_position: int
    total_candidates: int
    overall_wsi: float


# ---------------------------------------------------------------------------
# wsi_reports / wsi_feedbacks
# ---------------------------------------------------------------------------


class WsiReportRow(TypedDict):
    """Row returned by WsiRepository.get_report_for_result().

    Columns: executive_summary, technical_analysis, behavioral_analysis,
             cultural_fit, recommendation.
    """

    executive_summary: str | None
    technical_analysis: str | None
    behavioral_analysis: str | None
    cultural_fit: str | None
    recommendation: str | None


class WsiFeedbackRow(TypedDict):
    """Row returned by WsiRepository.get_feedback_for_result().

    Columns from wsi_feedbacks.
    """

    decision: str | None
    main_message: str | None
    technical_strengths: str | None
    development_opportunities: str | None
    behavioral_strengths: str | None
    next_steps: str | None
    personalized_tip: str | None


# ---------------------------------------------------------------------------
# wsi_questions
# ---------------------------------------------------------------------------


class WsiQuestionTextRow(TypedDict):
    """Row returned by WsiRepository.get_question_text_and_competency()."""

    question_text: str
    competency: str


# ---------------------------------------------------------------------------
# job_vacancies
# ---------------------------------------------------------------------------


class WsiJobVacancyContextRow(TypedDict):
    """Row returned by WsiRepository.get_job_vacancy_context()."""

    title: str
    description: str | None
    seniority_level: str | None


# ---------------------------------------------------------------------------
# Screening pipeline results
# ---------------------------------------------------------------------------


class ScreeningPolicyResult(TypedDict):
    """Result of WsiScreeningPipelineService.apply_screening_policy().

    Contains the processed questions list and a flag indicating whether
    a company policy was found and applied.
    """

    questions: list  # list[UnifiedScreeningQuestion] — avoid circular import
    policy_applied: bool


class ScreeningPolicyConfig(TypedDict):
    """Result of WsiScreeningPipelineService.get_screening_policy().

    Effective screening configuration for a company, sourced from policy_middleware.
    """

    experience_policy: str
    default_screening_questions: list[str]
    salary_expectation_filter: bool
    salary_tolerance_percent: int
