"""
Pydantic schemas for WSI-based Screening Questions endpoints.
"""
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel

_logger = logging.getLogger(__name__)


class BigFiveProfile(BaseModel):
    openness: int = Field(default=50, ge=0, le=100, description="Abertura a novas experiências")
    conscientiousness: int = Field(default=50, ge=0, le=100, description="Organização e responsabilidade")
    extraversion: int = Field(default=50, ge=0, le=100, description="Sociabilidade e energia")
    agreeableness: int = Field(default=50, ge=0, le=100, description="Cooperação e empatia")
    stability: int = Field(default=50, ge=0, le=100, description="Estabilidade emocional")


class ScreeningQuestionRequest(WeDoBaseModel):
    title: str = Field(..., description="Job title")
    department: str | None = Field(None, description="Department/area")
    seniority: Literal["junior", "pleno", "senior", "lead", "executive"] | None = Field(
        default=None, description="Seniority level. Se None, será resolvido automaticamente via multi-signal."
    )
    big_five_profile: BigFiveProfile | None = Field(None, description="Big Five personality profile")
    skills: list[str] = Field(default=[], description="Required technical skills")
    behavioral_competencies: list[str] = Field(
        default=[],
        description="Soft skills / behavioral competencies (alinhado com canonical /api/v1/wsi/generate-questions). "
                    "Audit 2026-05-20 F6.O3+O6: antes era hardcoded [] no handler — gerava perguntas behavioral usando skills técnicas como fallback. "
                    "Frontend canonical já manda esse field via /api/v1/wsi/generate-questions; este endpoint legacy agora aceita também (backward-compat: default [] preserva comportamento antigo)."
    )
    job_description: str | None = Field(None, description="Full job description text")
    question_count: int = Field(default=8, ge=4, le=25, description="Number of questions to generate")


class ScreeningQuestion(BaseModel):
    id: str = Field(..., description="Unique question identifier")
    text: str = Field(..., description="The question text in Portuguese")
    category: Literal["behavioral", "technical", "cultural"] = Field(..., description="Question category")
    trait: str | None = Field(None, description="Big Five trait if behavioral question")
    skill: str | None = Field(None, description="Technical skill if technical question")
    bloom_level: int = Field(default=3, ge=1, le=6, description="Bloom's Taxonomy level (1-6)")
    bloom_label: str = Field(default="Aplicar", description="Bloom level label")
    dreyfus_stage: int = Field(default=3, ge=1, le=5, description="Dreyfus model stage (1-5)")
    dreyfus_label: str = Field(default="Competente", description="Dreyfus stage label")
    framework: Literal["CBI", "Bloom", "Dreyfus", "BigFive"] = Field(
        default="CBI", description="Framework used to generate question"
    )
    weight: float = Field(default=1.0, ge=0, le=1, description="Question weight for scoring")
    expected_signals: list[str] = Field(default=[], description="Expected positive signals in answer")
    scoring_criteria: dict[str, Any] = Field(default={}, description="Scoring criteria by level")
    is_selected: bool = Field(default=True, description="Whether question is selected for use")
    order: int = Field(default=0, description="Display order")


class ScreeningQuestionResponse(BaseModel):
    questions: list[ScreeningQuestion] = Field(default=[], description="Generated screening questions")
    behavioral_questions: list[ScreeningQuestion] = Field(default=[], description="Behavioral questions grouped")
    technical_questions: list[ScreeningQuestion] = Field(default=[], description="Technical questions grouped")
    cultural_questions: list[ScreeningQuestion] = Field(default=[], description="Cultural questions grouped")
    total_count: int = Field(default=0, description="Total number of questions")
    metadata: dict[str, Any] = Field(default={}, description="Generation metadata")


class RegenerateQuestionsRequest(WeDoBaseModel):
    context: ScreeningQuestionRequest = Field(..., description="Original job context")
    category: Literal["behavioral", "technical", "cultural"] | None = Field(
        None, description="Category to regenerate, or all if None"
    )
    exclude_ids: list[str] = Field(default=[], description="Question IDs to exclude from regeneration")


