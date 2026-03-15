"""
Structured Response Models for LLM outputs.

Pydantic models that define the expected structure of LLM responses,
enabling direct parsing without manual JSON extraction.
"""
from typing import Any, Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field


class JobFieldUpdate(BaseModel):
    """Represents a single field update from LLM analysis."""
    field_name: str = Field(..., description="Name of the job field being updated")
    value: Any = Field(..., description="The value to set for this field")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence score 0-1")
    reasoning: Optional[str] = Field(default=None, description="Explanation for this update")


class OrchestrationDecision(BaseModel):
    """Decision from the orchestrator about what action to take."""
    action: Literal["respond", "advance_stage", "update_fields", "request_clarification"] = Field(
        ..., description="The action to take"
    )
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence in this decision")
    response_text: Optional[str] = Field(
        default=None, description="Text response to show the user"
    )
    field_updates: List[JobFieldUpdate] = Field(
        default_factory=list, description="List of field updates to apply"
    )
    target_stage: Optional[str] = Field(
        default=None, description="Target stage if advancing"
    )
    clarification_needed: Optional[str] = Field(
        default=None, description="What clarification is needed from user"
    )


class IntentClassification(BaseModel):
    """Classification of user intent from their message."""
    intent: str = Field(..., description="The classified intent type")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence score 0-1")
    entities: Dict[str, Any] = Field(
        default_factory=dict, description="Extracted entities from the message"
    )
    suggested_response: Optional[str] = Field(
        default=None, description="Suggested response based on intent"
    )


class SalaryAnalysis(BaseModel):
    """Analysis of salary/compensation for a position."""
    recommended_min: Optional[int] = Field(
        default=None, description="Recommended minimum salary"
    )
    recommended_max: Optional[int] = Field(
        default=None, description="Recommended maximum salary"
    )
    market_position: Literal["below_market", "at_market", "above_market"] = Field(
        ..., description="How this salary compares to market"
    )
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Explanation of the analysis")


class SkillExtraction(BaseModel):
    """Extracted skills from job description or candidate profile."""
    technical_skills: List[str] = Field(
        default_factory=list, description="Technical/hard skills"
    )
    soft_skills: List[str] = Field(
        default_factory=list, description="Soft/behavioral skills"
    )
    languages: List[str] = Field(
        default_factory=list, description="Programming or spoken languages"
    )
    certifications: List[str] = Field(
        default_factory=list, description="Certifications or credentials"
    )
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence score 0-1")


class JobDescriptionExtraction(BaseModel):
    """Structured extraction from a job description."""
    job_title: Optional[str] = Field(default=None, description="The job title")
    department: Optional[str] = Field(default=None, description="Department or team")
    seniority: Optional[str] = Field(default=None, description="Seniority level")
    location: Optional[str] = Field(default=None, description="Work location")
    work_model: Optional[Literal["remote", "hybrid", "onsite"]] = Field(
        default=None, description="Remote/hybrid/onsite"
    )
    employment_type: Optional[str] = Field(default=None, description="Full-time/part-time/contract")
    salary_min: Optional[float] = Field(default=None, description="Minimum salary")
    salary_max: Optional[float] = Field(default=None, description="Maximum salary")
    currency: Optional[str] = Field(default="BRL", description="Salary currency")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    benefits: List[str] = Field(default_factory=list, description="Benefits offered")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Overall extraction confidence")


class CandidateEvaluation(BaseModel):
    """Evaluation of a candidate for a position."""
    overall_score: float = Field(ge=0, le=100, description="Overall match score 0-100")
    technical_fit: float = Field(ge=0, le=100, description="Technical skills match 0-100")
    experience_fit: float = Field(ge=0, le=100, description="Experience level match 0-100")
    culture_fit: float = Field(ge=0, le=100, description="Culture fit estimate 0-100")
    strengths: List[str] = Field(default_factory=list, description="Key strengths")
    gaps: List[str] = Field(default_factory=list, description="Identified gaps")
    recommendation: Literal["strong_yes", "yes", "maybe", "no", "strong_no"] = Field(
        ..., description="Hiring recommendation"
    )
    reasoning: str = Field(..., description="Explanation of evaluation")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence score 0-1")


class ConversationAnalysis(BaseModel):
    """Analysis of a conversation turn for context management."""
    topic_shift: bool = Field(default=False, description="Whether topic changed")
    current_topic: Optional[str] = Field(default=None, description="Current conversation topic")
    user_sentiment: Optional[Literal["positive", "neutral", "negative", "frustrated"]] = Field(
        default=None, description="Detected user sentiment"
    )
    requires_followup: bool = Field(default=False, description="Whether followup is needed")
    key_entities: Dict[str, Any] = Field(
        default_factory=dict, description="Important entities mentioned"
    )
    suggested_next_step: Optional[str] = Field(
        default=None, description="Recommended next action"
    )


class ValidationResult(BaseModel):
    """Result of validating data or input."""
    is_valid: bool = Field(..., description="Whether the input is valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    corrected_value: Optional[Any] = Field(default=None, description="Auto-corrected value if applicable")


class TextGeneration(BaseModel):
    """Generic structured text generation response."""
    text: str = Field(..., description="The generated text")
    tone: Optional[str] = Field(default=None, description="Tone of the generated text")
    language: Optional[str] = Field(default="pt-BR", description="Language of the text")
    word_count: Optional[int] = Field(default=None, description="Word count")
    key_points: List[str] = Field(default_factory=list, description="Key points covered")


class WizardOrchestrationResult(BaseModel):
    """
    Structured output for the job wizard orchestrator.
    
    Maps directly to WizardOrchestratorResponse for use with LLM structured outputs.
    """
    action: Literal["respond", "advance_stage", "update_fields", "request_clarification", "provide_suggestion", "validate_data"] = Field(
        ..., description="Action to take based on user input"
    )
    response: str = Field(
        ..., description="Response message to show the user in Portuguese"
    )
    updated_fields: Optional[Dict[str, Any]] = Field(
        default=None, description="Fields to update with their new values"
    )
    target_stage: Optional[str] = Field(
        default=None, description="Target stage to navigate to"
    )
    confidence: float = Field(
        default=0.9, ge=0, le=1, description="Confidence in this decision"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Internal reasoning for this decision"
    )
    suggestions: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Suggestions for the user"
    )
    validation_errors: Optional[List[str]] = Field(
        default=None, description="Validation errors if action is validate_data"
    )
