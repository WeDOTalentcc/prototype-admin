"""
Pydantic schemas for Rubric Evaluation API.

Based on Schmidt & Hunter (1998) and BARS methodology.
"""
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RequirementPriorityEnum(StrEnum):
    """Priority levels for job requirements."""
    ESSENTIAL = "essential"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice_to_have"


class EvaluationLevelEnum(StrEnum):
    """Evaluation levels based on BARS."""
    EXCEEDS = "exceeds"
    MEETS = "meets"
    PARTIAL = "partial"
    MISSING = "missing"


class EvidenceType(StrEnum):
    """Type of evidence supporting an evaluation."""
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    INFERRED = "inferred"


# Sprint F.3 #25 canonical-fix: JobRequirementCreate moved to schemas/rubric.py
from app.schemas.rubric import JobRequirementCreate  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: JobRequirementResponse moved to schemas/rubric.py
from app.schemas.rubric import JobRequirementResponse  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: RequirementEvaluation moved to schemas/rubric.py
from app.schemas.rubric import RequirementEvaluation  # noqa: F401  (re-export for backward compat)


# DUPLICATE_OF_INTENT: app/schemas/rubric.py — domain-internal subset of canonical rubric schema (Sprint Q.1 triagem I bucket)
class RubricEvaluationResult(BaseModel):
    """Complete rubric evaluation result.
    
    André's Methodology (Phase 3):
    - Cap 99: Maximum score is 99, never 100 (ensures human review margin)
    - Floor: Scores are rounded to integers (eliminates decimal noise, e.g. 84.98 ≈ 85)
    - Evidence weights: explicit=1.0, implicit=0.7, inferred=0.3
    - Auto-exclusion: Essential requirements with missing/non-explicit evidence
    """
    score: float = Field(..., ge=0, le=99, description="Final score 0-99 (Cap 99 per André's methodology)")
    raw_score: float = Field(default=0.0, ge=0, description="Score before cap/floor/evidence adjustments")
    total_weighted_points: float = Field(..., description="Sum of all weighted points (with evidence weights)")
    max_possible_points: float = Field(..., description="Maximum possible weighted points")
    evaluations: list[RequirementEvaluation] = Field(..., description="Individual requirement evaluations")
    strengths: list[str] = Field(default_factory=list, description="Identified strengths")
    concerns: list[str] = Field(default_factory=list, description="Identified concerns or gaps")
    reasoning: str = Field(..., description="Overall evaluation reasoning")
    recommendation: str = Field(..., description="Recommendation level based on score")
    anomaly_flags: list[str] = Field(default_factory=list, description="Global anomaly flags")
    auto_excluded: bool = Field(default=False, description="Auto-excluded due to essential requirements missing")
    exclusion_reasons: list[str] = Field(default_factory=list, description="Reasons for auto-exclusion")
    scoring_methodology: str = Field(default="andre_v1", description="Scoring methodology version")


# Sprint F.3 #25 canonical-fix: RubricEvaluationResponse moved to schemas/rubric.py
from app.schemas.rubric import RubricEvaluationResponse  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: EvaluateCandidateRequest moved to schemas/rubric.py
from app.schemas.rubric import EvaluateCandidateRequest  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: BatchEvaluateRequest moved to schemas/rubric.py
from app.schemas.rubric import BatchEvaluateRequest  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: BatchEvaluateResponse moved to schemas/rubric.py
from app.schemas.rubric import BatchEvaluateResponse  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: LegacyScoreWrapper moved to schemas/rubric.py
from app.schemas.rubric import LegacyScoreWrapper  # noqa: F401  (re-export for backward compat)