class UnifiedScreeningQuestion(BaseModel):
    """Unified screening question with WSI block assignment."""
    id: str = Field(..., description="Unique question identifier")
    text: str = Field(..., description="The question text in Portuguese")
    category: str = Field(..., description="Question category: behavioral, technical, cultural, eligibility, company")
    block_id: int = Field(..., description="WSI block ID: 2 (company), 3 (technical), 4 (behavioral/situational)")
    source: Literal["company", "wsi_generated"] = Field(default="wsi_generated", description="Question source")
    trait: str | None = Field(None, description="Big Five trait if behavioral question")
    skill: str | None = Field(None, description="Technical skill if technical question")
    bloom_level: int = Field(default=3, ge=1, le=6, description="Bloom's Taxonomy level")
    bloom_label: str = Field(default="Aplicar", description="Bloom level label")
    dreyfus_stage: int = Field(default=3, ge=1, le=5, description="Dreyfus model stage")
    dreyfus_label: str = Field(default="Competente", description="Dreyfus stage label")
    framework: str = Field(default="CBI", description="Framework used")
    weight: float = Field(default=1.0, ge=0, le=1, description="Question weight")
    expected_signals: list[str] = Field(default=[], description="Expected positive signals")
    scoring_criteria: dict[str, Any] = Field(default={}, description="Scoring criteria")
    is_selected: bool = Field(default=True, description="Whether selected for use")
    is_eliminatory: bool = Field(default=False, description="Whether eliminatory")
    question_type: str = Field(default="open", description="Question format: open, yes_no, single_choice, multiple_choice, scale")
    options: list[str] | None = Field(None, description="Options for choice questions")
    expected_answer: str | None = Field(None, description="Expected answer for eliminatory questions")
    order: int = Field(default=0, description="Display order within block")


class WSIScreeningPipelineRequest(WeDoBaseModel):
    """Request for the unified WSI screening pipeline."""
    job_title: str = Field(..., description="Job title")
    department: str | None = Field(None, description="Department")
    seniority: Literal["junior", "pleno", "senior", "lead", "executive"] | None = Field(default=None, description="Seniority level. Se None, será resolvido automaticamente via multi-signal.")
    technical_skills: list[str] = Field(default=[], description="Required technical skills")
    behavioral_competencies: list[str] = Field(default=[], description="Behavioral competencies")
    responsibilities: list[str] = Field(default=[], description="Job responsibilities")
    big_five_profile: BigFiveProfile | None = Field(None, description="Big Five profile")
    job_description: str | None = Field(None, description="Full job description")
    question_count: int | None = Field(default=None, ge=7, le=25, description="Total target question count. Defaults to 7 for compact, 12 for full format (per WSI F5 spec).")
    format: Literal["compact", "full"] = Field(default="full", description="compact=fewer questions, full=complete assessment")
    include_company_questions: bool = Field(default=True, description="Include company default questions")
    company_question_categories: list[str] | None = Field(None, description="Filter company questions by category")
    is_affirmative: bool = Field(default=False, description="Whether this is an affirmative action job vacancy")
    affirmative_type: str | None = Field(None, description="Type of affirmative action: pcd, racial, gender, age, lgbtqia+")
    job_id: str | None = Field(None, description="ID da vaga — servidor resolve is_affirmative/critério da vaga server-side (fonte da verdade, não confia na flag do FE)")


class WSIBlockSummary(BaseModel):
    """Summary of questions in a WSI block."""
    block_id: int
    block_name: str
    question_count: int
    questions: list[UnifiedScreeningQuestion]


class WSIScreeningPipelineResponse(BaseModel):
    """Response from the unified WSI screening pipeline."""
    success: bool = True
    questions: list[UnifiedScreeningQuestion] = Field(default=[], description="All questions flat list")
    blocks: list[WSIBlockSummary] = Field(default=[], description="Questions grouped by WSI block")
    total_count: int = Field(default=0)
    block_distribution: dict[str, int] = Field(default={})
    metadata: dict[str, Any] = Field(default={})
    seniority_resolution: dict[str, Any] | None = Field(default=None, description="Metadata da resolução de senioridade multi-signal")
    quality_warnings: list[str] = Field(default=[])
