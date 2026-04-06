"""Hiring Policy Action dataclasses — LIA Sprint 3 T05"""
from dataclasses import dataclass, field


@dataclass
class CheckDiversityAction:
    job_id: str
    current_pipeline: dict = field(default_factory=dict)


@dataclass
class ValidateRequirementsAction:
    job_id: str
    requirements_text: str


@dataclass
class GenerateExplanationAction:
    candidate_id: str
    decision: str
    decision_factors: list[str] = field(default_factory=list)


@dataclass
class AuditDecisionAction:
    job_id: str
    candidate_id: str
    decision: str
    reviewer_id: str
