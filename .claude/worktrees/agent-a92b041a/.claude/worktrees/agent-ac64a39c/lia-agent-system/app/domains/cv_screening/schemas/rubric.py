"""
Pydantic schemas for Rubric Evaluation API.

Based on Schmidt & Hunter (1998) and BARS methodology.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class RequirementPriorityEnum(str, Enum):
    """Priority levels for job requirements."""
    ESSENTIAL = "essential"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice_to_have"


class EvaluationLevelEnum(str, Enum):
    """Evaluation levels based on BARS."""
    EXCEEDS = "exceeds"
    MEETS = "meets"
    PARTIAL = "partial"
    MISSING = "missing"


class EvidenceType(str, Enum):
    """Type of evidence supporting an evaluation."""
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    INFERRED = "inferred"


class JobRequirementCreate(BaseModel):
    """Schema for creating a job requirement."""
    requirement: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: RequirementPriorityEnum = RequirementPriorityEnum.IMPORTANT
    category: Optional[str] = None


class JobRequirementResponse(BaseModel):
    """Schema for job requirement response."""
    id: UUID
    job_vacancy_id: UUID
    requirement: str
    description: Optional[str] = None
    priority: str
    category: Optional[str] = None
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
    reasoning: Optional[str] = Field(None, description="Explanation for the evaluation")
    vague_language_detected: bool = Field(default=False, description="Whether vague language was detected")
    anomaly_flags: List[str] = Field(default_factory=list, description="Anomaly flags if any")


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
    evaluations: List[RequirementEvaluation] = Field(..., description="Individual requirement evaluations")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    concerns: List[str] = Field(default_factory=list, description="Identified concerns or gaps")
    reasoning: str = Field(..., description="Overall evaluation reasoning")
    recommendation: str = Field(..., description="Recommendation level based on score")
    anomaly_flags: List[str] = Field(default_factory=list, description="Global anomaly flags")
    auto_excluded: bool = Field(default=False, description="Auto-excluded due to essential requirements missing")
    exclusion_reasons: List[str] = Field(default_factory=list, description="Reasons for auto-exclusion")
    scoring_methodology: str = Field(default="andre_v1", description="Scoring methodology version")


class RubricEvaluationResponse(BaseModel):
    """API response for rubric evaluation."""
    id: Optional[UUID] = None
    candidate_id: UUID
    job_vacancy_id: UUID
    result: RubricEvaluationResult
    evaluated_at: datetime
    model_version: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluateCandidateRequest(BaseModel):
    """Request to evaluate a single candidate against job requirements."""
    candidate_id: UUID
    job_vacancy_id: UUID
    candidate_data: Optional[Dict[str, Any]] = Field(None, description="Optional candidate data if not fetching from DB")
    job_requirements: Optional[List[JobRequirementCreate]] = Field(None, description="Optional requirements if not fetching from DB")
    save_result: bool = Field(True, description="Whether to persist the evaluation result")


class BatchEvaluateRequest(BaseModel):
    """Request to evaluate multiple candidates against job requirements."""
    candidate_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    job_vacancy_id: UUID
    job_requirements: Optional[List[JobRequirementCreate]] = Field(None, description="Optional requirements if not fetching from DB")
    save_results: bool = Field(True, description="Whether to persist the evaluation results")


class BatchEvaluateResponse(BaseModel):
    """Response for batch evaluation."""
    job_vacancy_id: UUID
    total_candidates: int
    evaluated: int
    failed: int
    results: List[RubricEvaluationResponse]
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class LegacyScoreWrapper(BaseModel):
    """
    Wrapper to convert RubricEvaluationResult to legacy LIA Score format.
    Maintains backward compatibility during transition.
    """
    score: float
    breakdown: Dict[str, float]
    reasoning: str
    matched_skills: List[str]
    missing_skills: List[str]
    strengths: List[str]
    concerns: List[str]

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
