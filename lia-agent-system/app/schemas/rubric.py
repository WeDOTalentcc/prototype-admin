"""
Pydantic schemas for Rubric Evaluation API.

Based on Schmidt & Hunter (1998) and BARS methodology.
"""
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


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


class JobRequirementCreate(WeDoBaseModel):
    """Schema for creating a job requirement."""
    requirement: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    priority: RequirementPriorityEnum = RequirementPriorityEnum.IMPORTANT
    category: str | None = None


class JobRequirementResponse(BaseModel):
    """Schema for job requirement response."""
    id: UUID
    job_vacancy_id: UUID
    requirement: str
    description: str | None = None
    priority: str
    category: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RequirementEvaluation(BaseModel):
    """Individual requirement evaluation result."""
    requirement: str = Field(..., description="The requirement being evaluated")
    priority: RequirementPriorityEnum = Field(..., description="Priority level of the requirement")
    level: EvaluationLevelEnum = Field(..., description="Evaluation level achieved")
    evidence_type: EvidenceType = Field(default=EvidenceType.EXPLICIT, description="Type of evidence: explicit, implicit, or inferred")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for this evaluation")
    points: int = Field(..., ge=0, le=100, description="Base points (0, 40, 75, or 100)")
    multiplier: int = Field(..., ge=1, le=3, description="Priority multiplier (1, 2, or 3)")
    weighted_points: float = Field(..., description="Points × Multiplier")
    max_weighted_points: float = Field(..., description="100 × Multiplier")
    evidence: str = Field(..., description="Specific quote or evidence from CV")
    reasoning: str | None = Field(None, description="Explanation for the evaluation")
    vague_language_detected: bool = Field(default=False, description="Whether vague language was detected")
    anomaly_flags: list[str] = Field(default_factory=list, description="Anomaly flags if any")


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
    consent_warnings: list[str] = Field(default_factory=list, description="LGPD: avisos de consentimento ausente (soft enforcement)")
    fairness_warnings: list[str] = Field(
        default_factory=list,
        description="DEI: avisos de viés implícito detectados pelo FairnessGuard no output do LLM"
    )


class RubricEvaluationResponse(BaseModel):
    """API response for rubric evaluation."""
    id: UUID | None = None
    candidate_id: UUID
    job_vacancy_id: UUID
    result: RubricEvaluationResult
    evaluated_at: datetime
    model_version: str | None = None

    class Config:
        from_attributes = True


class EvaluateCandidateRequest(WeDoBaseModel):
    """Request to evaluate a single candidate against job requirements."""
    candidate_id: UUID
    job_vacancy_id: UUID
    candidate_data: dict[str, Any] | None = Field(None, description="Optional candidate data if not fetching from DB")
    job_requirements: list[JobRequirementCreate] | None = Field(None, description="Optional requirements if not fetching from DB")
    save_result: bool = Field(True, description="Whether to persist the evaluation result")


class BatchEvaluateRequest(WeDoBaseModel):
    """Request to evaluate multiple candidates against job requirements."""
    candidate_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    job_vacancy_id: UUID
    job_requirements: list[JobRequirementCreate] | None = Field(None, description="Optional requirements if not fetching from DB")
    save_results: bool = Field(True, description="Whether to persist the evaluation results")


class BatchEvaluateResponse(BaseModel):
    """Response for batch evaluation."""
    job_vacancy_id: UUID
    total_candidates: int
    evaluated: int
    failed: int
    results: list[RubricEvaluationResponse]
    errors: list[dict[str, Any]] = Field(default_factory=list)


class LegacyScoreWrapper(BaseModel):
    """
    Wrapper to convert RubricEvaluationResult to legacy LIA Score format.
    Maintains backward compatibility during transition.
    """
    score: float
    breakdown: dict[str, float]
    reasoning: str
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    concerns: list[str]

    @classmethod
    def from_rubric_result(cls, result: RubricEvaluationResult) -> "LegacyScoreWrapper":
        """Convert rubric result to legacy format."""
        matched = [
            e.requirement for e in result.evaluations 
            if e.level in [EvaluationLevelEnum.EXCEEDS, EvaluationLevelEnum.MEETS]
        ]
        missing = [
            e.requirement for e in result.evaluations 
            if e.level == EvaluationLevelEnum.MISSING
        ]
        
        essential_score = 0.0
        essential_count = 0
        important_score = 0.0
        important_count = 0
        
        for e in result.evaluations:
            if e.priority == RequirementPriorityEnum.ESSENTIAL:
                essential_score += e.points
                essential_count += 1
            elif e.priority == RequirementPriorityEnum.IMPORTANT:
                important_score += e.points
                important_count += 1
        
        breakdown = {
            "skills_match": result.score,
            "experience_match": essential_score / essential_count if essential_count > 0 else 0,
            "seniority_match": important_score / important_count if important_count > 0 else 0,
            "location_match": 100.0,  # Not evaluated in rubrics
            "title_match": 100.0,     # Not evaluated in rubrics
        }
        
        return cls(
            score=result.score,
            breakdown=breakdown,
            reasoning=result.reasoning,
            matched_skills=matched,
            missing_skills=missing,
            strengths=result.strengths,
            concerns=result.concerns,
        )
